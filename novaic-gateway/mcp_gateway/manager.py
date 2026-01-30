"""
MCPGatewayManager - Manages MCP Gateways for all Agents

Handles dynamic creation and mounting of MCP gateways for each agent.
Each agent gets its own MCP endpoint at /agents/{agent_id}/mcp.

Architecture:
    Gateway (FastAPI app at 19999)
    └── MCPGatewayManager
        ├── /agents/{agent0_id}/mcp → AgentMCPGateway(0)
        ├── /agents/{agent1_id}/mcp → AgentMCPGateway(1)
        └── ...
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .gateway import AgentMCPGateway

logger = logging.getLogger(__name__)


class MCPGatewayManager:
    """
    Manager for all Agent MCP Gateways.
    
    Provides dynamic creation and mounting of MCP gateways for each agent.
    Supports adding and removing agents at runtime.
    """
    
    def __init__(self, app: FastAPI):
        """
        Initialize the gateway manager.
        
        Args:
            app: The main FastAPI application to mount gateways on
        """
        self.app = app
        self.gateways: Dict[str, AgentMCPGateway] = {}
        self._mounted_paths: Dict[str, str] = {}  # agent_id -> mount_path
        self._lifespan_contexts: Dict[str, Any] = {}  # agent_id -> lifespan context
        
        logger.info("[MCPGatewayManager] Initialized")
    
    async def add_agent(
        self,
        agent_id: str,
        agent_index: int,
    ) -> bool:
        """
        Create and mount an MCP Gateway for an agent.
        
        Args:
            agent_id: Unique agent identifier
            agent_index: Agent index for port allocation
        
        Returns:
            True if successfully added, False otherwise
        """
        if agent_id in self.gateways:
            logger.warning(f"[MCPGatewayManager] Agent {agent_id} already has a gateway")
            return False
        
        try:
            # Create gateway
            gateway = AgentMCPGateway(
                agent_id=agent_id,
                agent_index=agent_index,
            )
            
            # Setup (discover tools and skills)
            await gateway.setup()
            
            # Get ASGI app and mount
            mcp_app = gateway.get_asgi_app()
            mount_path = f"/agents/{agent_id}/mcp"
            
            # Initialize FastMCP's lifespan (required for http_app to work)
            # This starts the internal task group needed for SSE/HTTP transport
            if hasattr(mcp_app, 'lifespan_handler') and mcp_app.lifespan_handler:
                try:
                    lifespan_ctx = mcp_app.lifespan_handler(mcp_app)
                    await lifespan_ctx.__aenter__()
                    self._lifespan_contexts[agent_id] = lifespan_ctx
                    logger.info(f"[MCPGatewayManager] Initialized lifespan for agent {agent_id}")
                except Exception as e:
                    logger.warning(f"[MCPGatewayManager] Could not init lifespan for {agent_id}: {e}")
            
            # Mount the MCP app
            self.app.mount(mount_path, mcp_app)
            
            # Track
            self.gateways[agent_id] = gateway
            self._mounted_paths[agent_id] = mount_path
            
            logger.info(f"[MCPGatewayManager] Mounted MCP Gateway at {mount_path}")
            return True
            
        except Exception as e:
            logger.error(f"[MCPGatewayManager] Failed to add agent {agent_id}: {e}")
            return False
    
    async def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent's MCP Gateway.
        
        Note: FastAPI doesn't directly support unmounting routes.
        The gateway is removed from tracking but the route may persist
        until the application is restarted.
        
        Args:
            agent_id: Agent identifier to remove
        
        Returns:
            True if found and removed, False otherwise
        """
        if agent_id not in self.gateways:
            logger.warning(f"[MCPGatewayManager] Agent {agent_id} not found")
            return False
        
        try:
            # Close the gateway
            gateway = self.gateways[agent_id]
            await gateway.close()
            
            # Remove from tracking
            del self.gateways[agent_id]
            mount_path = self._mounted_paths.pop(agent_id, None)
            
            # Note: FastAPI doesn't support unmounting, but we can mark it as removed
            # The route will return 404 after gateway is closed
            
            logger.info(f"[MCPGatewayManager] Removed gateway for agent {agent_id} (was at {mount_path})")
            return True
            
        except Exception as e:
            logger.error(f"[MCPGatewayManager] Failed to remove agent {agent_id}: {e}")
            return False
    
    def get_gateway(self, agent_id: str) -> Optional[AgentMCPGateway]:
        """Get a gateway by agent ID."""
        return self.gateways.get(agent_id)
    
    def get_mount_path(self, agent_id: str) -> Optional[str]:
        """Get the mount path for an agent's MCP Gateway."""
        return self._mounted_paths.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all mounted agent gateways."""
        return [
            {
                "agent_id": agent_id,
                "mount_path": self._mounted_paths.get(agent_id),
                "stats": gateway.get_stats(),
            }
            for agent_id, gateway in self.gateways.items()
        ]
    
    async def setup_existing_agents(self) -> int:
        """
        Setup MCP Gateways for all existing agents.
        
        This should be called during application startup.
        
        Returns:
            Number of agents successfully setup
        """
        try:
            from config.agents import get_agent_config_manager
            agent_mgr = get_agent_config_manager()
            agents = agent_mgr.list_agents()
            
            count = 0
            for agent in agents:
                success = await self.add_agent(
                    agent_id=agent.id,
                    agent_index=agent.vm.agent_index,
                )
                if success:
                    count += 1
            
            logger.info(f"[MCPGatewayManager] Setup {count}/{len(agents)} existing agents")
            return count
            
        except Exception as e:
            logger.error(f"[MCPGatewayManager] Failed to setup existing agents: {e}")
            return 0
    
    async def refresh_agent(self, agent_id: str) -> bool:
        """
        Refresh an agent's gateway (re-discover tools and skills).
        
        Args:
            agent_id: Agent identifier to refresh
        
        Returns:
            True if refreshed successfully
        """
        gateway = self.gateways.get(agent_id)
        if not gateway:
            logger.warning(f"[MCPGatewayManager] Agent {agent_id} not found for refresh")
            return False
        
        try:
            # Re-run setup to discover new tools/skills
            await gateway.setup()
            logger.info(f"[MCPGatewayManager] Refreshed gateway for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MCPGatewayManager] Failed to refresh agent {agent_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "total_gateways": len(self.gateways),
            "agents": list(self.gateways.keys()),
            "mount_paths": dict(self._mounted_paths),
        }
    
    async def close_all(self) -> None:
        """Close all gateways."""
        # Close lifespan contexts first
        for agent_id, ctx in list(self._lifespan_contexts.items()):
            try:
                await ctx.__aexit__(None, None, None)
                logger.info(f"[MCPGatewayManager] Closed lifespan for agent {agent_id}")
            except Exception as e:
                logger.error(f"[MCPGatewayManager] Error closing lifespan {agent_id}: {e}")
        self._lifespan_contexts.clear()
        
        # Then close gateways
        for agent_id, gateway in list(self.gateways.items()):
            try:
                await gateway.close()
            except Exception as e:
                logger.error(f"[MCPGatewayManager] Error closing gateway {agent_id}: {e}")
        
        self.gateways.clear()
        self._mounted_paths.clear()
        logger.info("[MCPGatewayManager] Closed all gateways")


# Global instance (set by main.py)
_mcp_gateway_manager: Optional[MCPGatewayManager] = None


def get_mcp_gateway_manager() -> Optional[MCPGatewayManager]:
    """Get the global MCPGatewayManager instance."""
    return _mcp_gateway_manager


def set_mcp_gateway_manager(manager: MCPGatewayManager) -> None:
    """Set the global MCPGatewayManager instance."""
    global _mcp_gateway_manager
    _mcp_gateway_manager = manager
