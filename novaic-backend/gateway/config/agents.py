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
    Port configuration for an agent - SSH and VMUSE HTTP.
    
    Each agent gets 2 ports starting from BASE_PORT + agent_index * 2.
    SSH is used for VM deployment and debugging.
    VMUSE is the HTTP API for VM tools (desktop, browser, shell, etc).
    """
    ssh: int = 20000   # SSH port for VM access
    vmuse: int = 18080  # VMUSE HTTP API port (VM:8080 -> Host:18000+)


class VmConfig(BaseModel):
    """VM configuration for an agent"""
    backend: str = "qemu"  # qemu | virtualization_framework
    image_path: str = ""   # Path to qcow2 image
    os_type: str = "ubuntu"  # ubuntu, debian, etc.
    os_version: str = "24.04"  # 24.04, 22.04, etc.
    memory: str = "4096"   # Memory in MB
    cpus: int = 4          # CPU cores
    ports: PortConfig = Field(default_factory=PortConfig)


class AICAgent(BaseModel):
    """AIC Agent configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    vm: VmConfig = Field(default_factory=VmConfig)
    
    # Setup complete flag (persisted)
    # False = needs setup (download image, create VM)
    # True = VM is ready to start
    setup_complete: bool = False


class AgentsConfig(BaseModel):
    """Root configuration for all agents"""
    version: int = 1
    agents: List[AICAgent] = []


# Centralized port allocation configuration
# Port layout:
#   19999       - Gateway (固定)
#   20000-20199 - Agents (100个 × 2端口 for SSH + VMUSE)
#   18000-18099 - VMUSE HTTP ports (separate range to avoid conflicts)
GATEWAY_PORT = 19999        # Gateway 固定端口
BASE_PORT = 20000           # Agent SSH 基础端口号
BASE_VMUSE_PORT = 18000     # Agent VMUSE 基础端口号
PORTS_PER_AGENT = 2         # 每个Agent分配的端口数量 (SSH + VMUSE)
MAX_AGENTS = 100            # 最大支持的Agent数量

# 服务端口偏移量 (相对于Agent基础端口)
SERVICE_OFFSETS = {
    "ssh": 0,          # SSH port
    "vmuse": 0,        # VMUSE port (uses separate BASE_VMUSE_PORT)
}


def get_agent_port(agent_index: int, service: str) -> int:
    """
    Calculate the port for a specific service of an agent.
    
    NOTE: This function is for internal use during agent creation only.
    Runtime code should use the port configuration stored in the database.
    
    Args:
        agent_index: Agent index (0, 1, 2, ...)
        service: Service name ("ssh" or "vmuse")
    
    Returns:
        Port number
        
    Example:
        Agent 0: ssh=20000, vmuse=18000
        Agent 1: ssh=20001, vmuse=18001
    """
    if service not in SERVICE_OFFSETS:
        raise ValueError(f"Unknown service: {service}. Valid services: {list(SERVICE_OFFSETS.keys())}")
    if agent_index < 0 or agent_index >= MAX_AGENTS:
        raise ValueError(f"Agent index must be between 0 and {MAX_AGENTS - 1}")
    
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
    
    Args:
        agent_index: Agent index (0, 1, 2, ...)
    
    Returns:
        PortConfig with SSH and VMUSE ports assigned
    """
    return PortConfig(
        ssh=get_agent_port(agent_index, "ssh"),
        vmuse=get_agent_port(agent_index, "vmuse")
    )


# =============================================================================
# Database-backed Agent Manager (replaces old JSON-based version)
# =============================================================================
from .agents_db import (
    AgentConfigManager,
    AgentConfigManagerDB,
    get_agent_config_manager,
    get_agent_config_manager_db,
)

# Public exports
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
