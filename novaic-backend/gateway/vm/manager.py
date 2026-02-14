"""
VM Manager - Manages QEMU virtual machine processes

Migrated from Tauri's manager.rs to Python for Gateway control.
State is persisted to database for crash recovery.
"""

import os
import platform
import subprocess
import signal
import socket
import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from common.config import ServiceConfig

from gateway.config.agents import PortConfig, allocate_ports_for_agent
from .repository import VmProcessRepository
from .ssh import get_ssh_key_manager

logger = logging.getLogger(__name__)

# Singleton instance
_vm_manager: Optional["VmManager"] = None


def get_vm_manager() -> "VmManager":
    """Get the global VM manager instance."""
    import tempfile
    
    global _vm_manager
    if _vm_manager is None:
        # 跨平台临时目录
        if "NOVAIC_DATA_DIR" in os.environ:
            data_dir = os.environ["NOVAIC_DATA_DIR"]
        else:
            data_dir = str(Path(tempfile.gettempdir()) / "novaic")
        _vm_manager = VmManager(data_dir)
    return _vm_manager


@dataclass
class VmRunConfig:
    """
    VM runtime configuration for QEMU (non-persistent).
    
    Note: This is distinct from gateway.config.agents_db.VmConfig which is
    the persistent VM configuration stored in the database.
    """
    agent_id: str
    ports: PortConfig  # Required, from agent config
    memory: str = "4096"
    cpus: int = 4
    image_path: Optional[str] = None


@dataclass
class VmStatus:
    """VM status information."""
    agent_id: str
    running: bool
    agent_healthy: bool
    mcp_healthy: bool
    ports: Dict[str, int]
    vnc_url: str
    mcp_url: str
    pid: Optional[int] = None
    started_at: Optional[str] = None
    error_message: Optional[str] = None
    vnc_socket: Optional[Path] = None  # QEMU native VNC socket path


class VmManager:
    """
    Manages QEMU virtual machine processes.
    
    Features:
    - Start/stop VMs for agents
    - Track VM processes (PID stored in DB)
    - Recover running VMs after Gateway restart
    - Multi-VM support (each agent has its own VM)
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.repo = VmProcessRepository()
        
        # In-memory process handles (for subprocess management)
        self._processes: Dict[str, subprocess.Popen] = {}
        
        # Architecture detection
        self.arch = platform.machine()
        self.is_arm = self.arch in ("arm64", "aarch64")
        self.is_macos = platform.system() == "Darwin"
        self.is_linux = platform.system() == "Linux"
        
        logger.info(f"[VmManager] Initialized (arch={self.arch}, macos={self.is_macos})")
    
    def get_agent_dir(self, agent_id: str) -> Path:
        """Get directory for agent's VM files."""
        return self.data_dir / "agents" / agent_id
    
    # ==================== VM Lifecycle ====================
    
    def start(
        self,
        agent_id: str,
        memory: str = "4096",
        cpus: int = 4,
        ports: Optional["PortConfig"] = None,
        image_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start VM for an agent.
        
        Args:
            agent_id: Agent ID
            memory: Memory size (e.g., "4096")
            cpus: Number of CPUs
            ports: Optional port configuration. If not provided, reads from agent config.
            image_path: Optional image path. If not provided, auto-detects.
        
        Returns:
            Dict with VM status info.
        
        端口配置可以直接传入，或从 agent 配置中获取
        """
        from gateway.config.agents_db import PortConfig
        
        # 如果没有传入端口配置，从数据库获取 agent 配置
        if ports is None:
            from gateway.config.agents_db import AgentConfigManagerDB
            agent_service = AgentConfigManagerDB()
            agent = agent_service.get_agent(agent_id)
            
            if not agent or not agent.vm or not agent.vm.ports:
                raise ValueError(f"Agent {agent_id} not found or has no port configuration")
            
            ports = agent.vm.ports
        
        logger.info(f"[VmManager] Starting VM for agent {agent_id} (ssh_port={ports.ssh})")
        
        # Check if already running
        process_info = self.repo.get_process(agent_id)
        if process_info and process_info["status"] == "running":
            if self._is_pid_alive(process_info.get("pid")):
                logger.info(f"[VmManager] VM for agent {agent_id} already running")
                return {"status": "already_running", "pid": process_info["pid"]}
        
        # Build config - 使用传入的或持久化的端口配置
        config = VmRunConfig(
            agent_id=agent_id,
            ports=ports,
            memory=memory,
            cpus=cpus,
        )
        
        # Always get agent_dir (needed for QEMU args like UEFI files)
        agent_dir = self.get_agent_dir(agent_id)
        
        # Get image path - use provided path or auto-detect
        if image_path and Path(image_path).exists():
            disk_path = Path(image_path)
        else:
            # Auto-detect image path - check multiple possible locations
            # Possible disk paths (in order of preference)
            possible_paths = [
                agent_dir / "disk.qcow2",                         # New setup path
                agent_dir / "vm" / "disk.qcow2",                  # Alternative path
                agent_dir / "vm" / "disk" / "novaic-vm.qcow2",    # Old Tauri path in agents
                self.data_dir / "vms" / agent_id / "disk.qcow2",  # Old Tauri path in vms
            ]
            
            disk_path = None
            for path in possible_paths:
                if path.exists():
                    disk_path = path
                    break
            
            if disk_path is None:
                raise RuntimeError(f"VM disk not found in any of: {[str(p) for p in possible_paths]}. Run setup first.")
        
        logger.info(f"[VmManager] Using disk: {disk_path}")
        config.image_path = str(disk_path)
        
        # Check SSH port available
        if self._is_port_in_use(config.ports.ssh):
            raise RuntimeError(f"SSH port {config.ports.ssh} already in use")
        
        # Update status to starting
        self.repo.upsert_process(
            agent_id=agent_id,
            status="starting",
            ports=config.ports.__dict__,
        )
        
        try:
            # Build QEMU command
            qemu_cmd = self._get_qemu_command()
            qemu_args = self._build_qemu_args(config, agent_dir)
            
            full_cmd = [qemu_cmd] + qemu_args
            logger.info(f"[VmManager] Starting QEMU: {' '.join(full_cmd[:10])}...")
            
            # Prepare log directory and files
            # Use data_dir/logs for QEMU logs (consistent with other services)
            log_dir = self.data_dir / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            stdout_log = log_dir / f"qemu-{agent_id}-stdout.log"
            stderr_log = log_dir / f"qemu-{agent_id}-stderr.log"
            
            # Start QEMU process with log files instead of PIPE
            # Using log files prevents buffer overflow and allows debugging
            process = subprocess.Popen(
                full_cmd,
                stdout=open(stdout_log, 'w'),
                stderr=open(stderr_log, 'w'),
                cwd=str(agent_dir),
            )
            
            self._processes[agent_id] = process
            
            # Save to DB
            self.repo.upsert_process(
                agent_id=agent_id,
                pid=process.pid,
                status="running",
                ports=config.ports.__dict__,
                qemu_cmd=" ".join(full_cmd),
            )
            
            # Wait for VM to boot
            logger.info(f"[VmManager] Waiting for VM to start (PID: {process.pid})...")
            time.sleep(5)
            
            # Check if process is still running
            if process.poll() is not None:
                exit_code = process.returncode
                error_msg = f"QEMU process exited immediately with code {exit_code}. Check logs: {stdout_log}, {stderr_log}"
                logger.error(f"[VmManager] {error_msg}")
                # Try to read error from stderr log
                try:
                    if stderr_log.exists():
                        with open(stderr_log, 'r') as f:
                            stderr_content = f.read()
                            if stderr_content:
                                error_msg += f"\nStderr: {stderr_content[-500:]}"  # Last 500 chars
                except Exception:
                    pass
                self.repo.update_status(agent_id, "error", error_message=error_msg)
                raise RuntimeError(error_msg)
            
            logger.info(f"[VmManager] VM for agent {agent_id} started successfully")
            
            # Register VM with vmcontrol service (async call in sync context)
            # Use asyncio.run to execute the async registration
            try:
                import asyncio
                asyncio.run(self._register_vm_with_vmcontrol(agent_id, agent.name, config.ports))
            except Exception as e:
                logger.warning(f"[VmManager] Failed to register VM with vmcontrol (non-fatal): {e}")
            
            return {
                "status": "running",
                "pid": process.pid,
                "ports": config.ports.__dict__,
            }
            
        except Exception as e:
            logger.error(f"[VmManager] Failed to start VM: {e}")
            self.repo.update_status(agent_id, "error", error_message=str(e))
            raise
    
    def stop(self, agent_id: str, graceful: bool = True, quick: bool = False) -> Dict[str, Any]:
        """
        Stop VM for an agent.
        
        Args:
            agent_id: Agent ID
            graceful: Try graceful shutdown via SSH first
            quick: Use shorter timeouts (for app exit)
        
        Returns:
            Dict with stop status.
        """
        logger.info(f"[VmManager] Stopping VM for agent {agent_id} (graceful={graceful}, quick={quick})")
        
        process_info = self.repo.get_process(agent_id)
        if not process_info:
            return {"status": "not_found"}
        
        pid = process_info.get("pid")
        ports = process_info.get("ports", {})
        
        # Update status
        self.repo.update_status(agent_id, "stopping")
        
        # Quick mode: shorter timeouts
        ssh_timeout = ServiceConfig.SSH_QUICK_TIMEOUT if quick else ServiceConfig.SSH_NORMAL_TIMEOUT
        wait_iterations = 3 if quick else 10
        
        # Step 1: Try graceful shutdown via SSH (skip in quick mode if graceful=False)
        if graceful and ports.get("ssh"):
            try:
                ssh_manager = get_ssh_key_manager()
                key_path = ssh_manager.get_private_key_path()
                
                connect_timeout = "2" if quick else "5"
                # TODO: Replace with QMP system_powerdown command
                # Will be implemented in Phase 1 via vmcontrol
                result = subprocess.run(
                    [
                        "ssh",
                        "-i", str(key_path),
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        "-o", f"ConnectTimeout={connect_timeout}",
                        "-p", str(ports["ssh"]),
                        "ubuntu@localhost",
                        "sudo", "poweroff",
                    ],
                    capture_output=True,
                    timeout=ssh_timeout,
                )
                logger.info(f"[VmManager] SSH poweroff sent to agent {agent_id}")
            except Exception as e:
                logger.warning(f"[VmManager] SSH shutdown failed: {e}")
        
        # Step 2: Wait for process to exit
        shutdown_ok = False
        if pid:
            for i in range(wait_iterations):
                time.sleep(1)
                if not self._is_pid_alive(pid):
                    logger.info(f"[VmManager] VM {agent_id} shutdown gracefully")
                    shutdown_ok = True
                    break
        
        # Step 3: Force kill if needed
        if not shutdown_ok and pid:
            logger.info(f"[VmManager] Force killing VM {agent_id} (PID: {pid})")
            self._kill_process(pid, quick=quick)
        
        # Cleanup
        if agent_id in self._processes:
            del self._processes[agent_id]
        
        self.repo.update_status(agent_id, "stopped")
        
        logger.info(f"[VmManager] VM for agent {agent_id} stopped")
        return {"status": "stopped"}
    
    def stop_all(self, graceful: bool = True, quick: bool = False) -> Dict[str, Any]:
        """Stop all running VMs in parallel.
        
        Args:
            graceful: Try graceful shutdown via SSH first
            quick: Use shorter timeouts (for app exit)
        
        Returns:
            Dict mapping agent_id to stop result.
        """
        running = self.repo.get_running_processes()
        
        if not running:
            logger.info("[VmManager] No running VMs to stop")
            return {}
        
        logger.info(f"[VmManager] Stopping {len(running)} VMs in parallel (graceful={graceful}, quick={quick})")
        
        # Stop all VMs in parallel
        tasks = [
            self.stop(proc["agent_id"], graceful=graceful, quick=quick)
            for proc in running
        ]
        results_list = asyncio.gather(*tasks, return_exceptions=True)
        
        # Build results dict
        results = {}
        for proc, result in zip(running, results_list):
            agent_id = proc["agent_id"]
            if isinstance(result, Exception):
                logger.error(f"[VmManager] Error stopping VM {agent_id}: {result}")
                results[agent_id] = {"status": "error", "error": str(result)}
            else:
                results[agent_id] = result
        
        logger.info(f"[VmManager] All VMs stopped: {list(results.keys())}")
        return results
    
    # ==================== Status ====================
    
    def get_status(self, agent_id: str) -> Optional[VmStatus]:
        """Get VM status for an agent."""
        process_info = self.repo.get_process(agent_id)
        if not process_info:
            return None
        
        ports = process_info.get("ports", {})
        pid = process_info.get("pid")
        
        # Check if actually running
        running = self._is_pid_alive(pid) if pid else False
        
        # Get VNC socket path for vmcontrol WebSocket URL
        agent_dir = self.get_agent_dir(agent_id)
        vnc_socket_path = Path("/tmp/novaic") / f"novaic-vnc-{agent_id}.sock"
        
        return VmStatus(
            agent_id=agent_id,
            running=running,
            agent_healthy=True,  # Gateway is always healthy
            mcp_healthy=False,  # MCP no longer used
            ports=ports,
            vnc_url=f"ws://localhost:19996/api/vms/{agent_id}/vnc",  # vmcontrol WebSocket URL
            mcp_url="",  # MCP no longer used
            pid=pid,
            started_at=process_info.get("started_at"),
            error_message=process_info.get("error_message"),
            vnc_socket=vnc_socket_path if vnc_socket_path.exists() else None,
        )
    
    def get_all_status(self) -> Dict[str, VmStatus]:
        """Get status for all VMs."""
        all_processes = self.repo.get_all_processes()
        result = {}
        
        for proc in all_processes:
            agent_id = proc["agent_id"]
            status = self.get_status(agent_id)
            if status:
                result[agent_id] = status
        
        return result
    
    def is_running(self, agent_id: str) -> bool:
        """Check if VM is running."""
        status = self.get_status(agent_id)
        return status.running if status else False
    
    def get_running_agents(self) -> List[str]:
        """Get list of running agent IDs."""
        running = self.repo.get_running_processes()
        return [
            p["agent_id"] for p in running
            if self._is_pid_alive(p.get("pid"))
        ]
    
    # ==================== Recovery ====================
    
    def recover_processes(self):
        """
        Recover running VMs after Gateway restart.
        
        Checks DB for VMs marked as running and verifies they're still alive.
        Also re-registers all running VMs with vmcontrol service.
        """
        logger.info("[VmManager] Recovering VM processes...")
        
        running = self.repo.get_running_processes()
        recovered = 0
        cleaned = 0
        
        # Get agent service for name lookup
        from gateway.config.agents_db import AgentConfigManagerDB
        agent_service = AgentConfigManagerDB()
        
        # List to store running VMs for vmcontrol registration
        running_vms = []
        
        for proc in running:
            agent_id = proc["agent_id"]
            pid = proc.get("pid")
            
            if pid and self._is_pid_alive(pid):
                logger.info(f"[VmManager] Recovered VM {agent_id} (PID: {pid})")
                recovered += 1
                
                # Collect for vmcontrol registration
                agent = agent_service.get_agent(agent_id)
                if agent:
                    ports = proc.get("ports", {})
                    running_vms.append({
                        "agent_id": agent_id,
                        "agent_name": agent.name,
                        "ports": ports
                    })
            else:
                logger.info(f"[VmManager] VM {agent_id} no longer running, cleaning up")
                self.repo.update_status(agent_id, "stopped")
                cleaned += 1
        
        logger.info(f"[VmManager] Recovery complete: {recovered} running, {cleaned} cleaned")
        
        # Re-register all running VMs with vmcontrol
        if running_vms:
            logger.info(f"[VmManager] Re-registering {len(running_vms)} VMs with vmcontrol...")
            try:
                import asyncio
                asyncio.run(self._batch_register_vms(running_vms))
            except Exception as e:
                logger.warning(f"[VmManager] Failed to batch register VMs: {e}")
    
    async def _batch_register_vms(self, vms: List[Dict[str, Any]]):
        """
        Batch register multiple VMs with vmcontrol service.
        
        Args:
            vms: List of dicts with agent_id, agent_name, ports
        """
        from gateway.clients.vmcontrol import get_vmcontrol_client
        
        client = get_vmcontrol_client()
        
        # Check if vmcontrol is available
        if not await client.health_check():
            logger.warning(f"[VmManager] vmcontrol not available, skipping batch registration")
            return
        
        # Register each VM
        registered = 0
        for vm in vms:
            agent_id = vm["agent_id"]
            agent_name = vm["agent_name"]
            
            try:
                qmp_socket = f"/tmp/novaic/novaic-qmp-{agent_id}.sock"
                
                await client.register_vm(
                    vm_id=agent_id,
                    name=agent_name,
                    qmp_socket=qmp_socket
                )
                
                logger.info(f"[VmManager] Re-registered VM {agent_id} with vmcontrol")
                registered += 1
                
            except Exception as e:
                logger.warning(f"[VmManager] Failed to register VM {agent_id}: {e}")
        
        logger.info(f"[VmManager] Batch registration complete: {registered}/{len(vms)} VMs registered")
    
    # ==================== Internal Helpers ====================
    
    def _get_qemu_command(self) -> str:
        """Get QEMU system binary path."""
        arch_suffix = "aarch64" if self.is_arm else "x86_64"
        binary_name = f"qemu-system-{arch_suffix}"
        
        # 1. Check bundled QEMU in resource directory (for packaged app)
        bundled_path = self._get_bundled_qemu_path(binary_name)
        if bundled_path:
            logger.info(f"[VmManager] Using bundled QEMU: {bundled_path}")
            return bundled_path
        
        # 2. Fallback to system paths
        paths = [
            f"/opt/homebrew/bin/{binary_name}",
            f"/usr/local/bin/{binary_name}",
            f"/usr/bin/{binary_name}",
        ]
        
        for path in paths:
            if Path(path).exists():
                return path
        
        return binary_name  # Hope it's in PATH
    
    def _get_bundled_qemu_path(self, binary_name: str) -> Optional[str]:
        """Get bundled QEMU path from resource directory."""
        resource_dir = os.environ.get("NOVAIC_RESOURCE_DIR", "")
        logger.info(f"[VmManager] _get_bundled_qemu_path: NOVAIC_RESOURCE_DIR='{resource_dir}'")
        if not resource_dir:
            logger.info(f"[VmManager] _get_bundled_qemu_path: resource_dir is empty, returning None")
            return None
        
        bundled_path = Path(resource_dir) / "qemu" / binary_name
        logger.info(f"[VmManager] _get_bundled_qemu_path: checking {bundled_path}, exists={bundled_path.exists()}")
        if bundled_path.exists():
            return str(bundled_path)
        
        return None
    
    def _get_bundled_qemu_share_dir(self) -> Optional[str]:
        """Get bundled QEMU share directory path (for ROM files, firmware, etc.)."""
        resource_dir = os.environ.get("NOVAIC_RESOURCE_DIR", "")
        if not resource_dir:
            return None
        
        share_path = Path(resource_dir) / "qemu" / "share"
        if share_path.exists() and share_path.is_dir():
            logger.info(f"[VmManager] Using bundled QEMU share dir: {share_path}")
            return str(share_path)
        
        return None
    
    def _build_qemu_args(self, config: VmRunConfig, agent_dir: Path) -> List[str]:
        """Build QEMU command arguments."""
        ports = config.ports
        
        # Port forwarding: SSH + VMUSE HTTP server
        # VM:22 -> Host:{ports.ssh}, VM:8080 -> Host:{ports.vmuse}
        port_forward = f"hostfwd=tcp::{ports.ssh}-:22,hostfwd=tcp::{ports.vmuse}-:8080"
        
        if self.is_arm:
            return self._build_arm64_args(config, agent_dir, port_forward)
        else:
            return self._build_x86_args(config, agent_dir, port_forward)
    
    def _find_firmware_file(self, agent_id: str, filename: str) -> Path:
        """Find firmware file in multiple possible locations."""
        # Possible locations for firmware files
        possible_paths = [
            self.data_dir / "agents" / agent_id / filename,           # New path
            self.data_dir / "vms" / agent_id / filename,              # Old Tauri path
            self.data_dir / "shared" / "firmware" / filename,         # Shared firmware
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Check bundled QEMU share directory for base firmware (edk2-aarch64-code.fd)
        # This is used as a fallback source for QEMU_EFI.fd
        if filename == "QEMU_EFI.fd":
            share_dir = self._get_bundled_qemu_share_dir()
            if share_dir:
                bundled_edk2 = Path(share_dir) / "edk2-aarch64-code.fd"
                if bundled_edk2.exists():
                    logger.info(f"[VmManager] Using bundled firmware: {bundled_edk2}")
                    return bundled_edk2
        
        raise RuntimeError(f"{filename} not found in any of: {[str(p) for p in possible_paths]}")
    
    def _build_arm64_args(
        self,
        config: VmRunConfig,
        agent_dir: Path,
        port_forward: str,
    ) -> List[str]:
        """Build QEMU args for ARM64."""
        # Find firmware files from multiple locations
        agent_id = agent_dir.name
        firmware_path = self._find_firmware_file(agent_id, "QEMU_EFI.fd")
        vars_path = self._find_firmware_file(agent_id, "QEMU_VARS.fd")
        
        logger.info(f"[VmManager] Using firmware: {firmware_path}")
        logger.info(f"[VmManager] Using vars: {vars_path}")
        
        # Check for cloud-init ISO in multiple locations
        # First try device directory (v38 unified model) - derive from image_path
        seed_iso = None
        if config.image_path:
            device_dir = Path(config.image_path).parent
            device_iso = device_dir / "cloud-init.iso"
            if device_iso.exists():
                seed_iso = device_iso
        
        # Fallback to legacy locations
        if not seed_iso:
            for iso_path in [
                agent_dir / "cloud-init.iso",
                agent_dir / "vm" / "iso" / "cloud-init-seed.iso",
                self.data_dir / "vms" / agent_id / "cloud-init-seed.iso",
            ]:
                if iso_path.exists():
                    seed_iso = iso_path
                    break
        
        # Socket 路径 - 使用固定的 /tmp/novaic 避免路径过长
        socket_dir = Path("/tmp/novaic")
        socket_dir.mkdir(parents=True, exist_ok=True)
        socket_path = socket_dir / f"novaic-mcp-{agent_id}.sock"
        qmp_socket_path = socket_dir / f"novaic-qmp-{agent_id}.sock"
        ga_socket_path = socket_dir / f"novaic-ga-{agent_id}.sock"
        vnc_socket_path = socket_dir / f"novaic-vnc-{agent_id}.sock"
        
        args = [
            "-name", f"novaic-vm-{agent_id}",
            "-M", "virt,highmem=on",
            "-cpu", "host",
            "-accel", "hvf",
            "-m", config.memory,
            "-smp", str(config.cpus),
            "-drive", f"if=pflash,format=raw,file={firmware_path},readonly=on",
            "-drive", f"if=pflash,format=raw,file={vars_path}",
            "-drive", f"if=none,id=hd0,format=qcow2,file={config.image_path}",
            "-device", "virtio-blk-pci,drive=hd0,bootindex=1",
            "-device", "virtio-net-pci,netdev=net0",
            "-netdev", f"user,id=net0,{port_forward}",
            "-device", "virtio-serial-pci",
            "-chardev", f"socket,id=mcp,path={socket_path},server=on,wait=off",
            "-device", "virtserialport,chardev=mcp,name=mcp",
            # QEMU Guest Agent channel
            "-chardev", f"socket,path={ga_socket_path},server=on,wait=off,id=qga0",
            "-device", "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
            # QMP control socket for external VM management
            "-qmp", f"unix:{qmp_socket_path},server,nowait",
            "-device", "virtio-gpu-pci",
            "-device", "usb-ehci",
            "-device", "usb-kbd",
            "-device", "usb-tablet",  # 使用绝对坐标，便于 QMP input-send-event 和 VNC
            # QEMU native VNC via Unix socket
            "-vnc", f"unix:{vnc_socket_path}",
            "-display", "none",
        ]
        
        # Add QEMU data directory for bundled ROM files
        qemu_share_dir = self._get_bundled_qemu_share_dir()
        if qemu_share_dir:
            args.extend(["-L", qemu_share_dir])
        
        if seed_iso:
            logger.info(f"[VmManager] Using cloud-init ISO: {seed_iso}")
            args.extend([
                "-device", "virtio-scsi-pci,id=scsi0",
                "-drive", f"if=none,id=cd0,format=raw,file={seed_iso},readonly=on",
                "-device", "scsi-cd,drive=cd0,bus=scsi0.0",
            ])
        
        return args
    
    def _build_x86_args(
        self,
        config: VmRunConfig,
        agent_dir: Path,
        port_forward: str,
    ) -> List[str]:
        """Build QEMU args for x86_64."""
        agent_id = agent_dir.name
        
        # Check for cloud-init ISO - try device directory first (v38), then legacy
        seed_iso = None
        if config.image_path:
            device_dir = Path(config.image_path).parent
            device_iso = device_dir / "cloud-init.iso"
            if device_iso.exists():
                seed_iso = device_iso
        if not seed_iso:
            legacy_iso = agent_dir / "cloud-init.iso"
            if legacy_iso.exists():
                seed_iso = legacy_iso
        
        # Socket 路径 - 使用固定的 /tmp/novaic 避免路径过长
        socket_dir = Path("/tmp/novaic")
        socket_dir.mkdir(parents=True, exist_ok=True)
        socket_path = socket_dir / f"novaic-mcp-{agent_id}.sock"
        qmp_socket_path = socket_dir / f"novaic-qmp-{agent_id}.sock"
        ga_socket_path = socket_dir / f"novaic-ga-{agent_id}.sock"
        vnc_socket_path = socket_dir / f"novaic-vnc-{agent_id}.sock"
        
        args = [
            "-name", f"novaic-vm-{agent_id}",
        ]
        
        # Acceleration
        if self.is_macos:
            args.extend(["-accel", "hvf"])
        elif self.is_linux:
            args.extend(["-enable-kvm"])
        
        args.extend([
            "-cpu", "host",
            "-m", config.memory,
            "-smp", str(config.cpus),
            "-hda", config.image_path,
            "-boot", "c",
            "-net", "nic",
            "-net", f"user,{port_forward}",
            "-device", "virtio-serial-pci",
            "-chardev", f"socket,id=mcp,path={socket_path},server=on,wait=off",
            "-device", "virtserialport,chardev=mcp,name=mcp",
            # QEMU Guest Agent channel
            "-chardev", f"socket,path={ga_socket_path},server=on,wait=off,id=qga0",
            "-device", "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
            # QMP control socket for external VM management
            "-qmp", f"unix:{qmp_socket_path},server,nowait",
            # QEMU native VNC via Unix socket
            "-vnc", f"unix:{vnc_socket_path}",
            "-display", "none",
        ])
        
        # Add QEMU data directory for bundled ROM files
        qemu_share_dir = self._get_bundled_qemu_share_dir()
        if qemu_share_dir:
            args.extend(["-L", qemu_share_dir])
        
        if seed_iso and seed_iso.exists():
            logger.info(f"[VmManager] Using cloud-init ISO: {seed_iso}")
            args.extend(["-cdrom", str(seed_iso)])
        
        return args
    
    def _wait_for_service(
        self,
        port: int,
        name: str,
        timeout: int = 60,
        interval: float = 2.0,
    ):
        """Wait for a service to become available on a port. Uses time.time() so it works in sync threads (e.g. AnyIO worker)."""
        logger.info(f"[VmManager] Waiting for {name} on port {port}...")
        
        start = time.time()
        while time.time() - start < timeout:
            if self._is_port_in_use(port):
                elapsed = time.time() - start
                logger.info(f"[VmManager] {name} ready after {elapsed:.1f}s")
                return
            time.sleep(interval)
        
        logger.warning(f"[VmManager] {name} not ready after {timeout}s (continuing anyway)")
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        if not port:
            return False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("127.0.0.1", port))
                return result == 0
        except Exception:
            return False
    
    async def _register_vm_with_vmcontrol(self, agent_id: str, agent_name: str, ports: PortConfig):
        """
        Register VM with vmcontrol service
        
        Args:
            agent_id: Agent ID (VM ID)
            agent_name: Agent name
            ports: Port configuration for the VM
        """
        try:
            from gateway.clients.vmcontrol import get_vmcontrol_client
            
            client = get_vmcontrol_client()
            
            # Check if vmcontrol is available
            if not await client.health_check():
                logger.warning(f"[VmManager] vmcontrol not available, skipping VM registration")
                return
            
            # Build QMP socket path
            qmp_socket = f"/tmp/novaic/novaic-qmp-{agent_id}.sock"
            
            # Register VM
            result = await client.register_vm(
                vm_id=agent_id,
                name=agent_name,
                qmp_socket=qmp_socket
            )
            
            logger.info(f"[VmManager] VM {agent_id} registered with vmcontrol: {result}")
            
        except Exception as e:
            logger.warning(f"[VmManager] Failed to register VM with vmcontrol: {e}")
            # Don't fail VM start if registration fails
    
    def _is_pid_alive(self, pid: Optional[int]) -> bool:
        """Check if a process is still running."""
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def _kill_process(self, pid: int, quick: bool = False):
        """Kill a process by PID.
        
        Args:
            pid: Process ID
            quick: Use shorter wait times (for app exit)
        """
        try:
            # Try SIGTERM first
            os.kill(pid, signal.SIGTERM)
            
            # Wait a bit (shorter in quick mode)
            wait_iterations = 2 if quick else 6
            for _ in range(wait_iterations):
                time.sleep(0.5)
                if not self._is_pid_alive(pid):
                    return
            
            # Force kill
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
