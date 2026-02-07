"""
AIC Agent Configuration Manager - Database Version

Manages multiple AIC agents using SQLite storage.
All operations are synchronous.
"""

import os
import json
import uuid
import shutil
import platform
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from gateway.db.access import get_db
from common.db.database import Database
from gateway.db.repositories.agent import AgentRepository


# Port allocation constants
GATEWAY_PORT = 19999
BASE_PORT = 20000
PORTS_PER_AGENT = 1  # Only SSH port needed
MAX_AGENTS = 100

SERVICE_OFFSETS = {
    "ssh": 0,  # Only SSH port needed
}


class PortConfig(BaseModel):
    """Port configuration for an agent - SSH and VMUSE HTTP."""
    ssh: int = 20000   # SSH port for VM access
    vmuse: int = 18080  # VMUSE HTTP API port


class VmConfig(BaseModel):
    """VM configuration for an agent."""
    backend: str = "qemu"
    image_path: str = ""
    os_type: str = "ubuntu"
    os_version: str = "24.04"
    memory: str = "4096"
    cpus: int = 4
    ports: PortConfig = Field(default_factory=PortConfig)


class AICAgent(BaseModel):
    """AIC Agent configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    vm: VmConfig = Field(default_factory=VmConfig)
    setup_complete: bool = False


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
    
    base = BASE_PORT + agent_index * PORTS_PER_AGENT
    return base + SERVICE_OFFSETS[service]


def allocate_ports_for_agent(agent_index: int) -> PortConfig:
    """
    Allocate ports for an agent based on its index.
    
    NOTE: This function is for internal use during agent creation only.
    It should not be called at runtime. Runtime code should use the
    port configuration stored in the database.
    """
    base = BASE_PORT + agent_index * PORTS_PER_AGENT
    return PortConfig(
        ssh=base + SERVICE_OFFSETS["ssh"],
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
        策略：查询所有已使用的 SSH 端口，找到下一个可用的端口范围。
        """
        # 获取所有已存在的 agent
        all_agents = self.repo.list_agents()
        
        # 收集已使用的 SSH 端口（作为端口范围的标识）
        used_ssh_ports = set()
        for agent in all_agents:
            ports = agent.get("ports", {})
            if ports and "ssh" in ports:
                used_ssh_ports.add(ports["ssh"])
        
        # 找到下一个可用的端口范围
        # 假设每个 agent 占用 PORTS_PER_AGENT 个端口
        index = 0
        while True:
            base_port = BASE_PORT + index * PORTS_PER_AGENT
            ssh_port = base_port + SERVICE_OFFSETS["ssh"]
            if ssh_port not in used_ssh_ports:
                break
            index += 1
            if index >= MAX_AGENTS:
                raise RuntimeError(f"No available ports (max {MAX_AGENTS} agents)")
        
        # 使用现有的 allocate_ports_for_agent 函数分配完整的端口配置
        return allocate_ports_for_agent(index)
    
    def list_agents(self) -> List[AICAgent]:
        """List all agents."""
        rows = self.repo.list_agents()
        agents = []
        for row in rows:
            vm_config = row.get("vm_config", {})
            ports = row.get("ports", {})
            
            vm_config["ports"] = PortConfig(**ports) if ports else PortConfig()
            
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
        
        return AICAgent(
            id=row["id"],
            name=row["name"],
            created_at=row.get("created_at", ""),
            vm=VmConfig(**vm_config),
            setup_complete=row.get("setup_complete", False),
        )
    
    def create_agent(
        self,
        name: str,
        backend: str = "qemu",
        os_type: str = "ubuntu",
        os_version: str = "24.04",
        memory: str = "4096",
        cpus: int = 4,
        source_image: Optional[str] = None,
    ) -> AICAgent:
        """Create a new agent."""
        self._ensure_dirs()
        
        # 分配新端口（基于已使用端口找到空闲范围）
        ports = self._allocate_new_ports()
        
        agent_id = str(uuid.uuid4())
        
        # Build VM config
        vm_config = {
            "backend": backend,
            "os_type": os_type,
            "os_version": os_version,
            "memory": memory,
            "cpus": cpus,
            "image_path": str(self._get_agent_vm_dir(agent_id) / f"{os_type}-{os_version}.qcow2"),
        }
        
        # Create in database
        self.repo.create_agent(
            id=agent_id,
            name=name,
            vm_config=vm_config,
            ports=ports.model_dump(),
            setup_complete=False,
        )
        
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
        vm_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[AICAgent]:
        """Update agent configuration."""
        current = self.get_agent(agent_id)
        if not current:
            return None
        
        update_vm = None
        update_ports = None
        
        if vm_config:
            # Merge with existing VM config
            current_vm = current.vm.model_dump()
            ports = current_vm.pop("ports", {})
            
            if "ports" in vm_config:
                ports.update(vm_config.pop("ports"))
            
            current_vm.update(vm_config)
            update_vm = current_vm
            update_ports = ports
        
        self.repo.update_agent(
            agent_id=agent_id,
            name=name,
            setup_complete=setup_complete,
            vm_config=update_vm,
            ports=update_ports,
        )
        
        return self.get_agent(agent_id)
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent and its VM files."""
        # Get current agent for cleanup
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        # 手动清理相关数据（确保兼容没有外键约束的旧数据库）
        # 对于新数据库，外键约束会自动级联删除，但这个手动清理逻辑是安全的冗余
        db = get_db()
        with db.transaction("agent_cleanup", resource_id=agent_id):
            # 删除所有关联的数据
            db.execute("DELETE FROM chat_messages WHERE agent_id = ?", (agent_id,))
            db.execute("DELETE FROM execution_logs WHERE agent_id = ?", (agent_id,))
            db.execute("DELETE FROM tasks WHERE agent_id = ?", (agent_id,))
            db.execute("DELETE FROM pending_questions WHERE agent_id = ?", (agent_id,))
            db.execute("DELETE FROM agent_runtime_state WHERE agent_id = ?", (agent_id,))
            # pipeline_tasks 允许 NULL agent_id，只删除关联的
            db.execute("DELETE FROM pipeline_tasks WHERE agent_id = ?", (agent_id,))
            
            # Delete from database (will also trigger cascade if foreign keys exist)
            success = self.repo.delete_agent(agent_id)
        
        if success:
            # Delete VM directory
            vm_dir = self._get_agent_vm_dir(agent_id)
            if vm_dir.exists():
                shutil.rmtree(vm_dir)
        
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
