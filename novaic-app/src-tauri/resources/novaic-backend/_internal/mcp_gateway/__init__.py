"""
NovAIC MCP Gateway Module (mcp_gateway)

v2.8: Per-Runtime Aggregate MCP

Provides a unified MCP interface for each Runtime, aggregating tools from:
- RuntimeMCP (runtime_* tools)
- Shared MCP servers (chat, memory, local, qemudebug)
- VM MCP

Note: Named 'mcp_gateway' to avoid conflict with the 'mcp' package from FastMCP.

Architecture:
    Gateway (19999)
    └── /mcp/aggregate/{subagent_id}  → AggregateMCP
        ├── Tools: Proxied from sub-servers via ToolRegistry
        ├── Skills: Aggregated from skills directory
        └── task_*: Async wrapper tools
"""

from .gateway import AggregateMCP

__all__ = ["AggregateMCP"]
