"""
MCP Client Module - 外部 MCP 服务连接

本模块提供连接外部 MCP 服务（如 vmuse）的客户端功能。
内置工具已迁移到 tools_server 模块。

主要组件：
- MCPServerConnection: 连接单个 MCP 服务器
- MCPClient: MCP 客户端
- ToolRegistry: 外部 MCP 服务发现和注册

NOTE: 原 MCP Gateway (FastMCP) 已废弃，由 Tools Server 替代。
"""

from .mcp_client import MCPServerConnection, MCPClient
from .registry import ToolRegistry

__all__ = [
    "MCPServerConnection",
    "MCPClient", 
    "ToolRegistry",
]
