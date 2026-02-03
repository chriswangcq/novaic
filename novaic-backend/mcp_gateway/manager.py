"""
MCPManager - MCP Server 管理器

v3.0: 简化架构 - 只管理 AggregateMCP

内部 MCP servers (memory, chat, etc.) 已被移除。
AggregateMCP 直接注册工具调用 Gateway API。
ToolRegistry 只用于发现外部 MCP servers (vmuse)。
"""

import os
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from fastapi import FastAPI

if TYPE_CHECKING:
    from mcp_gateway.gateway import AggregateMCP

logger = logging.getLogger(__name__)


class MCPManager:
    """
    MCP Server 管理器。
    
    v3.0: 简化架构
    - 只管理 AggregateMCP (每个 Runtime 一个)
    - 内部工具由 AggregateMCP 直接注册
    - ToolRegistry 只发现外部 MCP (vmuse)
    """
    
    def __init__(self, app: FastAPI):
        """
        Initialize MCP Manager.
        
        Args:
            app: FastAPI application instance
        """
        self.app = app
        
        # Aggregate gateways: {runtime_id: AggregateMCP}
        self._aggregate_gateways: Dict[str, 'AggregateMCP'] = {}
        self._aggregate_lifespan_contexts: Dict[str, Any] = {}
        
        logger.info("[MCPManager] Initialized (v3.0 - simplified architecture)")
    
    # ========================================
    # Aggregate Gateway Management
    # ========================================
    
    async def create_aggregate_gateway(
        self,
        agent_id: str,
        runtime_id: str,
        subagent_id: str,
        ports: dict,
    ) -> 'AggregateMCP':
        """
        Create an AggregateMCP gateway for a Runtime.
        
        Args:
            agent_id: Agent ID
            runtime_id: Runtime ID (rt-xxx)
            subagent_id: SubAgent ID (main-xxx or sub-xxx)
            ports: Port configuration dict (from Gateway API)
        
        Returns:
            Created AggregateMCP instance
        """
        if runtime_id in self._aggregate_gateways:
            logger.warning(f"[MCPManager] Gateway for {runtime_id} already exists")
            return self._aggregate_gateways[runtime_id]
        
        try:
            from mcp_gateway.gateway import AggregateMCP, PortConfig
            
            port_config = PortConfig(**ports)
            
            gateway = AggregateMCP(
                agent_id=agent_id,
                runtime_id=runtime_id,
                subagent_id=subagent_id,
                ports=port_config,
            )
            
            await gateway.setup()
            
            mcp_app = gateway.get_asgi_app()
            mount_path = f"/mcp/aggregate/{runtime_id}/"
            
            # Initialize lifespan
            lifespan_ctx = await self._init_lifespan(mcp_app, runtime_id)
            if lifespan_ctx:
                self._aggregate_lifespan_contexts[runtime_id] = lifespan_ctx
            
            # Mount to FastAPI
            self.app.mount(mount_path, mcp_app)
            
            # Start external tool discovery
            gateway.start_discovery_task()
            
            self._aggregate_gateways[runtime_id] = gateway
            logger.info(f"[MCPManager] Mounted gateway at {mount_path}")
            
            return gateway
            
        except Exception as e:
            logger.error(f"[MCPManager] Failed to create gateway: {e}")
            raise
    
    async def remove_aggregate_gateway(self, runtime_id: str) -> bool:
        """Remove an AggregateMCP gateway."""
        if runtime_id not in self._aggregate_gateways:
            return False
        
        try:
            gateway = self._aggregate_gateways[runtime_id]
            await gateway.close()
            
            lifespan_ctx = self._aggregate_lifespan_contexts.pop(runtime_id, None)
            if lifespan_ctx:
                try:
                    await lifespan_ctx.__aexit__(None, None, None)
                except Exception as e:
                    logger.error(f"[MCPManager] Error closing lifespan: {e}")
            
            del self._aggregate_gateways[runtime_id]
            logger.info(f"[MCPManager] Removed gateway for {runtime_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MCPManager] Failed to remove gateway: {e}")
            return False
    
    def get_aggregate_gateway(self, runtime_id: str) -> Optional['AggregateMCP']:
        """Get an AggregateMCP gateway by runtime_id."""
        return self._aggregate_gateways.get(runtime_id)
    
    def get_aggregate_mount_path(self, runtime_id: str) -> str:
        """Get the mount path for an aggregate gateway."""
        return f"/mcp/aggregate/{runtime_id}/"
    
    # ========================================
    # Compatibility Methods (deprecated)
    # ========================================
    
    def has_agent_shared_servers(self, agent_id: str) -> bool:
        """Deprecated: Internal MCP servers no longer exist."""
        return True  # Always return True for compatibility
    
    async def create_agent_shared_servers(self, agent_id: str, ports: dict) -> Dict:
        """Deprecated: Internal MCP servers no longer exist."""
        logger.debug(f"[MCPManager] create_agent_shared_servers called (no-op)")
        return {}
    
    async def remove_agent_shared_servers(self, agent_id: str) -> bool:
        """Deprecated: Internal MCP servers no longer exist."""
        return True
    
    async def create_runtime_server(self, agent_id: str, runtime_id: str, subagent_id: str, ports: dict):
        """Deprecated: RuntimeMCP no longer exists as separate server."""
        logger.debug(f"[MCPManager] create_runtime_server called (no-op)")
        return None
    
    async def remove_runtime_server(self, runtime_id: str) -> bool:
        """Deprecated: RuntimeMCP no longer exists as separate server."""
        return True
    
    def get_runtime_mount_path(self, runtime_id: str) -> str:
        """Deprecated: Use get_aggregate_mount_path instead."""
        return self.get_aggregate_mount_path(runtime_id)
    
    # ========================================
    # Utility Methods
    # ========================================
    
    async def _init_lifespan(self, mcp_app, context_id: str) -> Optional[Any]:
        """Initialize MCP app lifespan."""
        if hasattr(mcp_app, 'lifespan') and mcp_app.lifespan is not None:
            try:
                lifespan_ctx = mcp_app.lifespan(mcp_app)
                await lifespan_ctx.__aenter__()
                return lifespan_ctx
            except Exception as e:
                logger.warning(f"[MCPManager] Lifespan init failed: {e}")
        return None
    
    async def close_all(self) -> None:
        """Close all gateways."""
        for runtime_id in list(self._aggregate_gateways.keys()):
            await self.remove_aggregate_gateway(runtime_id)
        logger.info("[MCPManager] Closed all gateways")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        stats = {
            "aggregate_gateways": list(self._aggregate_gateways.keys()),
            "total_gateways": len(self._aggregate_gateways),
        }
        
        # Add per-gateway stats
        for runtime_id, gateway in self._aggregate_gateways.items():
            stats[f"gateway_{runtime_id}"] = gateway.get_stats()
        
        return stats


# Global instance
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> Optional[MCPManager]:
    """Get the global MCPManager instance."""
    return _mcp_manager


def set_mcp_manager(manager: MCPManager) -> None:
    """Set the global MCPManager instance."""
    global _mcp_manager
    _mcp_manager = manager
