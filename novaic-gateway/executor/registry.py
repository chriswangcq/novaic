"""
ToolRegistry - Unified tool registry aggregating multiple MCP servers

Provides a single interface for tool discovery and execution across
multiple MCP servers (VM, session, local, qemu).
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import asyncio

from .mcp_client import MCPClient, MCPServerConnection

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    url: str
    port: Optional[int] = None
    enabled: bool = True
    priority: int = 0  # Lower = higher priority for tool name conflicts


class ToolRegistry:
    """
    Unified tool registry that aggregates tools from multiple MCP servers.
    
    Features:
    - Discovers tools from all registered MCP servers
    - Routes tool calls to the correct server
    - Handles server health and reconnection
    - Provides unified tool listing for LLM
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._servers: Dict[str, MCPServerConfig] = {}
        self._clients: Dict[str, MCPClient] = {}
        
        # Tool -> server mapping
        self._tool_server_map: Dict[str, str] = {}
        
        # Cached tools in LLM format
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        
        # Statistics
        self._stats = {
            "tools_discovered": 0,
            "tools_called": 0,
            "tools_failed": 0,
        }
    
    def register_server(
        self,
        name: str,
        url: Optional[str] = None,
        port: Optional[int] = None,
        enabled: bool = True,
        priority: int = 0,
    ) -> None:
        """
        Register an MCP server.
        
        Args:
            name: Server name (e.g., "vm", "session", "local", "qemu")
            url: Full URL to the MCP server (e.g., "http://127.0.0.1:8080/mcp")
            port: Port number (will construct URL as http://127.0.0.1:{port}/mcp)
            enabled: Whether to enable this server
            priority: Priority for tool name conflicts (lower = higher priority)
        """
        if url is None and port is not None:
            url = f"http://127.0.0.1:{port}/mcp"
        elif url is None:
            raise ValueError("Either url or port must be provided")
        
        config = MCPServerConfig(
            name=name,
            url=url,
            port=port,
            enabled=enabled,
            priority=priority,
        )
        self._servers[name] = config
        
        # Create MCP client for this server
        client = MCPClient()
        self._clients[name] = client
        
        # Clear cache to trigger rediscovery
        self._tools_cache = None
        self._tool_server_map.clear()
        
        logger.info(f"[ToolRegistry] Registered server: {name} at {url}")
    
    def unregister_server(self, name: str) -> bool:
        """
        Unregister an MCP server.
        
        Returns:
            True if server was found and removed
        """
        if name not in self._servers:
            return False
        
        del self._servers[name]
        if name in self._clients:
            del self._clients[name]
        
        # Clear cache
        self._tools_cache = None
        self._tool_server_map = {
            k: v for k, v in self._tool_server_map.items() if v != name
        }
        
        logger.info(f"[ToolRegistry] Unregistered server: {name}")
        return True
    
    async def discover_all_tools(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Discover tools from all registered servers.
        
        Args:
            use_cache: Use cached tools if available
        
        Returns:
            List of tools in raw MCP format
        """
        if use_cache and self._tools_cache is not None:
            return self._tools_cache
        
        all_tools = []
        self._tool_server_map.clear()
        
        # Sort servers by priority
        sorted_servers = sorted(
            self._servers.items(),
            key=lambda x: x[1].priority
        )
        
        for server_name, config in sorted_servers:
            if not config.enabled:
                continue
            
            client = self._clients.get(server_name)
            if not client:
                continue
            
            try:
                # Register the server if not already done
                if config.port:
                    await client.register_server(name=server_name, port=config.port)
                
                # Discover tools
                tools = await client.list_all_tools(use_cache=False)
                
                for tool in tools:
                    tool_name = tool.get("name", "")
                    
                    # Check for conflicts
                    if tool_name in self._tool_server_map:
                        existing_server = self._tool_server_map[tool_name]
                        logger.warning(
                            f"[ToolRegistry] Tool '{tool_name}' from {server_name} "
                            f"conflicts with {existing_server}, using {existing_server}"
                        )
                        continue
                    
                    # Add server info to tool
                    tool["_server"] = server_name
                    all_tools.append(tool)
                    self._tool_server_map[tool_name] = server_name
                
                logger.info(f"[ToolRegistry] Discovered {len(tools)} tools from {server_name}")
                
            except Exception as e:
                logger.error(f"[ToolRegistry] Failed to discover tools from {server_name}: {e}")
        
        self._tools_cache = all_tools
        self._stats["tools_discovered"] = len(all_tools)
        
        return all_tools
    
    def to_llm_tools_format(self, tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Convert tools to LLM-compatible format.
        
        Args:
            tools: Tools to convert (uses cache if None)
        
        Returns:
            Tools in OpenAI function calling format
        """
        if tools is None:
            tools = self._tools_cache or []
        
        result = []
        for tool in tools:
            input_schema = tool.get("inputSchema", {"type": "object", "properties": {}})
            
            result.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": input_schema,
                }
            })
        
        return result
    
    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        self._stats["tools_called"] += 1
        
        # Find the server for this tool
        server_name = self._tool_server_map.get(tool_name)
        
        if server_name is None:
            # Try rediscovering tools
            await self.discover_all_tools(use_cache=False)
            server_name = self._tool_server_map.get(tool_name)
        
        if server_name is None:
            self._stats["tools_failed"] += 1
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in any registered server"
            }
        
        client = self._clients.get(server_name)
        if not client:
            self._stats["tools_failed"] += 1
            return {
                "success": False,
                "error": f"Server '{server_name}' not available"
            }
        
        try:
            result = await client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            self._stats["tools_failed"] += 1
            logger.error(f"[ToolRegistry] Tool execution failed: {tool_name} - {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools in LLM format.
        
        Returns:
            List of tools ready for LLM consumption
        """
        await self.discover_all_tools()
        return self.to_llm_tools_format()
    
    def get_tool_server(self, tool_name: str) -> Optional[str]:
        """Get the server name for a tool."""
        return self._tool_server_map.get(tool_name)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all registered servers.
        
        Returns:
            Health status for each server
        """
        results = {}
        
        for server_name, config in self._servers.items():
            if not config.enabled:
                results[server_name] = {"status": "disabled"}
                continue
            
            client = self._clients.get(server_name)
            if not client:
                results[server_name] = {"status": "no_client"}
                continue
            
            try:
                health = await client.health_check()
                results[server_name] = {
                    "status": "healthy" if any(health.values()) else "unhealthy",
                    "details": health,
                }
            except Exception as e:
                results[server_name] = {
                    "status": "error",
                    "error": str(e),
                }
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            **self._stats,
            "registered_servers": len(self._servers),
            "enabled_servers": sum(1 for c in self._servers.values() if c.enabled),
            "tool_count": len(self._tool_server_map),
            "tools_by_server": {
                server: sum(1 for s in self._tool_server_map.values() if s == server)
                for server in self._servers
            }
        }
    
    async def close(self) -> None:
        """Close all client connections."""
        for client in self._clients.values():
            try:
                await client.close()
            except Exception:
                pass
        
        self._clients.clear()
        self._tools_cache = None
        self._tool_server_map.clear()
