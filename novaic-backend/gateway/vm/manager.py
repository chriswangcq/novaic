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
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from gateway.config.agents import PortConfig, allocate_ports_for_agent
from .repository import VmProcessRepository
from .ssh import get_ssh_key_manager

logger = logging.getLogger(__name__)

# Singleton instance
_vm_manager: Optional["VmManager"] = None


def get_vm_manager() -> "VmManager":
    """Get the global VM manager instance."""
    global _vm_manager
    if _vm_manager is None:
        data_dir = os.environ.get("NOVAIC_DATA_DIR", "/tmp/novaic")
        _vm_manager = VmManager(data_dir)
    return _vm_manager


@dataclass
class VmConfig:
    """VM configuration for QEMU."""
    memory: str = "4096"
    cpus: int = 4
    image_path: Optional[str] = None
    agent_index: int = 0
    ports: PortConfig = field(default_factory=lambda: allocate_ports_for_agent(0))
    # VM internal ports (fixed, mapped via QEMU port forwarding)
    mcp_vm_port: int = 8080
    vnc_vm_port: int = 5900
    ws_vm_port: int = 6080


@dataclass
class VmStatus:
    """VM status information."""
    agent_id: str
    running: bool
    agent_healthy: bool
    mcp_healthy: bool
    websockify_running: bool
    ports: Dict[str, int]
    vnc_url: str
    mcp_url: str
    pid: Optional[int] = None
    started_at: Optional[str] = None
    error_message: Optional[str] = None


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
    
    async def start(
        self,
        agent_id: str,
        agent_index: int,
        memory: str = "4096",
        cpus: int = 4,
    ) -> Dict[str, Any]:
        """
        Start VM for an agent.
        
        Args:
            agent_id: Agent ID
            agent_index: Agent index (for port allocation)
            memory: Memory size (e.g., "4096")
            cpus: Number of CPUs
        
        Returns:
            Dict with VM status info.
        """
        logger.info(f"[VmManager] Starting VM for agent {agent_id} (index={agent_index})")
        
        # Check if already running
        process_info = await self.repo.get_process(agent_id)
        if process_info and process_info["status"] == "running":
            if self._is_pid_alive(process_info.get("pid")):
                logger.info(f"[VmManager] VM for agent {agent_id} already running")
                return {"status": "already_running", "pid": process_info["pid"]}
        
        # Build config
        ports = allocate_ports_for_agent(agent_index)
        config = VmConfig(
            memory=memory,
            cpus=cpus,
            agent_index=agent_index,
            ports=ports,
        )
        
        # Get image path - check multiple possible locations
        agent_dir = self.get_agent_dir(agent_id)
        
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
        
        # Check ports available
        for port_name in ["vnc", "websocket", "ssh", "vm"]:
            port = getattr(ports, port_name)
            if self._is_port_in_use(port):
                raise RuntimeError(f"Port {port} ({port_name}) is already in use")
        
        # Update status to starting
        await self.repo.upsert_process(
            agent_id=agent_id,
            status="starting",
            ports=ports.__dict__,
        )
        
        try:
            # Build QEMU command
            qemu_cmd = self._get_qemu_command()
            qemu_args = self._build_qemu_args(config, agent_dir)
            
            full_cmd = [qemu_cmd] + qemu_args
            logger.info(f"[VmManager] Starting QEMU: {' '.join(full_cmd[:10])}...")
            
            # Start QEMU process
            process = subprocess.Popen(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(agent_dir),
            )
            
            self._processes[agent_id] = process
            
            # Save to DB
            await self.repo.upsert_process(
                agent_id=agent_id,
                pid=process.pid,
                status="running",
                ports=ports.__dict__,
                qemu_cmd=" ".join(full_cmd),
            )
            
            # Wait for VM to boot
            logger.info(f"[VmManager] Waiting for VM to start (PID: {process.pid})...")
            await asyncio.sleep(5)
            
            # Wait for websockify
            await self._wait_for_service(ports.websocket, "websockify", timeout=60)
            
            # Wait for MCP
            await self._wait_for_service(ports.vm, "MCP", timeout=120)
            
            logger.info(f"[VmManager] VM for agent {agent_id} started successfully")
            
            return {
                "status": "running",
                "pid": process.pid,
                "ports": ports.__dict__,
            }
            
        except Exception as e:
            logger.error(f"[VmManager] Failed to start VM: {e}")
            await self.repo.update_status(agent_id, "error", error_message=str(e))
            raise
    
    async def stop(self, agent_id: str, graceful: bool = True, quick: bool = False) -> Dict[str, Any]:
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
        
        process_info = await self.repo.get_process(agent_id)
        if not process_info:
            return {"status": "not_found"}
        
        pid = process_info.get("pid")
        ports = process_info.get("ports", {})
        
        # Update status
        await self.repo.update_status(agent_id, "stopping")
        
        # Quick mode: shorter timeouts
        ssh_timeout = 3 if quick else 10
        wait_iterations = 3 if quick else 10
        
        # Step 1: Try graceful shutdown via SSH (skip in quick mode if graceful=False)
        if graceful and ports.get("ssh"):
            try:
                ssh_manager = get_ssh_key_manager()
                key_path = await ssh_manager.get_private_key_path()
                
                connect_timeout = "2" if quick else "5"
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
                await asyncio.sleep(1)
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
        
        await self.repo.update_status(agent_id, "stopped")
        
        logger.info(f"[VmManager] VM for agent {agent_id} stopped")
        return {"status": "stopped"}
    
    async def stop_all(self, graceful: bool = True, quick: bool = False) -> Dict[str, Any]:
        """Stop all running VMs in parallel.
        
        Args:
            graceful: Try graceful shutdown via SSH first
            quick: Use shorter timeouts (for app exit)
        
        Returns:
            Dict mapping agent_id to stop result.
        """
        running = await self.repo.get_running_processes()
        
        if not running:
            logger.info("[VmManager] No running VMs to stop")
            return {}
        
        logger.info(f"[VmManager] Stopping {len(running)} VMs in parallel (graceful={graceful}, quick={quick})")
        
        # Stop all VMs in parallel
        tasks = [
            self.stop(proc["agent_id"], graceful=graceful, quick=quick)
            for proc in running
        ]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
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
    
    async def get_status(self, agent_id: str) -> Optional[VmStatus]:
        """Get VM status for an agent."""
        process_info = await self.repo.get_process(agent_id)
        if not process_info:
            return None
        
        ports = process_info.get("ports", {})
        pid = process_info.get("pid")
        
        # Check if actually running
        running = self._is_pid_alive(pid) if pid else False
        
        # Check services
        websockify_running = self._is_port_in_use(ports.get("websocket", 0))
        mcp_healthy = self._is_port_in_use(ports.get("vm", 0))
        
        return VmStatus(
            agent_id=agent_id,
            running=running,
            agent_healthy=True,  # Gateway is always healthy
            mcp_healthy=mcp_healthy,
            websockify_running=websockify_running,
            ports=ports,
            vnc_url=f"ws://localhost:{ports.get('websocket', 0)}/websockify",
            mcp_url=f"http://127.0.0.1:{ports.get('vm', 0)}/mcp",
            pid=pid,
            started_at=process_info.get("started_at"),
            error_message=process_info.get("error_message"),
        )
    
    async def get_all_status(self) -> Dict[str, VmStatus]:
        """Get status for all VMs."""
        all_processes = await self.repo.get_all_processes()
        result = {}
        
        for proc in all_processes:
            agent_id = proc["agent_id"]
            status = await self.get_status(agent_id)
            if status:
                result[agent_id] = status
        
        return result
    
    async def is_running(self, agent_id: str) -> bool:
        """Check if VM is running."""
        status = await self.get_status(agent_id)
        return status.running if status else False
    
    async def get_running_agents(self) -> List[str]:
        """Get list of running agent IDs."""
        running = await self.repo.get_running_processes()
        return [
            p["agent_id"] for p in running
            if self._is_pid_alive(p.get("pid"))
        ]
    
    # ==================== Recovery ====================
    
    async def recover_processes(self):
        """
        Recover running VMs after Gateway restart.
        
        Checks DB for VMs marked as running and verifies they're still alive.
        """
        logger.info("[VmManager] Recovering VM processes...")
        
        running = await self.repo.get_running_processes()
        recovered = 0
        cleaned = 0
        
        for proc in running:
            agent_id = proc["agent_id"]
            pid = proc.get("pid")
            
            if pid and self._is_pid_alive(pid):
                logger.info(f"[VmManager] Recovered VM {agent_id} (PID: {pid})")
                recovered += 1
            else:
                logger.info(f"[VmManager] VM {agent_id} no longer running, cleaning up")
                await self.repo.update_status(agent_id, "stopped")
                cleaned += 1
        
        logger.info(f"[VmManager] Recovery complete: {recovered} running, {cleaned} cleaned")
    
    # ==================== Internal Helpers ====================
    
    def _get_qemu_command(self) -> str:
        """Get QEMU system binary path."""
        arch_suffix = "aarch64" if self.is_arm else "x86_64"
        binary_name = f"qemu-system-{arch_suffix}"
        
        paths = [
            f"/opt/homebrew/bin/{binary_name}",
            f"/usr/local/bin/{binary_name}",
            f"/usr/bin/{binary_name}",
        ]
        
        for path in paths:
            if Path(path).exists():
                return path
        
        return binary_name  # Hope it's in PATH
    
    def _build_qemu_args(self, config: VmConfig, agent_dir: Path) -> List[str]:
        """Build QEMU command arguments."""
        ports = config.ports
        
        port_forward = (
            f"hostfwd=tcp::{ports.vnc}-:{config.vnc_vm_port},"
            f"hostfwd=tcp::{ports.websocket}-:{config.ws_vm_port},"
            f"hostfwd=tcp::{ports.ssh}-:22,"
            f"hostfwd=tcp:127.0.0.1:{ports.vm}-:{config.mcp_vm_port}"
        )
        
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
        
        raise RuntimeError(f"{filename} not found in any of: {[str(p) for p in possible_paths]}")
    
    def _build_arm64_args(
        self,
        config: VmConfig,
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
        seed_iso = None
        for iso_path in [
            agent_dir / "cloud-init.iso",
            agent_dir / "vm" / "iso" / "cloud-init-seed.iso",
            self.data_dir / "vms" / agent_id / "cloud-init-seed.iso",
        ]:
            if iso_path.exists():
                seed_iso = iso_path
                break
        
        args = [
            "-name", f"novaic-vm-{config.agent_index}",
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
            "-chardev", f"socket,id=mcp,path=/tmp/novaic-mcp-{config.agent_index}.sock,server=on,wait=off",
            "-device", "virtserialport,chardev=mcp,name=mcp",
            "-device", "virtio-gpu-pci",
            "-device", "usb-ehci",
            "-device", "usb-kbd",
            "-device", "usb-mouse",
            "-display", "none",
        ]
        
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
        config: VmConfig,
        agent_dir: Path,
        port_forward: str,
    ) -> List[str]:
        """Build QEMU args for x86_64."""
        seed_iso = agent_dir / "cloud-init.iso"
        
        args = [
            "-name", f"novaic-vm-{config.agent_index}",
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
            "-chardev", f"socket,id=mcp,path=/tmp/novaic-mcp-{config.agent_index}.sock,server=on,wait=off",
            "-device", "virtserialport,chardev=mcp,name=mcp",
            "-display", "none",
        ])
        
        if seed_iso.exists():
            args.extend(["-cdrom", str(seed_iso)])
        
        return args
    
    async def _wait_for_service(
        self,
        port: int,
        name: str,
        timeout: int = 60,
        interval: float = 2.0,
    ):
        """Wait for a service to become available on a port."""
        logger.info(f"[VmManager] Waiting for {name} on port {port}...")
        
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            if self._is_port_in_use(port):
                elapsed = asyncio.get_event_loop().time() - start
                logger.info(f"[VmManager] {name} ready after {elapsed:.1f}s")
                return
            await asyncio.sleep(interval)
        
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
            import time
            wait_iterations = 2 if quick else 6
            for _ in range(wait_iterations):
                time.sleep(0.5)
                if not self._is_pid_alive(pid):
                    return
            
            # Force kill
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
