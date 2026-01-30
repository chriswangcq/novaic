"""
NovAIC MCP Gateway Module (mcp_gateway)

Provides a unified MCP interface for each Agent, aggregating tools and skills
from all sub-MCP servers (vmuse, session, local, memory, chat, qemudebug).

Note: Named 'mcp_gateway' to avoid conflict with the 'mcp' package from FastMCP.

Architecture:
    Gateway (19999)
    └── /agents/{agent_id}/mcp  → AgentMCPGateway
        ├── Tools: Proxied from sub-servers via ToolRegistry
        ├── Skills: Aggregated from sub-servers
        └── task_*: Async wrapper tools
"""

from .gateway import AgentMCPGateway
from .manager import MCPGatewayManager

__all__ = ["AgentMCPGateway", "MCPGatewayManager"]
