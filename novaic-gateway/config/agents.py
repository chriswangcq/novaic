"""
AIC Agent Configuration Manager

Manages multiple AIC agents, each with its own VM configuration.
Storage: ~/.novaic/agents.json
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
import json
import uuid
import os
import shutil


class PortConfig(BaseModel):
    """Port configuration for an agent's VM (仅用于 VNC/websockify/SSH)"""
    vnc: int = 5900
    websocket: int = 6080
    ssh: int = 2222


class VmConfig(BaseModel):
    """VM configuration for an agent"""
    backend: str = "qemu"  # qemu | virtualization_framework
    image_path: str = ""   # Path to qcow2 image
    os_type: str = "ubuntu"  # ubuntu, debian, etc.
    os_version: str = "24.04"  # 24.04, 22.04, etc.
    memory: str = "4096"   # Memory in MB
    cpus: int = 4          # CPU cores
    ports: PortConfig = Field(default_factory=PortConfig)
    # MCP 通信配置
    mcp_host_port: int = 8081  # 宿主机 MCP 端口 (QEMU 端口转发: 宿主机 -> VM 8080)
    mcp_vm_port: int = 8080    # VM 内部 MCP 端口 (固定)
    # 兼容性字段 (保留)
    vsock_cid: int = 3         # 用于 Agent ID 和端口分配偏移


class AICAgent(BaseModel):
    """AIC Agent configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    vm: VmConfig = Field(default_factory=VmConfig)
    
    # Runtime status (not persisted)
    status: str = "stopped"  # stopped, starting, running, error


class AgentsConfig(BaseModel):
    """Root configuration for all agents"""
    version: int = 1
    current_agent_id: Optional[str] = None
    agents: List[AICAgent] = []


# Base values for resource allocation
BASE_PORTS = {
    "vnc": 5900,
    "websocket": 6080,
    "ssh": 2222,
    "mcp": 8081,  # MCP 宿主机端口起始值 (8081, 8082, ...)
}
BASE_VSOCK_CID = 3  # 用于 Agent ID 偏移


class AgentConfigManager:
    """
    Manages AIC Agent configurations.
    
    Storage:
    - Config: ~/.novaic/agents.json
    - VMs: ~/.novaic/vms/{agent-id}/
    """
    
    def __init__(self):
        self._config_dir = Path.home() / ".novaic"
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
        
        # Allocate resources (ports + MCP port + CID offset)
        ports, mcp_host_port, vsock_cid = self._allocate_resources(config)
        
        # Create agent
        agent_id = str(uuid.uuid4())
        agent = AICAgent(
            id=agent_id,
            name=name,
            vm=VmConfig(
                backend=backend,
                os_type=os_type,
                os_version=os_version,
                memory=memory,
                cpus=cpus,
                ports=ports,
                mcp_host_port=mcp_host_port,  # 宿主机 MCP 端口 (8081, 8082, ...)
                mcp_vm_port=8080,  # VM 内部固定端口
                vsock_cid=vsock_cid,
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
    
    def _allocate_resources(self, config: AgentsConfig) -> tuple:
        """
        Allocate unique ports for a new agent
        
        Returns:
            (PortConfig, mcp_host_port, vsock_cid)
        """
        # Collect used offsets (based on VNC port or VSOCK CID)
        used_offsets = set()
        for agent in config.agents:
            # Calculate offset from base
            offset = agent.vm.vsock_cid - BASE_VSOCK_CID
            used_offsets.add(offset)
        
        # Find next available offset
        offset = 0
        while offset in used_offsets:
            offset += 1
        
        ports = PortConfig(
            vnc=BASE_PORTS["vnc"] + offset,
            websocket=BASE_PORTS["websocket"] + offset,
            ssh=BASE_PORTS["ssh"] + offset,
        )
        
        mcp_host_port = BASE_PORTS["mcp"] + offset  # 8081, 8082, 8083...
        vsock_cid = BASE_VSOCK_CID + offset
        
        return ports, mcp_host_port, vsock_cid
    
    def _allocate_ports(self, config: AgentsConfig) -> PortConfig:
        """Allocate unique ports for a new agent (deprecated, use _allocate_resources)"""
        ports, _, _ = self._allocate_resources(config)
        return ports
    
    def get_available_images(self) -> List[Dict[str, Any]]:
        """
        Get list of available VM images.
        
        Returns images from:
        - novaic-vm/images/ (development)
        - ~/.novaic/images/ (user downloaded)
        """
        images = []
        
        # Check novaic-vm/images (development path)
        dev_images_dir = Path.home() / "novaic" / "novaic-vm" / "images"
        if dev_images_dir.exists():
            for img in dev_images_dir.glob("*.qcow2"):
                images.append({
                    "path": str(img),
                    "name": img.stem,
                    "size": img.stat().st_size,
                    "source": "development"
                })
        
        # Check ~/.novaic/images (user images)
        user_images_dir = self._config_dir / "images"
        if user_images_dir.exists():
            for img in user_images_dir.glob("*.qcow2"):
                images.append({
                    "path": str(img),
                    "name": img.stem,
                    "size": img.stat().st_size,
                    "source": "user"
                })
        
        return images


# Global instance
_agent_config_manager: Optional[AgentConfigManager] = None


def get_agent_config_manager() -> AgentConfigManager:
    """Get the global agent config manager instance"""
    global _agent_config_manager
    if _agent_config_manager is None:
        _agent_config_manager = AgentConfigManager()
    return _agent_config_manager
