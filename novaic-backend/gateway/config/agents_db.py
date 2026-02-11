"""
AIC Agent Configuration Manager - Database Version

Manages multiple AIC agents using SQLite storage.
All operations are synchronous.
"""

import logging
import os
import json
import uuid
import shutil
import platform
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from common.utils.time import utc_now_iso

logger = logging.getLogger(__name__)

from gateway.db.access import get_db
from common.db.database import Database
from gateway.db.repositories.agent import AgentRepository


# Port allocation constants
GATEWAY_PORT = 19999
BASE_PORT = 20000
BASE_VMUSE_PORT = 18000
PORTS_PER_AGENT = 2  # SSH + VMUSE ports
MAX_AGENTS = 100

SERVICE_OFFSETS = {
    "ssh": 0,
    "vmuse": 0,
}


class PortConfig(BaseModel):
    """
    Port configuration for an agent - SSH and VMUSE HTTP.
    
    Ports must be explicitly assigned during agent creation:
    - Agent 0: ssh=20000, vmuse=18000
    - Agent 1: ssh=20001, vmuse=18001
    - Agent N: ssh=20000+N, vmuse=18000+N
    """
    ssh: int = 0    # SSH port for VM access (dynamically assigned, 0 means not assigned)
    vmuse: int = 0  # VMUSE HTTP API port (dynamically assigned, 0 means not assigned)


class AndroidConfig(BaseModel):
    """Android emulator configuration for an agent."""
    device_serial: str = ""      # e.g., emulator-5554
    managed: bool = False        # Whether managed by novaic (create/destroy AVD)
    avd_name: Optional[str] = None  # AVD name for managed mode


class VmConfig(BaseModel):
    """VM configuration for an agent."""
    backend: str = "qemu"
    image_path: str = ""
    os_type: str = "ubuntu"
    os_version: str = "24.04"
    memory: str = "4096"
    cpus: int = 4
    ports: PortConfig = Field(default_factory=PortConfig)
    android: Optional[AndroidConfig] = None  # Android emulator config (optional)


class AICAgent(BaseModel):
    """AIC Agent configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: str = Field(default_factory=lambda: utc_now_iso())
    vm: VmConfig = Field(default_factory=VmConfig)
    setup_complete: bool = False  # VM setup complete (disk, config)
    cloud_init_complete: bool = False  # Cloud-init initialization complete


def get_agent_port(agent_index: int, service: str) -> int:
    """
    Calculate the port for a specific service of an agent.
    
    NOTE: This function is for internal use during agent creation only.
    Runtime code should use the port configuration stored in the database.
    """
    if service not in SERVICE_OFFSETS:
        raise ValueError(f"Unknown service: {service}")
    if agent_index < 0 or agent_index >= MAX_AGENTS:
        raise ValueError(f"Agent index must be between 0 and {MAX_AGENTS - 1}")
    
    # SSH and VMUSE use separate port ranges
    if service == "ssh":
        return BASE_PORT + agent_index
    elif service == "vmuse":
        return BASE_VMUSE_PORT + agent_index
    else:
        base = BASE_PORT + agent_index * PORTS_PER_AGENT
        return base + SERVICE_OFFSETS[service]


def allocate_ports_for_agent(agent_index: int) -> PortConfig:
    """
    Allocate ports for an agent based on its index.
    
    NOTE: This function is for internal use during agent creation only.
    It should not be called at runtime. Runtime code should use the
    port configuration stored in the database.
    """
    return PortConfig(
        ssh=get_agent_port(agent_index, "ssh"),
        vmuse=get_agent_port(agent_index, "vmuse"),
    )


class AgentConfigManagerDB:
    """
    Database-backed Agent Configuration Manager (Synchronous).
    
    All operations go directly to SQLite database.
    """
    
    def __init__(self, db: Optional[Database] = None):
        self._db = db
        self._repo: Optional[AgentRepository] = None
        self._data_dir = Path(os.environ.get("NOVAIC_DATA_DIR", "."))
        self._agents_dir = self._data_dir / "agents"  # 与 qemudebug.py 一致
    
    @property
    def db(self) -> Database:
        if self._db is None:
            self._db = get_db()
        return self._db
    
    @property
    def repo(self) -> AgentRepository:
        if self._repo is None:
            self._repo = AgentRepository(self.db)
        return self._repo
    
    def _ensure_dirs(self):
        """Ensure required directories exist."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._agents_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_agent_vm_dir(self, agent_id: str) -> Path:
        """Get VM directory for an agent (matches qemudebug.py path)."""
        return self._agents_dir / agent_id
    
    def _allocate_new_ports(self) -> PortConfig:
        """
        分配新的端口配置，避免与现有 agent 冲突。
        策略：直接扫描数据库中已使用的端口，找到第一个空闲的端口对。
        """
        # 获取所有已存在的 agent
        all_agents = self.repo.list_agents()
        
        # 收集已使用的所有端口
        used_ssh_ports = set()
        used_vmuse_ports = set()
        for agent in all_agents:
            ports = agent.get("ports", {})
            if ports:
                if "ssh" in ports:
                    used_ssh_ports.add(ports["ssh"])
                if "vmuse" in ports:
                    used_vmuse_ports.add(ports["vmuse"])
        
        logger.info(f"[_allocate_new_ports] Used SSH ports: {sorted(used_ssh_ports)}")
        logger.info(f"[_allocate_new_ports] Used VMUSE ports: {sorted(used_vmuse_ports)}")
        
        # 找到第一个空闲的端口对（不使用 index，直接扫描端口范围）
        for offset in range(MAX_AGENTS):
            ssh_port = BASE_PORT + offset
            vmuse_port = BASE_VMUSE_PORT + offset
            if ssh_port not in used_ssh_ports and vmuse_port not in used_vmuse_ports:
                logger.info(f"[_allocate_new_ports] Allocated new ports: SSH={ssh_port}, VMUSE={vmuse_port}")
                return PortConfig(ssh=ssh_port, vmuse=vmuse_port)
        
        raise RuntimeError(f"No available ports (checked {MAX_AGENTS} port pairs from {BASE_PORT}/{BASE_VMUSE_PORT})")
    
    def list_agents(self) -> List[AICAgent]:
        """List all agents."""
        rows = self.repo.list_agents()
        agents = []
        for row in rows:
            vm_config = row.get("vm_config", {})
            ports = row.get("ports", {})
            
            vm_config["ports"] = PortConfig(**ports) if ports else PortConfig()
            
            # Parse Android config if present
            if "android" in vm_config and vm_config["android"]:
                vm_config["android"] = AndroidConfig(**vm_config["android"])
            
            agents.append(AICAgent(
                id=row["id"],
                name=row["name"],
                created_at=row.get("created_at", ""),
                vm=VmConfig(**vm_config),
                setup_complete=row.get("setup_complete", False),
            ))
        return agents
    
    def get_agent(self, agent_id: str) -> Optional[AICAgent]:
        """Get agent by ID."""
        row = self.repo.get_agent(agent_id)
        if not row:
            return None
        
        vm_config = row.get("vm_config", {})
        ports = row.get("ports", {})
        
        vm_config["ports"] = PortConfig(**ports) if ports else PortConfig()
        
        # Parse Android config if present
        if "android" in vm_config and vm_config["android"]:
            vm_config["android"] = AndroidConfig(**vm_config["android"])
        
        return AICAgent(
            id=row["id"],
            name=row["name"],
            created_at=row.get("created_at", ""),
            vm=VmConfig(**vm_config),
            setup_complete=row.get("setup_complete", False),
            cloud_init_complete=row.get("cloud_init_complete", False),
        )
    
    def create_agent(
        self,
        name: str,
        agent_type: str = "linux",  # 'chat' | 'linux' | 'android' | 'hybrid'
        backend: str = "qemu",
        os_type: str = "ubuntu",
        os_version: str = "24.04",
        memory: str = "4096",
        cpus: int = 4,
        source_image: Optional[str] = None,
        android_config: Optional["AndroidConfig"] = None,
    ) -> AICAgent:
        """
        Create a new agent.
        
        Agent types:
        - 'chat': Pure chat agent (no VM/AVD, just LLM)
        - 'linux': Linux VM agent
        - 'android': Android AVD agent
        - 'hybrid': Both Linux VM and Android AVD
        """
        self._ensure_dirs()
        
        agent_id = str(uuid.uuid4())
        
        # Initialize VM config and ports based on agent type
        vm_config = {}
        ports = PortConfig()  # Default empty ports
        
        # Only allocate ports and setup VM for types that need it
        needs_vm = agent_type in ("linux", "hybrid")
        needs_android = agent_type in ("android", "hybrid")
        
        if needs_vm:
            # Allocate ports for VM
            ports = self._allocate_new_ports()
            
            # Build VM config
            vm_config = {
                "backend": backend,
                "os_type": os_type,
                "os_version": os_version,
                "memory": memory,
                "cpus": cpus,
                "image_path": str(self._get_agent_vm_dir(agent_id) / f"{os_type}-{os_version}.qcow2"),
            }
        
        # Add Android config if provided
        if needs_android and android_config:
            vm_config["android"] = android_config.model_dump()
        
        # Create in database
        self.repo.create_agent(
            id=agent_id,
            name=name,
            vm_config=vm_config,
            ports=ports.model_dump(),
            setup_complete=not needs_vm,  # Chat-only agents are always "setup complete"
            agent_type=agent_type,
        )
        
        # Only create VM directory and setup for VM-based agents
        if needs_vm:
            # Create VM directory
            vm_dir = self._get_agent_vm_dir(agent_id)
            vm_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy source image if provided
            if source_image and Path(source_image).exists():
                dest_image = Path(vm_config["image_path"])
                print(f"[AgentConfig] Copying image from {source_image} to {dest_image}")
                shutil.copy2(source_image, dest_image)
            
            # Setup UEFI firmware
            self._setup_uefi_firmware(vm_dir)
        
        return self.get_agent(agent_id)
    
    def update_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        setup_complete: Optional[bool] = None,
        cloud_init_complete: Optional[bool] = None,
        vm_config: Optional[Dict[str, Any]] = None,
        android_config: Optional["AndroidConfig"] = None,
    ) -> Optional[AICAgent]:
        """
        Update agent configuration.
        
        Supports:
        - name: Update agent name
        - setup_complete: Mark VM setup as complete
        - cloud_init_complete: Mark cloud-init as complete
        - vm_config: Update VM configuration (merged with existing)
        - android_config: Add or update Android configuration
        """
        current = self.get_agent(agent_id)
        if not current:
            return None
        
        update_vm = None
        update_ports = None
        
        # Handle VM config update
        if vm_config:
            # Merge with existing VM config
            current_vm = current.vm.model_dump()
            ports = current_vm.pop("ports", {})
            android = current_vm.pop("android", None)  # Preserve existing android config
            
            if "ports" in vm_config:
                ports.update(vm_config.pop("ports"))
            
            current_vm.update(vm_config)
            
            # Restore android config if not being updated
            if android and "android" not in current_vm:
                current_vm["android"] = android
            
            update_vm = current_vm
            update_ports = ports
            
            # If adding VM config to a chat-only agent, allocate ports
            if not ports.get("ssh") and not ports.get("vmuse"):
                new_ports = self._allocate_new_ports()
                update_ports = new_ports.model_dump()
                
                # Create VM directory if needed
                vm_dir = self._get_agent_vm_dir(agent_id)
                vm_dir.mkdir(parents=True, exist_ok=True)
                self._setup_uefi_firmware(vm_dir)
        
        # Handle Android config update
        if android_config:
            if update_vm is None:
                # Start with current VM config
                current_vm = current.vm.model_dump()
                update_ports = current_vm.pop("ports", {})
                update_vm = current_vm
            
            update_vm["android"] = android_config.model_dump()
        
        self.repo.update_agent(
            agent_id=agent_id,
            name=name,
            setup_complete=setup_complete,
            cloud_init_complete=cloud_init_complete,
            vm_config=update_vm,
            ports=update_ports,
        )
        
        return self.get_agent(agent_id)
    
    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent and its VM files.
        
        Uses simple database delete - CASCADE will handle related data cleanup.
        No transaction needed for single DELETE statement.
        """
        # Get current agent for cleanup
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        try:
            # Direct delete without transaction wrapper - SQLite handles this atomically
            # Foreign key CASCADE will automatically delete related data from:
            # - chat_messages, execution_logs, tasks, pending_questions
            # - agent_runtime_state, pipeline_tasks, subagents, vm_processes
            success = self.repo.delete_agent(agent_id)
            logger.info(f"[delete_agent] Deleted agent {agent_id}, CASCADE cleaned up related data")
                
            if success:
                # Delete VM directory after database cleanup
                vm_dir = self._get_agent_vm_dir(agent_id)
                if vm_dir.exists():
                    try:
                        shutil.rmtree(vm_dir)
                        logger.info(f"[delete_agent] Deleted VM directory: {vm_dir}")
                    except Exception as e:
                        logger.warning(f"[delete_agent] Failed to delete VM directory {vm_dir}: {e}")
                
        except Exception as e:
            logger.error(f"[delete_agent] Failed to delete agent {agent_id}: {e}")
            raise
        
        return success
    
    def _setup_uefi_firmware(self, vm_dir: Path) -> None:
        """Copy UEFI firmware from Homebrew QEMU to VM directory (ARM64 only)."""
        if platform.machine() != "arm64":
            return
        
        homebrew_paths = [
            Path("/opt/homebrew/share/qemu/edk2-aarch64-code.fd"),
            Path("/usr/local/share/qemu/edk2-aarch64-code.fd"),
        ]
        
        src_firmware = None
        for p in homebrew_paths:
            if p.exists():
                src_firmware = p
                break
        
        if not src_firmware:
            print("[AgentConfig] Warning: UEFI firmware not found from Homebrew QEMU")
            return
        
        dest_firmware = vm_dir / "QEMU_EFI.fd"
        if not dest_firmware.exists():
            shutil.copy2(src_firmware, dest_firmware)
            print(f"[AgentConfig] Copied UEFI firmware to {dest_firmware}")
        
        dest_vars = vm_dir / "QEMU_VARS.fd"
        if not dest_vars.exists():
            with open(dest_vars, "wb") as f:
                f.write(b"\x00" * (64 * 1024 * 1024))
            print(f"[AgentConfig] Created UEFI VARS at {dest_vars}")
    
    def get_available_images(self) -> List[Dict[str, Any]]:
        """Get list of available base images for cloning."""
        images = []
        
        def scan_directory(directory: Path, source: str):
            if not directory.exists():
                return
            for img in directory.glob("*.img"):
                images.append({
                    "path": str(img),
                    "name": img.stem,
                    "size": img.stat().st_size,
                    "source": source
                })
        
        dev_images_dir = Path.home() / "novaic" / "novaic-vm" / "images"
        scan_directory(dev_images_dir, "development")
        
        user_images_dir = self._data_dir / "images"
        scan_directory(user_images_dir, "user")
        
        return images


# ==================== Alias ====================

# AgentConfigManager is an alias to AgentConfigManagerDB
AgentConfigManager = AgentConfigManagerDB


# Global instances
_agent_config_manager: Optional[AgentConfigManagerDB] = None
_agent_config_manager_db: Optional[AgentConfigManagerDB] = None


def get_agent_config_manager() -> AgentConfigManagerDB:
    """Get the global agent config manager instance."""
    global _agent_config_manager
    if _agent_config_manager is None:
        _agent_config_manager = AgentConfigManagerDB()
    return _agent_config_manager


def get_agent_config_manager_db() -> AgentConfigManagerDB:
    """Get the global agent config manager instance (alias for compatibility)."""
    global _agent_config_manager_db
    if _agent_config_manager_db is None:
        _agent_config_manager_db = AgentConfigManagerDB()
    return _agent_config_manager_db
