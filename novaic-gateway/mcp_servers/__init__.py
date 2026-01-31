"""
MCP Servers - 独立的子 MCP Server 模块

每个子 MCP Server 都是独立的 FastMCP 实例，可以：
1. 独立暴露 HTTP 端点
2. 被 Gateway 聚合

## 子 MCP Servers

- **SingleAgentRuntimeMCPServer**: 单个 Agent 的运行时管理（context 管理和调度）
- **LocalMCPServer**: 主机端 Web 搜索和抓取
- **MemoryMCPServer**: 持久化存储和状态管理
- **ChatMCPServer**: Agent-User 通信
- **QemuDebugMCPServer**: QEMU 虚拟机调试工具 (可选)
"""

from .base import BaseMCPServer
from .single_agent_runtime import SingleAgentRuntimeMCPServer
from .local import LocalMCPServer
from .memory import MemoryMCPServer
from .chat import ChatMCPServer
from .qemudebug import QemuDebugMCPServer

# Default MCP Server classes (always enabled)
# QemuDebugMCPServer is always enabled as fallback when VM is not ready
DEFAULT_SERVERS = [
    SingleAgentRuntimeMCPServer,
    LocalMCPServer,
    MemoryMCPServer,
    ChatMCPServer,
    QemuDebugMCPServer,  # Fallback for VM tools
]

# Optional MCP Server classes (enabled via environment)
OPTIONAL_SERVERS = {
    # Currently empty - qemudebug moved to DEFAULT_SERVERS
}

# All MCP Server classes
ALL_SERVERS = DEFAULT_SERVERS + list(OPTIONAL_SERVERS.values())

__all__ = [
    # Base class
    "BaseMCPServer",
    # Server classes
    "SingleAgentRuntimeMCPServer",
    "LocalMCPServer",
    "MemoryMCPServer",
    "ChatMCPServer",
    "QemuDebugMCPServer",
    # Collections
    "DEFAULT_SERVERS",
    "OPTIONAL_SERVERS",
    "ALL_SERVERS",
]
