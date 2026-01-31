"""
MCP Servers - 独立的子 MCP Server 模块

v2.8: 重命名

每个子 MCP Server 都是独立的 FastMCP 实例，可以：
1. 独立暴露 HTTP 端点
2. 被 AggregateMCP 聚合

## 子 MCP Servers

- **RuntimeMCP**: Runtime 管理（runtime_* 工具）
- **LocalMCPServer**: 主机端 Web 搜索和抓取
- **MemoryMCPServer**: 持久化存储和状态管理
- **ChatMCPServer**: Agent-User 通信
- **QemuDebugMCPServer**: QEMU 虚拟机调试工具
"""

from .base import BaseMCPServer
from .runtime import RuntimeMCP
from .local import LocalMCPServer
from .memory import MemoryMCPServer
from .chat import ChatMCPServer
from .qemudebug import QemuDebugMCPServer

# Default MCP Server classes (always enabled)
DEFAULT_SERVERS = [
    RuntimeMCP,
    LocalMCPServer,
    MemoryMCPServer,
    ChatMCPServer,
    QemuDebugMCPServer,
]

# Optional MCP Server classes (enabled via environment)
OPTIONAL_SERVERS = {}

# All MCP Server classes
ALL_SERVERS = DEFAULT_SERVERS + list(OPTIONAL_SERVERS.values())

__all__ = [
    # Base class
    "BaseMCPServer",
    # Server classes
    "RuntimeMCP",
    "LocalMCPServer",
    "MemoryMCPServer",
    "ChatMCPServer",
    "QemuDebugMCPServer",
    # Collections
    "DEFAULT_SERVERS",
    "OPTIONAL_SERVERS",
    "ALL_SERVERS",
]
