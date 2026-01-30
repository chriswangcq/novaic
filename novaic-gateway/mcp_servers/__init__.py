"""
MCP Servers - 独立的子 MCP Server 模块

每个子 MCP Server 都是独立的 FastMCP 实例，可以：
1. 独立暴露 HTTP 端点
2. 被 Gateway 聚合

## 子 MCP Servers

- **AgentContextMCPServer**: Agent 上下文管理和自我调度
- **LocalMCPServer**: 主机端 Web 搜索和抓取
- **MemoryMCPServer**: 持久化存储和状态管理
- **ChatMCPServer**: Agent-User 通信
"""

from .base import BaseMCPServer
from .agent_context import AgentContextMCPServer
from .local import LocalMCPServer
from .memory import MemoryMCPServer, init_memory_dir
from .chat import ChatMCPServer

# All MCP Server classes
ALL_SERVERS = [
    AgentContextMCPServer,
    LocalMCPServer,
    MemoryMCPServer,
    ChatMCPServer,
]

__all__ = [
    # Base class
    "BaseMCPServer",
    # Server classes
    "AgentContextMCPServer",
    "LocalMCPServer",
    "MemoryMCPServer",
    "ChatMCPServer",
    # Utils
    "init_memory_dir",
    # Collection
    "ALL_SERVERS",
]
