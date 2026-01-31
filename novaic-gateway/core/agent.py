"""
NovAIC Gateway - Core Agent Implementation

v12: Simplified - Only provides tool discovery and basic utilities.
The ReACT loop is now driven by Master, not this class.

For the full architecture, see: docs/ARCHITECTURE-V2-MULTIPROCESS.md
"""

from typing import Dict, Any, List, Optional
import asyncio

from .session import SessionManager
from .mcp_client import MCPClient, MCPSkill
from executor.registry import ToolRegistry


class NovAICAgent:
    """
    Agent class for tool discovery and environment info.
    
    v12: Simplified from full ReACT agent to just utility functions.
    - Tool discovery from MCP servers
    - Environment health checks
    - Basic session management
    
    The actual ReACT loop is now handled by:
    - Master: Drives the loop, manages Runtimes
    - Worker: Executes think/tool_call tasks
    """
    
    def __init__(self, mcp_port: int, tool_registry: Optional[ToolRegistry] = None, session_key: str = "main"):
        """
        Initialize the Agent.
        
        Args:
            mcp_port: MCP Server port
            tool_registry: Optional unified tool registry (aggregates multiple MCP servers)
            session_key: Session identifier (default: "main")
        """
        self.mcp_port = mcp_port
        self.session_key = session_key
        
        # ToolRegistry for unified tool access (if provided)
        self.tool_registry = tool_registry
        
        # Initialize components
        self.session = SessionManager()
        self.mcp_client = MCPClient()  # Fallback direct client
        
        # Tools list (dynamically loaded from MCP)
        self.tools: List[Dict[str, Any]] = []
        self._tools_initialized = False
        
        # Skills (dynamically loaded from MCP Resources)
        self.skills: Dict[str, MCPSkill] = {}
        self._skills_initialized = False
        
        # Environment state
        self._executor_healthy = None
        
        # Control flags
        self._interrupted = False
    
    async def initialize(self) -> None:
        """
        Initialize Agent: discover tools and skills from MCP Server(s).
        
        If tool_registry is provided, uses unified registry for multiple MCP servers.
        Otherwise falls back to direct MCPClient for single server.
        """
        from .mcp_client import get_mcp_url
        
        if self._tools_initialized and len(self.tools) > 0:
            print(f"[Agent] Already initialized with {len(self.tools)} tools")
            return
        
        print(f"[Agent] ========== MCP Initialize Start ==========")
        
        try:
            if self.tool_registry:
                # Use unified ToolRegistry (multiple MCP servers)
                print(f"[Agent] Using ToolRegistry (unified mode)")
                
                # Discover tools from all registered servers
                print(f"[Agent] Discovering tools from registry...")
                raw_tools = await self.tool_registry.discover_all_tools(use_cache=False)
                print(f"[Agent] Raw tools discovered: {len(raw_tools)}")
                
                # Convert to LLM format
                self.tools = self.tool_registry.to_llm_tools_format(raw_tools)
                print(f"[Agent] LLM-formatted tools: {len(self.tools)}")
                
                # Get registry stats
                stats = self.tool_registry.get_stats()
                print(f"[Agent] Tools by server: {stats.get('tools_by_server', {})}")
                
                # Also initialize direct MCPClient for skills (skills from primary VM server)
                mcp_url = get_mcp_url(self.mcp_port)
                print(f"[Agent] Registering primary MCP server for skills at port {self.mcp_port}...")
                await self.mcp_client.register_server(name="executor", port=self.mcp_port)
                
            else:
                # Direct MCPClient mode (single server)
                mcp_url = get_mcp_url(self.mcp_port)
                print(f"[Agent] Using direct MCPClient mode")
                print(f"[Agent] MCP URL: {mcp_url}")
                
                # Register MCP Server
                print(f"[Agent] Registering MCP server 'executor' at port {self.mcp_port}...")
                await self.mcp_client.register_server(name="executor", port=self.mcp_port)
                
                # Discover Tools
                print(f"[Agent] Discovering tools...")
                tools = await self.mcp_client.list_all_tools()
                print(f"[Agent] Raw tools discovered: {len(tools)}")
                
                self.tools = self.mcp_client.to_llm_tools_format(tools)
                print(f"[Agent] LLM-formatted tools: {len(self.tools)}")
            
            if self.tools:
                tool_names = [t.get('function', {}).get('name', 'unknown') for t in self.tools[:10]]
                print(f"[Agent] First 10 tools: {tool_names}")
            
            # Discover Skills
            print(f"[Agent] Discovering skills...")
            await self._discover_skills()
            
            if len(self.tools) > 0:
                self._executor_healthy = True
                self._tools_initialized = True
                print(f"[Agent] ✓ Initialized successfully: {len(self.tools)} tools, {len(self.skills)} skills")
            else:
                self._executor_healthy = False
                print(f"[Agent] ✗ MCP Server connected but NO TOOLS discovered!")
                
        except Exception as e:
            import traceback
            print(f"[Agent] ✗ Failed to initialize MCP connection: {e}")
            print(f"[Agent] Traceback:\n{traceback.format_exc()}")
            self._executor_healthy = False
            self.tools = []
        
        print(f"[Agent] ========== MCP Initialize End ==========")
    
    async def _discover_skills(self) -> None:
        """Discover and cache all available Skills."""
        try:
            skills = await self.mcp_client.discover_all_skills()
            self.skills = {skill.uri: skill for skill in skills}
            self._skills_initialized = True
            print(f"[Agent] Discovered skills: {[s.name for s in skills]}")
        except Exception as e:
            print(f"[Agent] Failed to discover skills: {e}")
            self.skills = {}
    
    async def check_executor_health(self) -> Dict[str, Any]:
        """Check Executor (MCP Server) health status."""
        if self._tools_initialized and len(self.tools) > 0:
            self._executor_healthy = True
            return {"healthy": True, "tools_count": len(self.tools)}
        
        try:
            await self.initialize()
            if len(self.tools) > 0:
                self._executor_healthy = True
                return {"healthy": True, "tools_count": len(self.tools)}
        except Exception as e:
            print(f"[Agent] MCP connection failed: {e}")
        
        self._executor_healthy = False
        return {"healthy": False, "error": "MCP Server not available"}
    
    async def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment info."""
        from .mcp_client import get_mcp_url
        import os
        
        # New architecture: use Gateway URL
        if self.tool_registry is not None:
            gateway_port = int(os.getenv("NOVAIC_PORT", "19999"))
            return {
                "mcp_port": gateway_port,
                "mcp_url": f"http://127.0.0.1:{gateway_port}/mcp",
                "executor_healthy": len(self.tools) > 0,
                "tools_count": len(self.tools),
                "skills_count": len(self.skills),
                "skills": [s.name for s in self.skills.values()],
            }
        
        # Legacy: direct VM connection
        return {
            "mcp_port": self.mcp_port,
            "mcp_url": get_mcp_url(self.mcp_port),
            "executor_healthy": self._executor_healthy,
            "tools_count": len(self.tools),
            "skills_count": len(self.skills),
            "skills": [s.name for s in self.skills.values()],
        }
    
    def interrupt(self) -> None:
        """Set interrupt flag."""
        self._interrupted = True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get session messages (v12: use chat_messages table instead)."""
        return self.session.get_all_messages()
    
    def clear_messages(self) -> None:
        """Clear session messages."""
        self.session.clear()
    
    async def close(self) -> None:
        """Clean up resources."""
        if self.mcp_client:
            await self.mcp_client.close()
