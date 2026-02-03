"""
MCP API (via Gateway proxy)

All MCP management operations go through Gateway.
Services do NOT call MCP Gateway directly.
"""

from typing import Optional, Dict, Any
from .base import BaseAPI


class McpAPI(BaseAPI):
    """
    MCP operations via Gateway proxy.
    
    All MCP management goes through Gateway API, which proxies to MCP Gateway.
    Services should NOT communicate with MCP Gateway directly.
    
    Usage:
        await sdk.mcp.create_agent_shared(agent_id)
        await sdk.mcp.create_runtime(agent_id, runtime_id)
        mcp_url = await sdk.mcp.create_aggregate(agent_id, runtime_id)
    """
    
    async def has_agent_shared(self, agent_id: str) -> bool:
        """Check if agent has shared MCP server."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/mcp/agent-shared/{agent_id}/exists"
        )
        return data.get("exists", False)
    
    async def create_agent_shared(
        self, 
        agent_id: str, 
        agent_index: int = 0
    ):
        """
        Create agent shared MCP server.
        
        This creates MCP tools shared across all runtimes for an agent.
        """
        await self._http.post(
            f"{self.gateway_url}/internal/mcp/agent-shared",
            json={"agent_id": agent_id, "agent_index": agent_index}
        )
    
    async def delete_agent_shared(self, agent_id: str):
        """Delete agent shared MCP server."""
        await self._http.delete(
            f"{self.gateway_url}/internal/mcp/agent-shared/{agent_id}"
        )
    
    async def create_runtime(
        self,
        agent_id: str,
        runtime_id: str,
        subagent_id: str,
        agent_index: int = 0
    ):
        """
        Create runtime-specific MCP server.
        
        This creates MCP tools specific to a runtime.
        
        Args:
            agent_id: Agent ID
            runtime_id: Runtime ID (rt-xxx)
            subagent_id: SubAgent ID (main-xxx or sub-xxx) for context
            agent_index: Agent index for port allocation
        """
        await self._http.post(
            f"{self.gateway_url}/internal/mcp/runtime",
            json={
                "agent_id": agent_id,
                "runtime_id": runtime_id,
                "subagent_id": subagent_id,
                "agent_index": agent_index,
            }
        )
    
    async def delete_runtime(self, agent_id: str, runtime_id: str):
        """Delete runtime MCP server."""
        await self._http.delete(
            f"{self.gateway_url}/internal/mcp/runtime/{agent_id}/{runtime_id}"
        )
    
    async def create_aggregate(
        self,
        agent_id: str,
        runtime_id: str,
        subagent_id: str,
        agent_index: int = 0
    ) -> str:
        """
        Create aggregate MCP server.
        
        This creates a combined MCP that aggregates:
        - Agent shared MCP
        - Runtime MCP
        - User-configured external MCPs
        
        Args:
            agent_id: Agent ID
            runtime_id: Runtime ID (rt-xxx)
            subagent_id: SubAgent ID (main-xxx or sub-xxx)
            agent_index: Agent index for port allocation
        
        Returns:
            MCP URL for this aggregate
        """
        data = await self._http.post(
            f"{self.gateway_url}/internal/mcp/aggregate",
            json={
                "agent_id": agent_id,
                "runtime_id": runtime_id,
                "subagent_id": subagent_id,
                "agent_index": agent_index,
            }
        )
        return data.get("mcp_url", "")
    
    async def delete_aggregate(self, agent_id: str, runtime_id: str):
        """Delete aggregate MCP server."""
        await self._http.delete(
            f"{self.gateway_url}/internal/mcp/aggregate/{agent_id}/{runtime_id}"
        )
    
    async def list_servers(self) -> Dict[str, Any]:
        """List all active MCP servers."""
        return await self._http.get(
            f"{self.gateway_url}/internal/mcp/servers"
        )
