"""
SubMCPManager - 子 MCP Server 管理器

管理所有子 MCP Server 的生命周期：
- 创建和初始化子 MCP servers
- 挂载到 FastAPI 应用
- 管理 lifespan
"""

import os
import logging
from typing import Dict, List, Any, Optional, Type

from fastapi import FastAPI

from .base import BaseMCPServer
from .single_agent_runtime import SingleAgentRuntimeMCPServer
from .local import LocalMCPServer
from .memory import MemoryMCPServer
from .chat import ChatMCPServer
from .qemudebug import QemuDebugMCPServer

logger = logging.getLogger(__name__)


class SubMCPManager:
    """
    子 MCP Server 管理器。
    
    负责：
    1. 创建和管理子 MCP servers
    2. 挂载到 FastAPI 应用的子路径
    3. 管理 lifespan
    """
    
    # 默认子 MCP Server 类 (always enabled)
    # QemuDebugMCPServer is always enabled as fallback when VM is not ready
    DEFAULT_SERVERS: List[Type[BaseMCPServer]] = [
        SingleAgentRuntimeMCPServer,
        LocalMCPServer,
        MemoryMCPServer,
        ChatMCPServer,
        QemuDebugMCPServer,  # Fallback for VM tools
    ]
    
    # 可选子 MCP Server 类 (enabled via environment)
    OPTIONAL_SERVERS: Dict[str, Type[BaseMCPServer]] = {
        # Currently empty - qemudebug moved to DEFAULT_SERVERS
    }
    
    def _get_enabled_servers(self) -> List[Type[BaseMCPServer]]:
        """获取所有启用的子 MCP Server 类。"""
        servers = list(self.DEFAULT_SERVERS)
        
        for env_var, server_class in self.OPTIONAL_SERVERS.items():
            if os.getenv(env_var, "false").lower() == "true":
                servers.append(server_class)
                logger.info(f"[SubMCPManager] Optional server enabled: {server_class.name}")
        
        return servers
    
    def __init__(self, app: FastAPI, base_path: str = "/agents/{agent_id}/sub-mcp"):
        """
        初始化子 MCP 管理器。
        
        子 MCP 挂载在 /agents/{id}/sub-mcp/{name}，避免与 Gateway MCP 路径冲突。
        Gateway MCP 挂载在 /agents/{id}/mcp。
        
        Args:
            app: FastAPI 应用实例
            base_path: 子 MCP 挂载的基础路径模板
        """
        self.app = app
        self.base_path = base_path
        
        # 存储已创建的 servers: {agent_id: {server_name: server_instance}}
        self._servers: Dict[str, Dict[str, BaseMCPServer]] = {}
        
        # 存储 lifespan 上下文: {agent_id: {server_name: lifespan_ctx}}
        self._lifespan_contexts: Dict[str, Dict[str, Any]] = {}
        
        logger.info("[SubMCPManager] Initialized")
    
    async def create_servers_for_agent(self, agent_id: str, agent_index: int = 0) -> Dict[str, BaseMCPServer]:
        """
        为一个 agent 创建所有子 MCP servers。
        
        Args:
            agent_id: Agent ID
            agent_index: Agent index for port allocation
        
        Returns:
            字典 {server_name: server_instance}
        """
        if agent_id in self._servers:
            logger.warning(f"[SubMCPManager] Servers for agent {agent_id} already exist")
            return self._servers[agent_id]
        
        servers = {}
        lifespan_contexts = {}
        
        for ServerClass in self._get_enabled_servers():
            try:
                # 创建 server 实例，传递 agent_id 和 agent_index 用于资源隔离
                server = ServerClass(agent_id=agent_id, agent_index=agent_index)
                server.setup()
                
                # 获取 ASGI app
                mcp_app = server.get_asgi_app(path="/")
                
                # 计算挂载路径
                mount_path = self.base_path.format(agent_id=agent_id) + f"/{server.name}"
                
                # 初始化 lifespan
                lifespan_ctx = await self._init_lifespan(mcp_app, agent_id, server.name)
                if lifespan_ctx:
                    lifespan_contexts[server.name] = lifespan_ctx
                
                # 挂载到 FastAPI
                self.app.mount(mount_path, mcp_app)
                
                servers[server.name] = server
                logger.info(f"[SubMCPManager] Mounted {server.name} at {mount_path}")
                
            except Exception as e:
                logger.error(f"[SubMCPManager] Failed to create {ServerClass.name}: {e}")
        
        self._servers[agent_id] = servers
        self._lifespan_contexts[agent_id] = lifespan_contexts
        
        logger.info(f"[SubMCPManager] Created {len(servers)} servers for agent {agent_id}")
        return servers
    
    async def _init_lifespan(self, mcp_app, agent_id: str, server_name: str) -> Optional[Any]:
        """初始化 MCP app 的 lifespan。"""
        # 尝试 .lifespan 属性
        if hasattr(mcp_app, 'lifespan') and mcp_app.lifespan is not None:
            try:
                lifespan_ctx = mcp_app.lifespan(mcp_app)
                await lifespan_ctx.__aenter__()
                logger.info(f"[SubMCPManager] Initialized lifespan for {server_name} (agent {agent_id})")
                return lifespan_ctx
            except Exception as e:
                logger.warning(f"[SubMCPManager] Failed lifespan init for {server_name}: {e}")
        
        # 尝试 .lifespan_handler 属性
        if hasattr(mcp_app, 'lifespan_handler') and mcp_app.lifespan_handler:
            try:
                lifespan_ctx = mcp_app.lifespan_handler(mcp_app)
                await lifespan_ctx.__aenter__()
                logger.info(f"[SubMCPManager] Initialized lifespan_handler for {server_name}")
                return lifespan_ctx
            except Exception as e:
                logger.warning(f"[SubMCPManager] Failed lifespan_handler for {server_name}: {e}")
        
        # 尝试 router.lifespan_context
        if hasattr(mcp_app, 'router') and hasattr(mcp_app.router, 'lifespan_context'):
            if mcp_app.router.lifespan_context is not None:
                try:
                    lifespan_ctx = mcp_app.router.lifespan_context(mcp_app)
                    await lifespan_ctx.__aenter__()
                    logger.info(f"[SubMCPManager] Initialized router.lifespan_context for {server_name}")
                    return lifespan_ctx
                except Exception as e:
                    logger.warning(f"[SubMCPManager] Failed router.lifespan_context for {server_name}: {e}")
        
        logger.debug(f"[SubMCPManager] No lifespan found for {server_name}")
        return None
    
    def get_server(self, agent_id: str, server_name: str) -> Optional[BaseMCPServer]:
        """获取指定的子 MCP server。"""
        return self._servers.get(agent_id, {}).get(server_name)
    
    def get_servers_for_agent(self, agent_id: str) -> Dict[str, BaseMCPServer]:
        """获取 agent 的所有子 MCP servers。"""
        return self._servers.get(agent_id, {})
    
    def get_mount_paths(self, agent_id: str) -> Dict[str, str]:
        """获取 agent 的所有子 MCP 挂载路径。"""
        servers = self._servers.get(agent_id, {})
        return {
            name: self.base_path.format(agent_id=agent_id) + f"/{name}"
            for name in servers.keys()
        }
    
    async def remove_agent(self, agent_id: str) -> bool:
        """
        移除一个 agent 的所有子 MCP servers。
        
        Args:
            agent_id: Agent ID
        
        Returns:
            是否成功移除
        """
        if agent_id not in self._servers:
            return False
        
        # 关闭 lifespan
        for server_name, lifespan_ctx in self._lifespan_contexts.get(agent_id, {}).items():
            try:
                await lifespan_ctx.__aexit__(None, None, None)
                logger.info(f"[SubMCPManager] Closed lifespan for {server_name} (agent {agent_id})")
            except Exception as e:
                logger.error(f"[SubMCPManager] Error closing lifespan for {server_name}: {e}")
        
        # 清理
        del self._servers[agent_id]
        self._lifespan_contexts.pop(agent_id, None)
        
        logger.info(f"[SubMCPManager] Removed servers for agent {agent_id}")
        return True
    
    async def close_all(self) -> None:
        """关闭所有子 MCP servers。"""
        for agent_id in list(self._servers.keys()):
            await self.remove_agent(agent_id)
        
        logger.info("[SubMCPManager] Closed all servers")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息。"""
        return {
            "total_agents": len(self._servers),
            "servers_per_agent": {
                agent_id: list(servers.keys())
                for agent_id, servers in self._servers.items()
            },
        }


# 全局实例
_sub_mcp_manager: Optional[SubMCPManager] = None


def get_sub_mcp_manager() -> Optional[SubMCPManager]:
    """获取全局 SubMCPManager 实例。"""
    return _sub_mcp_manager


def set_sub_mcp_manager(manager: SubMCPManager) -> None:
    """设置全局 SubMCPManager 实例。"""
    global _sub_mcp_manager
    _sub_mcp_manager = manager
