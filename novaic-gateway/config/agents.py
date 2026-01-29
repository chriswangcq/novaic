"""
AIC Agent Configuration Manager

Manages multiple AIC agents, each with its own VM configuration.
Storage: $NOVAIC_DATA_DIR/agents.json
NOVAIC_DATA_DIR is required (passed from Tauri app).
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
import json
import uuid
import os
import shutil
import platform


class PortConfig(BaseModel):
    """
    Complete port configuration for an agent.
    
    Each agent gets a contiguous block of 20 ports starting from BASE_PORT + agent_index * 20.
    
    Port layout (offsets 0-19):
        0: vm        - VM内MCP服务 (vmuse)
        1: session   - 会话管理MCP
        2: local     - 本地文件MCP
        3: memory    - 记忆管理MCP
        4: chat      - 用户通信MCP
        5: qemudebug - QEMU调试MCP
        6: vnc       - VNC服务
        7: websocket - noVNC WebSocket
        8: ssh       - SSH转发
        9-19: reserved - 预留扩展
    """
    # MCP服务端口
    vm: int = 20000           # VM内MCP (vmuse)
    session: int = 20001      # 会话管理MCP
    local: int = 20002        # 本地文件MCP
    memory: int = 20003       # 记忆管理MCP
    chat: int = 20004         # 用户通信MCP
    qemudebug: int = 20005    # QEMU调试MCP
    # VM连接端口
    vnc: int = 20006          # VNC服务
    websocket: int = 20007    # noVNC WebSocket
    ssh: int = 20008          # SSH转发


class VmConfig(BaseModel):
    """VM configuration for an agent"""
    backend: str = "qemu"  # qemu | virtualization_framework
    image_path: str = ""   # Path to qcow2 image
    os_type: str = "ubuntu"  # ubuntu, debian, etc.
    os_version: str = "24.04"  # 24.04, 22.04, etc.
    memory: str = "4096"   # Memory in MB
    cpus: int = 4          # CPU cores
    ports: PortConfig = Field(default_factory=PortConfig)
    # VM 内部端口 (固定，通过QEMU端口转发映射到宿主机动态端口)
    mcp_vm_port: int = 8080    # VM 内部 MCP 端口 (固定)
    vnc_vm_port: int = 5900    # VM 内部 VNC 端口 (固定)
    ws_vm_port: int = 6080     # VM 内部 WebSocket 端口 (固定)
    # 兼容性字段 (用于Agent索引计算)
    agent_index: int = 0       # Agent索引，用于端口分配


class AICAgent(BaseModel):
    """AIC Agent configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    vm: VmConfig = Field(default_factory=VmConfig)
    
    # Runtime status (not persisted, default to stopped for loaded agents)
    # pending = newly created, awaiting setup
    # stopped/starting/running/error = runtime states
    status: str = "stopped"


class AgentsConfig(BaseModel):
    """Root configuration for all agents"""
    version: int = 1
    current_agent_id: Optional[str] = None
    agents: List[AICAgent] = []


# Centralized port allocation configuration
# Port layout:
#   19999         - Gateway (固定)
#   20000-21999   - Agents (100个 × 20端口)
GATEWAY_PORT = 19999        # Gateway 固定端口
BASE_PORT = 20000           # Agent 基础端口号
PORTS_PER_AGENT = 20        # 每个Agent分配的端口数量
MAX_AGENTS = 100            # 最大支持的Agent数量

# 服务端口偏移量 (相对于Agent基础端口)
SERVICE_OFFSETS = {
    "vm": 0,           # VM内MCP (vmuse)
    "session": 1,      # 会话管理MCP
    "local": 2,        # 本地文件MCP
    "memory": 3,       # 记忆管理MCP
    "chat": 4,         # 用户通信MCP
    "qemudebug": 5,    # QEMU调试MCP
    "vnc": 6,          # VNC服务
    "websocket": 7,    # noVNC WebSocket
    "ssh": 8,          # SSH转发
    # 9-19: 预留扩展
}


def get_agent_port(agent_index: int, service: str) -> int:
    """
    Calculate the port for a specific service of an agent.
    
    Args:
        agent_index: Agent index (0, 1, 2, ...)
        service: Service name (vm, session, local, memory, chat, qemudebug, vnc, websocket, ssh)
    
    Returns:
        Port number
        
    Example:
        Agent 0: vm=20000, session=20001, ..., ssh=20008
        Agent 1: vm=20020, session=20021, ..., ssh=20028
    """
    if service not in SERVICE_OFFSETS:
        raise ValueError(f"Unknown service: {service}. Valid services: {list(SERVICE_OFFSETS.keys())}")
    if agent_index < 0 or agent_index >= MAX_AGENTS:
        raise ValueError(f"Agent index must be between 0 and {MAX_AGENTS - 1}")
    
    base = BASE_PORT + agent_index * PORTS_PER_AGENT
    return base + SERVICE_OFFSETS[service]


def allocate_ports_for_agent(agent_index: int) -> PortConfig:
    """
    Allocate all ports for an agent based on its index.
    
    Args:
        agent_index: Agent index (0, 1, 2, ...)
    
    Returns:
        PortConfig with all ports assigned
    """
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


class AgentConfigManager:
    """
    Manages AIC Agent configurations.
    
    Storage:
    - Config: $NOVAIC_DATA_DIR/agents.json
    - VMs: $NOVAIC_DATA_DIR/vms/{agent-id}/
    
    NOVAIC_DATA_DIR is required (passed from Tauri app).
    """
    
    def __init__(self):
        if not os.environ.get("NOVAIC_DATA_DIR"):
            raise RuntimeError("NOVAIC_DATA_DIR environment variable is required")
        self._config_dir = Path(os.environ["NOVAIC_DATA_DIR"])
        self._config_file = self._config_dir / "agents.json"
        self._vms_dir = self._config_dir / "vms"
        self._cache: Optional[AgentsConfig] = None
    
    def _ensure_dirs(self):
        """Ensure required directories exist"""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._vms_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> AgentsConfig:
        """Load agents configuration"""
        if self._cache is not None:
            return self._cache
        
        self._ensure_dirs()
        
        if self._config_file.exists():
            try:
                data = json.loads(self._config_file.read_text())
                self._cache = AgentsConfig(**data)
            except Exception as e:
                print(f"[AgentConfig] Failed to load config: {e}")
                self._cache = AgentsConfig()
        else:
            self._cache = AgentsConfig()
        
        return self._cache
    
    def save(self):
        """Save agents configuration"""
        if self._cache is None:
            return
        
        self._ensure_dirs()
        
        # Don't save runtime status
        data = self._cache.model_dump()
        for agent in data.get("agents", []):
            agent.pop("status", None)
        
        self._config_file.write_text(json.dumps(data, indent=2))
        
        # Set file permissions (Unix only)
        if os.name != "nt":
            os.chmod(self._config_file, 0o600)
    
    def reload(self) -> AgentsConfig:
        """Force reload configuration"""
        self._cache = None
        return self.load()
    
    def get_agent(self, agent_id: str) -> Optional[AICAgent]:
        """Get agent by ID"""
        config = self.load()
        for agent in config.agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def list_agents(self) -> List[AICAgent]:
        """List all agents"""
        return self.load().agents
    
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
        """
        Create a new agent.
        
        Args:
            name: Agent display name
            backend: Virtualization backend (qemu | virtualization_framework)
            os_type: OS type (ubuntu, debian, etc.)
            os_version: OS version
            memory: Memory in MB
            cpus: CPU cores
            source_image: Source image to copy (if provided)
        
        Returns:
            Created agent
        """
        config = self.load()
        
        # Allocate resources (find next available agent index)
        agent_index = self._find_next_agent_index(config)
        ports = allocate_ports_for_agent(agent_index)
        
        # Create agent with pending status (needs setup)
        agent_id = str(uuid.uuid4())
        agent = AICAgent(
            id=agent_id,
            name=name,
            status="pending",  # New agent needs setup
            vm=VmConfig(
                backend=backend,
                os_type=os_type,
                os_version=os_version,
                memory=memory,
                cpus=cpus,
                ports=ports,
                mcp_vm_port=8080,   # VM 内部 MCP 端口 (固定)
                vnc_vm_port=5900,   # VM 内部 VNC 端口 (固定)
                ws_vm_port=6080,    # VM 内部 WebSocket 端口 (固定)
                agent_index=agent_index,
                image_path=str(self._get_agent_vm_dir(agent_id) / f"{os_type}-{os_version}.qcow2"),
            )
        )
        
        # Create VM directory
        vm_dir = self._get_agent_vm_dir(agent_id)
        vm_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy source image if provided
        if source_image and Path(source_image).exists():
            dest_image = Path(agent.vm.image_path)
            print(f"[AgentConfig] Copying image from {source_image} to {dest_image}")
            shutil.copy2(source_image, dest_image)
        
        # Copy UEFI firmware from Homebrew QEMU (ARM64 only)
        self._setup_uefi_firmware(vm_dir)
        
        # Note: cloud-init seed ISO is created by novaic-app/src-tauri/src/vm/setup.rs
        # Do NOT create seed.iso here, it would override the complete version
        
        # Add to config
        config.agents.append(agent)
        
        # Set as current if first agent
        if config.current_agent_id is None:
            config.current_agent_id = agent.id
        
        self.save()
        return agent
    
    def update_agent(self, agent_id: str, **kwargs) -> Optional[AICAgent]:
        """Update agent configuration"""
        config = self.load()
        
        for i, agent in enumerate(config.agents):
            if agent.id == agent_id:
                # Update fields
                for key, value in kwargs.items():
                    if key == "vm" and isinstance(value, dict):
                        # Update VM config
                        for vm_key, vm_value in value.items():
                            if vm_key == "ports" and isinstance(vm_value, dict):
                                for port_key, port_value in vm_value.items():
                                    setattr(agent.vm.ports, port_key, port_value)
                            else:
                                setattr(agent.vm, vm_key, vm_value)
                    elif hasattr(agent, key):
                        setattr(agent, key, value)
                
                config.agents[i] = agent
                self.save()
                return agent
        
        return None
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent and its VM files"""
        config = self.load()
        
        for i, agent in enumerate(config.agents):
            if agent.id == agent_id:
                # Remove from config
                config.agents.pop(i)
                
                # Update current agent if needed
                if config.current_agent_id == agent_id:
                    config.current_agent_id = config.agents[0].id if config.agents else None
                
                # Delete VM directory
                vm_dir = self._get_agent_vm_dir(agent_id)
                if vm_dir.exists():
                    shutil.rmtree(vm_dir)
                
                self.save()
                return True
        
        return False
    
    def get_current_agent(self) -> Optional[AICAgent]:
        """Get the currently selected agent"""
        config = self.load()
        if config.current_agent_id:
            return self.get_agent(config.current_agent_id)
        return None
    
    def set_current_agent(self, agent_id: str) -> bool:
        """Set the current agent"""
        config = self.load()
        
        # Verify agent exists
        if not self.get_agent(agent_id):
            return False
        
        config.current_agent_id = agent_id
        self.save()
        return True
    
    def _get_agent_vm_dir(self, agent_id: str) -> Path:
        """Get VM directory for an agent"""
        return self._vms_dir / agent_id
    
    def _find_next_agent_index(self, config: AgentsConfig) -> int:
        """
        Find the next available agent index for port allocation.
        
        This finds gaps in the sequence to reuse indices from deleted agents.
        
        Returns:
            Next available agent index (0, 1, 2, ...)
        """
        # Collect used indices
        used_indices = set()
        for agent in config.agents:
            used_indices.add(agent.vm.agent_index)
        
        # Find next available index (fill gaps first)
        index = 0
        while index in used_indices:
            index += 1
        
        if index >= MAX_AGENTS:
            raise RuntimeError(f"Maximum number of agents ({MAX_AGENTS}) reached")
        
        return index
    
    def _allocate_ports(self, config: AgentsConfig) -> PortConfig:
        """Allocate unique ports for a new agent"""
        agent_index = self._find_next_agent_index(config)
        return allocate_ports_for_agent(agent_index)
    
    def _setup_uefi_firmware(self, vm_dir: Path) -> None:
        """Copy UEFI firmware from Homebrew QEMU to VM directory (ARM64 only)"""
        import platform
        import subprocess
        
        if platform.machine() != "arm64":
            return
        
        # Homebrew QEMU UEFI paths
        homebrew_paths = [
            Path("/opt/homebrew/share/qemu/edk2-aarch64-code.fd"),
            Path("/usr/local/share/qemu/edk2-aarch64-code.fd"),
        ]
        
        # Find UEFI firmware
        src_firmware = None
        for p in homebrew_paths:
            if p.exists():
                src_firmware = p
                break
        
        if not src_firmware:
            print("[AgentConfig] Warning: UEFI firmware not found from Homebrew QEMU")
            return
        
        # Copy firmware (read-only)
        dest_firmware = vm_dir / "QEMU_EFI.fd"
        if not dest_firmware.exists():
            shutil.copy2(src_firmware, dest_firmware)
            print(f"[AgentConfig] Copied UEFI firmware to {dest_firmware}")
        
        # Create empty VARS file (writable, for NVRAM)
        dest_vars = vm_dir / "QEMU_VARS.fd"
        if not dest_vars.exists():
            # Create 64MB empty file for NVRAM
            with open(dest_vars, "wb") as f:
                f.write(b"\x00" * (64 * 1024 * 1024))
            print(f"[AgentConfig] Created UEFI VARS at {dest_vars}")
    
    def get_available_images(self) -> List[Dict[str, Any]]:
        """
        Get list of available base images (cloud images) for cloning.
        
        Returns .img files from:
        - novaic-vm/images/ (development)
        - $NOVAIC_DATA_DIR/images/ (user downloaded)
        """
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
        
        # Check novaic-vm/images (development path)
        dev_images_dir = Path.home() / "novaic" / "novaic-vm" / "images"
        scan_directory(dev_images_dir, "development")
        
        # Check $NOVAIC_DATA_DIR/images (user images)
        user_images_dir = self._config_dir / "images"
        scan_directory(user_images_dir, "user")
        
        return images


# Global instance - use database-backed version
from .agents_db import (
    AgentConfigManager,
    AgentConfigManagerDB,
    get_agent_config_manager,
    get_agent_config_manager_db,
)

# Re-export for backward compatibility
__all__ = [
    # Constants
    "GATEWAY_PORT",
    "BASE_PORT",
    "PORTS_PER_AGENT",
    "MAX_AGENTS",
    "SERVICE_OFFSETS",
    # Functions
    "get_agent_port",
    "allocate_ports_for_agent",
    # Classes
    "PortConfig",
    "VmConfig",
    "AICAgent",
    "AgentsConfig",
    # Managers
    "AgentConfigManager",
    "AgentConfigManagerDB",
    "get_agent_config_manager",
    "get_agent_config_manager_db",
]
