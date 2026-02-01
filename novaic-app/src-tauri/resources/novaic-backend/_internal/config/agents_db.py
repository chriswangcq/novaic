"""
AIC Agent Configuration Manager - Database Version

Manages multiple AIC agents using SQLite storage.
"""

import os
import json
import uuid
import shutil
import asyncio
import platform
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from db.database import get_database, Database
from db.repositories.agent import AgentRepository


# Port allocation constants
GATEWAY_PORT = 19999
BASE_PORT = 20000
PORTS_PER_AGENT = 20
MAX_AGENTS = 100

SERVICE_OFFSETS = {
    "vm": 0,
    "session": 1,
    "local": 2,
    "memory": 3,
    "chat": 4,
    "qemudebug": 5,
    "vnc": 6,
    "websocket": 7,
    "ssh": 8,
}


class PortConfig(BaseModel):
    """Port configuration for an agent."""
    vm: int = 20000
    session: int = 20001
    local: int = 20002
    memory: int = 20003
    chat: int = 20004
    qemudebug: int = 20005
    vnc: int = 20006
    websocket: int = 20007
    ssh: int = 20008


class VmConfig(BaseModel):
    """VM configuration for an agent."""
    backend: str = "qemu"
    image_path: str = ""
    os_type: str = "ubuntu"
    os_version: str = "24.04"
    memory: str = "4096"
    cpus: int = 4
    ports: PortConfig = Field(default_factory=PortConfig)
    mcp_vm_port: int = 8080
    vnc_vm_port: int = 5900
    ws_vm_port: int = 6080
    agent_index: int = 0


class AICAgent(BaseModel):
    """AIC Agent configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    vm: VmConfig = Field(default_factory=VmConfig)
    setup_complete: bool = False


def get_agent_port(agent_index: int, service: str) -> int:
    """Calculate the port for a specific service of an agent."""
    if service not in SERVICE_OFFSETS:
        raise ValueError(f"Unknown service: {service}")
    if agent_index < 0 or agent_index >= MAX_AGENTS:
        raise ValueError(f"Agent index must be between 0 and {MAX_AGENTS - 1}")
    
    base = BASE_PORT + agent_index * PORTS_PER_AGENT
    return base + SERVICE_OFFSETS[service]


def allocate_ports_for_agent(agent_index: int) -> PortConfig:
    """Allocate all ports for an agent based on its index."""
    base = BASE_PORT + agent_index * PORTS_PER_AGENT
    return PortConfig(
        vm=base + SERVICE_OFFSETS["vm"],
        session=base + SERVICE_OFFSETS["session"],
        local=base + SERVICE_OFFSETS["local"],
        memory=base + SERVICE_OFFSETS["memory"],
        chat=base + SERVICE_OFFSETS["chat"],
        qemudebug=base + SERVICE_OFFSETS["qemudebug"],
        vnc=base + SERVICE_OFFSETS["vnc"],
        websocket=base + SERVICE_OFFSETS["websocket"],
        ssh=base + SERVICE_OFFSETS["ssh"],
    )


class AgentConfigManagerDB:
    """
    Database-backed Agent Configuration Manager.
    
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
            self._db = get_database()
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
    
    async def list_agents(self) -> List[AICAgent]:
        """List all agents."""
        rows = await self.repo.list_agents()
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
    
    async def get_agent(self, agent_id: str) -> Optional[AICAgent]:
        """Get agent by ID."""
        row = await self.repo.get_agent(agent_id)
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
    
    async def create_agent(
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
        
        # Find next available agent index
        agent_index = await self.repo.find_next_agent_index()
        ports = allocate_ports_for_agent(agent_index)
        
        agent_id = str(uuid.uuid4())
        
        # Build VM config
        vm_config = {
            "backend": backend,
            "os_type": os_type,
            "os_version": os_version,
            "memory": memory,
            "cpus": cpus,
            "mcp_vm_port": 8080,
            "vnc_vm_port": 5900,
            "ws_vm_port": 6080,
            "agent_index": agent_index,
            "image_path": str(self._get_agent_vm_dir(agent_id) / f"{os_type}-{os_version}.qcow2"),
        }
        
        # Create in database
        await self.repo.create_agent(
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
        
        # Set as current if first agent
        current = await self.repo.get_current_agent_id()
        if current is None:
            await self.repo.set_current_agent_id(agent_id)
        
        return await self.get_agent(agent_id)
    
    async def update_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        setup_complete: Optional[bool] = None,
        vm_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[AICAgent]:
        """Update agent configuration."""
        current = await self.get_agent(agent_id)
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
        
        await self.repo.update_agent(
            agent_id=agent_id,
            name=name,
            setup_complete=setup_complete,
            vm_config=update_vm,
            ports=update_ports,
        )
        
        return await self.get_agent(agent_id)
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent and its VM files."""
        # Get current agent for cleanup
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        # Delete from database
        success = await self.repo.delete_agent(agent_id)
        
        if success:
            # Update current agent if needed
            current_id = await self.repo.get_current_agent_id()
            if current_id == agent_id:
                agents = await self.list_agents()
                if agents:
                    await self.repo.set_current_agent_id(agents[0].id)
                else:
                    await self.repo.set_current_agent_id(None)
            
            # Delete VM directory
            vm_dir = self._get_agent_vm_dir(agent_id)
            if vm_dir.exists():
                shutil.rmtree(vm_dir)
        
        return success
    
    async def get_current_agent(self) -> Optional[AICAgent]:
        """Get the currently selected agent."""
        agent_id = await self.repo.get_current_agent_id()
        if agent_id:
            return await self.get_agent(agent_id)
        return None
    
    async def set_current_agent(self, agent_id: str) -> bool:
        """Set the current agent."""
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        await self.repo.set_current_agent_id(agent_id)
        return True
    
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
    
    async def get_available_images(self) -> List[Dict[str, Any]]:
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


# ==================== Sync Wrapper for Backward Compatibility ====================

class AgentConfigManager:
    """
    Synchronous wrapper around AgentConfigManagerDB.
    """
    
    def __init__(self):
        self._async_manager = AgentConfigManagerDB()
    
    def _run_async(self, coro):
        """Run an async coroutine synchronously."""
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            return asyncio.run(coro)
    
    def load(self):
        """Compatibility method - returns self."""
        return self
    
    def reload(self):
        """Compatibility method - returns self."""
        return self
    
    def list_agents(self) -> List[AICAgent]:
        """List all agents."""
        return self._run_async(self._async_manager.list_agents())
    
    def get_agent(self, agent_id: str) -> Optional[AICAgent]:
        """Get agent by ID."""
        return self._run_async(self._async_manager.get_agent(agent_id))
    
    def create_agent(self, **kwargs) -> AICAgent:
        """Create agent."""
        return self._run_async(self._async_manager.create_agent(**kwargs))
    
    def update_agent(self, agent_id: str, **kwargs) -> Optional[AICAgent]:
        """Update agent."""
        return self._run_async(self._async_manager.update_agent(agent_id, **kwargs))
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent."""
        return self._run_async(self._async_manager.delete_agent(agent_id))
    
    def get_current_agent(self) -> Optional[AICAgent]:
        """Get current agent."""
        return self._run_async(self._async_manager.get_current_agent())
    
    def set_current_agent(self, agent_id: str) -> bool:
        """Set current agent."""
        return self._run_async(self._async_manager.set_current_agent(agent_id))
    
    def get_available_images(self) -> List[Dict[str, Any]]:
        """Get available images."""
        return self._run_async(self._async_manager.get_available_images())


# Global instances
_agent_config_manager: Optional[AgentConfigManager] = None
_agent_config_manager_db: Optional[AgentConfigManagerDB] = None


def get_agent_config_manager() -> AgentConfigManager:
    """Get the global sync agent config manager instance."""
    global _agent_config_manager
    if _agent_config_manager is None:
        _agent_config_manager = AgentConfigManager()
    return _agent_config_manager


def get_agent_config_manager_db() -> AgentConfigManagerDB:
    """Get the global async agent config manager instance."""
    global _agent_config_manager_db
    if _agent_config_manager_db is None:
        _agent_config_manager_db = AgentConfigManagerDB()
    return _agent_config_manager_db
