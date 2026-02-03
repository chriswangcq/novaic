"""
NovAIC MCP Gateway Module (mcp_gateway)

v3.0: 简化架构

提供统一 MCP 接口：
- AggregateMCP: 直接注册工具调用 Gateway API
- MCPManager: 管理 AggregateMCP 生命周期
- ToolRegistry: 只用于发现外部 MCP (vmuse)

Architecture:
    MCP Gateway (19998)
    └── /mcp/aggregate/{runtime_id}  → AggregateMCP
        ├── 内置工具: memory_*, runtime_*, chat_*, web_*, qemu_*, task_*
        ├── 外部工具: vmuse (通过 ToolRegistry 发现)
        └── Skills: MCP Resources
"""

from .gateway import AggregateMCP, PortConfig
from .registry import ToolRegistry
from .manager import MCPManager, get_mcp_manager, set_mcp_manager

__all__ = [
    "AggregateMCP",
    "PortConfig",
    "ToolRegistry",
    "MCPManager",
    "get_mcp_manager",
    "set_mcp_manager",
]
