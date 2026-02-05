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


# =============================================================================
# Database-backed Agent Manager (replaces old JSON-based version)
# =============================================================================
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
