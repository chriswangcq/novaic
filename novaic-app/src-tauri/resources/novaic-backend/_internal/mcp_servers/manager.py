"""
MCPManager - MCP Server 管理器

v2.9: MCP Server 架构

1. 共享层 (qemu, memory, chat, local): 每个 Agent 独立，数据隔离
2. Runtime 层 (RuntimeMCP): 每个 Runtime 独立，runtime_* 工具
3. 聚合层 (AggregateMCP): 每个 Runtime 一个，聚合 Runtime + 共享层 + VM
"""

import os
import logging
from typing import Dict, List, Any, Optional, Type, TYPE_CHECKING

from fastapi import FastAPI

from .base import BaseMCPServer
from .runtime import RuntimeMCP
from .local import LocalMCPServer
from .memory import MemoryMCPServer
from .chat import ChatMCPServer
from .qemudebug import QemuDebugMCPServer

if TYPE_CHECKING:
    from mcp_gateway.gateway import AggregateMCP

logger = logging.getLogger(__name__)


class MCPManager:
    """
    MCP Server 管理器。
    
    v2.9: 架构
    
    负责：
    1. 共享层: 每个 Agent 独立的 qemu, memory, chat, local（Agent 数据隔离）
    2. Runtime 层: 动态创建/销毁 RuntimeMCP 实例（runtime_* 工具）
    3. 聚合层: 每个 Runtime 一个 AggregateMCP，聚合所有工具
    """
    
    # 共享层 MCP Server 类
    SHARED_SERVERS: List[Type[BaseMCPServer]] = [
        LocalMCPServer,
        MemoryMCPServer,
        ChatMCPServer,
        QemuDebugMCPServer,  # Fallback for VM tools
    ]
    
    def __init__(self, app: FastAPI):
        """
        初始化子 MCP 管理器。
        
        Args:
            app: FastAPI 应用实例
        """
        self.app = app
        
        # v2.9: 共享层 per-agent: {agent_id: {server_name: server_instance}}
        self._agent_shared_servers: Dict[str, Dict[str, BaseMCPServer]] = {}
        self._agent_shared_lifespan_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Runtime 层 servers: {subagent_id: server_instance}
        self._runtime_servers: Dict[str, RuntimeMCP] = {}
        self._runtime_lifespan_contexts: Dict[str, Any] = {}
        
        # v2.7: 聚合层 gateways: {subagent_id: AggregateMCP}
        self._aggregate_gateways: Dict[str, 'AggregateMCP'] = {}
        self._aggregate_lifespan_contexts: Dict[str, Any] = {}
        
        logger.info("[MCPManager] Initialized (v2.9 architecture - per-agent shared layer)")
    
    # ========================================
    # 共享层管理 (v2.9: 每个 Agent 独立)
    # ========================================
    
    async def create_agent_shared_servers(
        self, 
        agent_id: str, 
        agent_index: int = 0,
    ) -> Dict[str, BaseMCPServer]:
        """
        为一个 Agent 创建共享层 MCP servers。
        
        v2.9: 每个 Agent 有独立的共享层实例，数据隔离。
        路径: /agents/{agent_id}/mcp/{server_name}
        
        Args:
            agent_id: Agent ID
            agent_index: Agent index for port allocation
        
        Returns:
            字典 {server_name: server_instance}
        """
        if agent_id in self._agent_shared_servers:
            logger.info(f"[MCPManager] Shared servers for agent {agent_id} already exist")
            return self._agent_shared_servers[agent_id]
        
        servers = {}
        lifespan_contexts = {}
        
        for ServerClass in self.SHARED_SERVERS:
            try:
                # 创建 server 实例，传递 agent_id 用于数据隔离
                server = ServerClass(agent_id=agent_id, agent_index=agent_index)
                server.setup()
                
                # 获取 ASGI app
                mcp_app = server.get_asgi_app(path="/")
                
                # 挂载路径: /agents/{agent_id}/mcp/{server_name}/
                # v2.9: 统一使用尾部斜杠，避免 Starlette Mount 路由匹配问题
                mount_path = f"/agents/{agent_id}/mcp/{server.name}/"
                
                # 初始化 lifespan
                lifespan_ctx = await self._init_lifespan(mcp_app, agent_id, server.name)
                if lifespan_ctx:
                    lifespan_contexts[server.name] = lifespan_ctx
                
                # 挂载到 FastAPI
                self.app.mount(mount_path, mcp_app)
                
                # v2.9: 确保新挂载的路由在 StaticFiles (catch-all "/") 之前
                self._reorder_routes_before_staticfiles()
                
                servers[server.name] = server
                logger.info(f"[MCPManager] Mounted {server.name} at {mount_path} for agent {agent_id}")
                
            except Exception as e:
                logger.error(f"[MCPManager] Failed to create {ServerClass.name} for agent {agent_id}: {e}")
        
        self._agent_shared_servers[agent_id] = servers
        self._agent_shared_lifespan_contexts[agent_id] = lifespan_contexts
        
        logger.info(f"[MCPManager] Created {len(servers)} shared servers for agent {agent_id}")
        return servers
    
    def has_agent_shared_servers(self, agent_id: str) -> bool:
        """检查 Agent 是否已有共享层 MCP servers。"""
        return agent_id in self._agent_shared_servers
    
    def get_agent_shared_server(self, agent_id: str, server_name: str) -> Optional[BaseMCPServer]:
        """获取 Agent 的共享层 MCP server。"""
        return self._agent_shared_servers.get(agent_id, {}).get(server_name)
    
    def get_agent_shared_mount_path(self, agent_id: str, server_name: str) -> str:
        """获取 Agent 共享层 MCP server 的挂载路径。"""
        return f"/agents/{agent_id}/mcp/{server_name}/"
    
    def get_agent_shared_mount_paths(self, agent_id: str) -> Dict[str, str]:
        """获取 Agent 所有共享层 MCP 的挂载路径。"""
        servers = self._agent_shared_servers.get(agent_id, {})
        return {
            name: f"/agents/{agent_id}/mcp/{name}/"
            for name in servers.keys()
        }
    
    async def remove_agent_shared_servers(self, agent_id: str) -> bool:
        """
        移除一个 Agent 的所有共享层 MCP servers。
        
        Args:
            agent_id: Agent ID
        
        Returns:
            是否成功移除
        """
        if agent_id not in self._agent_shared_servers:
            return False
        
        # 关闭 lifespan
        for server_name, lifespan_ctx in self._agent_shared_lifespan_contexts.get(agent_id, {}).items():
            try:
                await lifespan_ctx.__aexit__(None, None, None)
                logger.info(f"[MCPManager] Closed lifespan for {server_name} (agent {agent_id})")
            except Exception as e:
                logger.error(f"[MCPManager] Error closing lifespan for {server_name}: {e}")
        
        # 移除记录
        del self._agent_shared_servers[agent_id]
        self._agent_shared_lifespan_contexts.pop(agent_id, None)
        
        logger.info(f"[MCPManager] Removed shared servers for agent {agent_id}")
        return True
    
    # ========================================
    # Runtime 层管理 (由 Master 动态创建/销毁)
    # ========================================
    
    async def create_runtime_server(
        self, 
        agent_id: str, 
        subagent_id: str,
        agent_index: int = 0,
    ) -> RuntimeMCP:
        """
        为一个 Runtime 创建 single-agent-runtime MCP server。
        
        由 Master 调用，路径: /mcp/runtime/{subagent_id}/
        
        Args:
            agent_id: Agent ID
            subagent_id: Runtime ID (main-xxx 或 sub-xxx)
            agent_index: Agent index for port allocation
        
        Returns:
            创建的 server 实例
        """
        if subagent_id in self._runtime_servers:
            logger.warning(f"[MCPManager] Runtime server for {subagent_id} already exists")
            return self._runtime_servers[subagent_id]
        
        try:
            # 创建 server 实例，绑定 subagent_id
            server = RuntimeMCP(
                agent_id=agent_id, 
                agent_index=agent_index,
                subagent_id=subagent_id,
            )
            server.setup()
            
            # 获取 ASGI app
            mcp_app = server.get_asgi_app(path="/")
            
            # 挂载路径: /mcp/runtime/{subagent_id}/
            # v2.9: 统一使用尾部斜杠
            mount_path = f"/mcp/runtime/{subagent_id}/"
            
            # 初始化 lifespan
            lifespan_ctx = await self._init_lifespan(mcp_app, subagent_id, "single-agent-runtime")
            if lifespan_ctx:
                self._runtime_lifespan_contexts[subagent_id] = lifespan_ctx
            
            # 挂载到 FastAPI
            self.app.mount(mount_path, mcp_app)
            
            # v2.9: 确保新挂载的路由在 StaticFiles (catch-all "/") 之前
            self._reorder_routes_before_staticfiles()
            
            self._runtime_servers[subagent_id] = server
            logger.info(f"[MCPManager] Mounted runtime server at {mount_path}")
            
            return server
            
        except Exception as e:
            logger.error(f"[MCPManager] Failed to create runtime server for {subagent_id}: {e}")
            raise
    
    async def remove_runtime_server(self, subagent_id: str) -> bool:
        """
        移除一个 Runtime 的 MCP server。
        
        由 Master 在 Runtime 销毁时调用。
        
        Args:
            subagent_id: Runtime ID
        
        Returns:
            是否成功移除
        """
        if subagent_id not in self._runtime_servers:
            logger.warning(f"[MCPManager] Runtime server for {subagent_id} not found")
            return False
        
        try:
            # 关闭 lifespan
            lifespan_ctx = self._runtime_lifespan_contexts.pop(subagent_id, None)
            if lifespan_ctx:
                try:
                    await lifespan_ctx.__aexit__(None, None, None)
                    logger.info(f"[MCPManager] Closed lifespan for runtime {subagent_id}")
                except Exception as e:
                    logger.error(f"[MCPManager] Error closing lifespan for {subagent_id}: {e}")
            
            # 移除 server
            del self._runtime_servers[subagent_id]
            
            # 注意: FastAPI 不支持动态卸载路由，但 server 已被移除
            # 后续请求会返回 404
            
            logger.info(f"[MCPManager] Removed runtime server for {subagent_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MCPManager] Failed to remove runtime server for {subagent_id}: {e}")
            return False
    
    def get_runtime_server(self, subagent_id: str) -> Optional[RuntimeMCP]:
        """获取 Runtime 层 MCP server。"""
        return self._runtime_servers.get(subagent_id)
    
    def get_runtime_mount_path(self, subagent_id: str) -> str:
        """获取 Runtime 层 MCP server 的挂载路径。"""
        return f"/mcp/runtime/{subagent_id}/"
    
    # ========================================
    # 聚合层管理 (v2.7: 每个 Runtime 一个聚合 Gateway)
    # ========================================
    
    async def create_aggregate_gateway(
        self,
        agent_id: str,
        subagent_id: str,
        agent_index: int = 0,
    ) -> 'AggregateMCP':
        """
        为一个 Runtime 创建聚合 MCP Gateway。
        
        v2.7: 每个 Runtime 有自己的聚合 Gateway，聚合：
        - Runtime MCP (context_* 工具)
        - 共享层 MCP (chat, memory, local, qemudebug)
        - VM MCP
        
        注意：必须先调用 create_runtime_server 创建 Runtime MCP！
        
        Args:
            agent_id: Agent ID
            subagent_id: Runtime ID (main-xxx 或 sub-xxx)
            agent_index: Agent index for port allocation
        
        Returns:
            创建的聚合 Gateway 实例
        """
        if subagent_id in self._aggregate_gateways:
            logger.warning(f"[MCPManager] Aggregate gateway for {subagent_id} already exists")
            return self._aggregate_gateways[subagent_id]
        
        # 检查 Runtime MCP 是否已创建
        if subagent_id not in self._runtime_servers:
            raise ValueError(f"Runtime MCP for {subagent_id} not found. Call create_runtime_server first.")
        
        try:
            from mcp_gateway.gateway import AggregateMCP
            
            # 创建聚合 Gateway
            gateway = AggregateMCP(
                agent_id=agent_id,
                agent_index=agent_index,
                subagent_id=subagent_id,
            )
            
            # 设置（注册 skills 和 task_* 工具）
            await gateway.setup()
            
            # 获取 ASGI app
            mcp_app = gateway.get_asgi_app()
            
            # 挂载路径: /mcp/aggregate/{subagent_id}/
            # v2.9: 统一使用尾部斜杠
            mount_path = f"/mcp/aggregate/{subagent_id}/"
            
            # 初始化 lifespan
            lifespan_ctx = await self._init_lifespan(mcp_app, subagent_id, "aggregate-gateway")
            if lifespan_ctx:
                self._aggregate_lifespan_contexts[subagent_id] = lifespan_ctx
            
            # 挂载到 FastAPI
            self.app.mount(mount_path, mcp_app)
            
            # v2.9: 确保新挂载的路由在 StaticFiles (catch-all "/") 之前
            self._reorder_routes_before_staticfiles()
            
            # 启动后台发现任务
            gateway.start_discovery_task()
            
            self._aggregate_gateways[subagent_id] = gateway
            logger.info(f"[MCPManager] Mounted aggregate gateway at {mount_path}")
            
            return gateway
            
        except Exception as e:
            logger.error(f"[MCPManager] Failed to create aggregate gateway for {subagent_id}: {e}")
            raise
    
    async def remove_aggregate_gateway(self, subagent_id: str) -> bool:
        """
        移除一个 Runtime 的聚合 Gateway。
        
        Args:
            subagent_id: Runtime ID
        
        Returns:
            是否成功移除
        """
        if subagent_id not in self._aggregate_gateways:
            logger.warning(f"[MCPManager] Aggregate gateway for {subagent_id} not found")
            return False
        
        try:
            # 关闭 gateway
            gateway = self._aggregate_gateways[subagent_id]
            await gateway.close()
            
            # 关闭 lifespan
            lifespan_ctx = self._aggregate_lifespan_contexts.pop(subagent_id, None)
            if lifespan_ctx:
                try:
                    await lifespan_ctx.__aexit__(None, None, None)
                    logger.info(f"[MCPManager] Closed lifespan for aggregate {subagent_id}")
                except Exception as e:
                    logger.error(f"[MCPManager] Error closing lifespan for aggregate {subagent_id}: {e}")
            
            # 移除 gateway
            del self._aggregate_gateways[subagent_id]
            
            logger.info(f"[MCPManager] Removed aggregate gateway for {subagent_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MCPManager] Failed to remove aggregate gateway for {subagent_id}: {e}")
            return False
    
    def get_aggregate_gateway(self, subagent_id: str) -> Optional['AggregateMCP']:
        """获取聚合 Gateway 实例。"""
        return self._aggregate_gateways.get(subagent_id)
    
    def get_aggregate_mount_path(self, subagent_id: str) -> str:
        """获取聚合 Gateway 的挂载路径。"""
        return f"/mcp/aggregate/{subagent_id}/"
    
    # ========================================
    # 通用方法
    # ========================================
    
    def _reorder_routes_before_staticfiles(self):
        """
        v2.9: 确保动态添加的 Mount 在 StaticFiles (catch-all "/") 之前。
        
        问题：StaticFiles mount 在 "/" 会捕获所有请求，包括动态添加的 MCP routes。
        Starlette 按路由列表顺序匹配，所以需要确保 MCP routes 在 StaticFiles 之前。
        
        解决方案：找到 StaticFiles mount (name="web")，将其移到路由列表末尾。
        """
        from starlette.routing import Mount
        from starlette.staticfiles import StaticFiles
        
        web_mount = None
        web_index = None
        
        for i, route in enumerate(self.app.routes):
            if isinstance(route, Mount) and route.name == "web":
                web_mount = route
                web_index = i
                break
        
        if web_mount is not None:
            # 移除并重新添加到末尾
            self.app.routes.pop(web_index)
            self.app.routes.append(web_mount)
            logger.info(f"[MCPManager] Moved StaticFiles mount to end of routes (was at index {web_index})")
        else:
            logger.info(f"[MCPManager] No StaticFiles mount found (routes: {len(self.app.routes)})")
    
    async def _init_lifespan(self, mcp_app, context_id: str, server_name: str) -> Optional[Any]:
        """初始化 MCP app 的 lifespan。"""
        # 尝试 .lifespan 属性
        if hasattr(mcp_app, 'lifespan') and mcp_app.lifespan is not None:
            try:
                lifespan_ctx = mcp_app.lifespan(mcp_app)
                await lifespan_ctx.__aenter__()
                logger.info(f"[MCPManager] Initialized lifespan for {server_name} ({context_id})")
                return lifespan_ctx
            except Exception as e:
                logger.warning(f"[MCPManager] Failed lifespan init for {server_name}: {e}")
        
        # 尝试 .lifespan_handler 属性
        if hasattr(mcp_app, 'lifespan_handler') and mcp_app.lifespan_handler:
            try:
                lifespan_ctx = mcp_app.lifespan_handler(mcp_app)
                await lifespan_ctx.__aenter__()
                logger.info(f"[MCPManager] Initialized lifespan_handler for {server_name}")
                return lifespan_ctx
            except Exception as e:
                logger.warning(f"[MCPManager] Failed lifespan_handler for {server_name}: {e}")
        
        # 尝试 router.lifespan_context
        if hasattr(mcp_app, 'router') and hasattr(mcp_app.router, 'lifespan_context'):
            if mcp_app.router.lifespan_context is not None:
                try:
                    lifespan_ctx = mcp_app.router.lifespan_context(mcp_app)
                    await lifespan_ctx.__aenter__()
                    logger.info(f"[MCPManager] Initialized router.lifespan_context for {server_name}")
                    return lifespan_ctx
                except Exception as e:
                    logger.warning(f"[MCPManager] Failed router.lifespan_context for {server_name}: {e}")
        
        logger.debug(f"[MCPManager] No lifespan found for {server_name}")
        return None
    
    async def close_all(self) -> None:
        """关闭所有 MCP servers。"""
        # 关闭聚合层 (v2.7)
        for subagent_id in list(self._aggregate_gateways.keys()):
            await self.remove_aggregate_gateway(subagent_id)
        
        # 关闭 Runtime 层
        for subagent_id in list(self._runtime_servers.keys()):
            await self.remove_runtime_server(subagent_id)
        
        # 关闭共享层 (v2.9: per-agent)
        for agent_id in list(self._agent_shared_servers.keys()):
            await self.remove_agent_shared_servers(agent_id)
        
        logger.info("[MCPManager] Closed all servers")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息。"""
        return {
            "agent_shared_servers": {
                agent_id: list(servers.keys()) 
                for agent_id, servers in self._agent_shared_servers.items()
            },
            "total_agents_with_shared": len(self._agent_shared_servers),
            "runtime_servers": list(self._runtime_servers.keys()),
            "total_runtime_servers": len(self._runtime_servers),
            "aggregate_gateways": list(self._aggregate_gateways.keys()),
            "total_aggregate_gateways": len(self._aggregate_gateways),
        }


# 全局实例
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> Optional[MCPManager]:
    """获取全局 MCPManager 实例。"""
    return _mcp_manager


def set_mcp_manager(manager: MCPManager) -> None:
    """设置全局 MCPManager 实例。"""
    global _mcp_manager
    _mcp_manager = manager
