"""
AIC Agent Configuration Manager - Database Version

Manages multiple AIC agents using SQLite storage.
All operations are synchronous.
"""

import logging
import os
import uuid
import shutil
import platform
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from common.utils.time import utc_now_iso

logger = logging.getLogger(__name__)

from device.db_access import get_db
from common.db.database import Database
from device.entity_store import get_entity_store


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
    """Linux VM configuration for an agent."""
    backend: str = "qemu"
    image_path: str = ""  # Empty = no VM
    os_type: str = "ubuntu"
    os_version: str = "24.04"
    memory: str = "4096"
    cpus: int = 4
    ports: PortConfig = Field(default_factory=PortConfig)
    # Note: android field removed in v37, now AICAgent.android is independent


class AICAgent(BaseModel):
    """AIC Agent configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: str = Field(default_factory=lambda: utc_now_iso())
    vm: VmConfig = Field(default_factory=VmConfig)
    android: Optional[AndroidConfig] = None  # Independent Android config (v37)
    setup_complete: bool = True  # Default True - no setup step needed
    cloud_init_complete: bool = False  # Cloud-init initialization complete
    model_id: Optional[str] = None  # Selected LLM model ID
    
    # New unified devices list (v38)
    # Will be populated from devices table when loading agent
    devices: List[Any] = Field(default_factory=list)


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
        from common.config import ServiceConfig
        
        self._db = db
        self._data_dir = Path(ServiceConfig.DATA_DIR)
        self._agents_dir = self._data_dir / "agents"
    
    @property
    def db(self) -> Database:
        if self._db is None:
            self._db = get_db()
        return self._db
    
    @property
    def store(self):
        return get_entity_store()
    
    def _ensure_dirs(self):
        """Ensure required directories exist."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._agents_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_devices_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Load devices from devices table for an agent (v38).
        
        DeviceRepository was removed; query via EntityStore instead.
        """
        try:
            rows = self.store.list("devices", "", params={"agent_id": agent_id})
            return list(rows)
        except Exception as e:
            logger.warning(f"[AgentConfigManager] Failed to load devices for agent {agent_id}: {e}")
            return []
    
    def _get_agent_vm_dir(self, agent_id: str) -> Path:
        """Get VM directory for an agent (matches qemudebug.py path)."""
        return self._agents_dir / agent_id
    
    def _allocate_new_ports(self) -> PortConfig:
        """
        分配新的端口配置，避免与现有 agent 冲突。
        策略：直接扫描数据库中已使用的端口，找到第一个空闲的端口对。
        """
        # 获取所有已存在的 agent（系统级查询，需跨用户避免端口冲突）
        all_agents = self.store.list("agents", "")
        
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
    
    def _rows_to_agents(self, rows: list) -> List[AICAgent]:
        """Convert raw DB rows to AICAgent objects."""
        agents = []
        for row in rows:
            vm_config = row.get("vm_config", {})
            ports = row.get("ports", {})
            vm_config["ports"] = PortConfig(**ports) if ports else PortConfig()
            android_config = row.get("android_config")
            android = AndroidConfig(**android_config) if android_config else None
            devices = self._load_devices_for_agent(row["id"])
            agents.append(AICAgent(
                id=row["id"],
                name=row["name"],
                created_at=row.get("created_at", ""),
                vm=VmConfig(**vm_config),
                android=android,
                setup_complete=row.get("setup_complete", False),
                model_id=row.get("model_id"),
                devices=devices,
            ))
        return agents

    def list_all_agents(self) -> List[AICAgent]:
        """List ALL agents across all users (internal/system use only)."""
        return self._rows_to_agents(self.store.list("agents", ""))

    def list_agents(self, user_id: str, updated_after: Optional[str] = None) -> List[AICAgent]:
        """List agents belonging to user_id."""
        rows = self.store.list("agents", user_id)
        if updated_after:
            rows = [r for r in rows if (r.get("updated_at") or r.get("created_at", "")) > updated_after]
        return self._rows_to_agents(rows)
    
    def get_agent(self, agent_id: str) -> Optional[AICAgent]:
        """Get agent by ID."""
        row = self.store.get("agents", "", agent_id)
        if not row:
            return None
        
        vm_config = row.get("vm_config", {})
        ports = row.get("ports", {})
        
        vm_config["ports"] = PortConfig(**ports) if ports else PortConfig()
        
        # Parse independent android_config
        android_config = row.get("android_config")
        android = AndroidConfig(**android_config) if android_config else None
        
        # Load devices from devices table (v38)
        devices = self._load_devices_for_agent(agent_id)
        
        return AICAgent(
            id=row["id"],
            name=row["name"],
            created_at=row.get("created_at", ""),
            vm=VmConfig(**vm_config),
            android=android,
            setup_complete=row.get("setup_complete", False),
            cloud_init_complete=row.get("cloud_init_complete", False),
            model_id=row.get("model_id"),
            devices=devices,
        )
    
    def create_agent(
        self,
        name: str,
        user_id: str,
        model_id: Optional[str] = None,
    ) -> AICAgent:
        """
        创建 Agent，默认无设备配置。
        用户可以后续通过 update_agent 添加 VM 或 Android 配置。

        Args:
            name: Agent 名称
            user_id: 所属用户 ID（v44）
            model_id: LLM 模型 ID（可选，由 API 层处理）

        Returns:
            新创建的 AICAgent
        """
        self._ensure_dirs()

        agent_id = str(uuid.uuid4())

        # 创建空的 VM 配置（无 image_path 表示无 VM）
        vm_config = VmConfig()  # 默认 image_path=""

        self.store.create(
            "agents",
            user_id,
            {
                "id": agent_id,
                "name": name,
                "vm_config": vm_config.model_dump(),
                "ports": {},  # 无端口分配
                "user_id": user_id,
                "setup_complete": 1,
            }
        )
        
        # model_id 由 API 层直接更新数据库
        
        return self.get_agent(agent_id)
    
    def update_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        setup_complete: Optional[bool] = None,
        cloud_init_complete: Optional[bool] = None,
        vm_config: Optional[Dict[str, Any]] = None,
        android_config: Optional["AndroidConfig"] = None,
        user_id: Optional[str] = None,
    ) -> Optional[AICAgent]:
        """
        Update agent configuration.
        
        Supports:
        - name: Update agent name
        - setup_complete: Mark VM setup as complete
        - cloud_init_complete: Mark cloud-init as complete
        - vm_config: Update VM configuration (merged with existing)
        - android_config: Add or update Android configuration (independent field)
        """
        current = self.get_agent(agent_id)
        if not current:
            return None
        
        update_vm = None
        update_ports = None
        update_android = None
        
        # Handle VM config update
        if vm_config:
            # Merge with existing VM config
            current_vm = current.vm.model_dump()
            ports = current_vm.pop("ports", {})
            
            if "ports" in vm_config:
                ports.update(vm_config.pop("ports"))
            
            current_vm.update(vm_config)
            
            update_vm = current_vm
            update_ports = ports
            
            # If adding VM config to a chat-only agent, allocate ports and set image_path
            if not ports.get("ssh") and not ports.get("vmuse"):
                new_ports = self._allocate_new_ports()
                update_ports = new_ports.model_dump()
                
                # Create VM directory if needed
                vm_dir = self._get_agent_vm_dir(agent_id)
                vm_dir.mkdir(parents=True, exist_ok=True)
                self._setup_uefi_firmware(vm_dir)
                
                # Set image_path to the standard disk location
                # VmSetup.setup_vm will create disk.qcow2 at this location
                update_vm["image_path"] = str(vm_dir / "disk.qcow2")
            # Ensure image_path is set when ports exist but image_path is empty
            elif ports.get("ssh") or ports.get("vmuse"):
                current_image_path = current.vm.image_path if current.vm else ""
                if not current_image_path:
                    vm_dir = self._get_agent_vm_dir(agent_id)
                    vm_dir.mkdir(parents=True, exist_ok=True)
                    self._setup_uefi_firmware(vm_dir)
                    update_vm["image_path"] = str(vm_dir / "disk.qcow2")
        
        # Handle Android config update (independent field)
        if android_config:
            update_android = android_config.model_dump()
        
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if setup_complete is not None:
            update_data["setup_complete"] = 1 if setup_complete else 0
        if cloud_init_complete is not None:
            update_data["cloud_init_complete"] = 1 if cloud_init_complete else 0
        if update_vm is not None:
            update_data["vm_config"] = update_vm
        if update_ports is not None:
            update_data["ports"] = update_ports
        if update_android is not None:
            update_data["android_config"] = update_android

        self.store.update("agents", user_id or "", agent_id, update_data)
        
        return self.get_agent(agent_id)
    
    def delete_agent(self, agent_id: str, user_id: Optional[str] = None) -> bool:
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
            success = self.store.delete("agents", user_id or "", agent_id)
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
            logger.warning("[AgentConfig] UEFI firmware not found from Homebrew QEMU")
            return
        
        dest_firmware = vm_dir / "QEMU_EFI.fd"
        if not dest_firmware.exists():
            shutil.copy2(src_firmware, dest_firmware)
            logger.info("[AgentConfig] Copied UEFI firmware to %s", dest_firmware)
        
        dest_vars = vm_dir / "QEMU_VARS.fd"
        if not dest_vars.exists():
            with open(dest_vars, "wb") as f:
                f.write(b"\x00" * (64 * 1024 * 1024))
            logger.info("[AgentConfig] Created UEFI VARS at %s", dest_vars)
    
    def remove_vm_config(self, agent_id: str) -> bool:
        """移除 VM 配置"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        # 重置 VM 配置为空
        empty_vm = VmConfig()  # image_path=""
        self.store.update("agents", "", agent_id, {
            "vm_config": empty_vm.model_dump(),
            "ports": {},
            "setup_complete": 0,
            "cloud_init_complete": 0,
        })
        return True

    def remove_android_config(self, agent_id: str) -> bool:
        """移除 Android 配置"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        self.store.update("agents", "", agent_id, {
            "android_config": None,
        })
        return True

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
