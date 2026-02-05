"""
RuntimeManager - 管理 Runtime 的工具上下文

负责：
- 内存存储 Runtime 上下文信息
- 创建、获取、删除 Runtime 上下文
- 管理外部 MCP 工具发现
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from mcp_client.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class RuntimeContext:
    """Runtime 上下文数据结构"""
    runtime_id: str
    agent_id: str
    subagent_id: str
    ports: dict  # 端口配置
    created_at: datetime
    external_tools: List[dict] = field(default_factory=list)  # 外部 MCP 发现的工具
    discovery_task: Optional[asyncio.Task] = None  # 外部工具发现任务


class RuntimeManager:
    """
    Runtime 上下文管理器
    
    功能：
    - 内存存储所有 Runtime 上下文
    - 支持 CRUD 操作
    - 管理外部 MCP 工具发现
    """
    
    def __init__(self):
        """初始化 RuntimeManager"""
        self._runtimes: Dict[str, RuntimeContext] = {}
        self._registry: Optional[ToolRegistry] = None
        self._lock = asyncio.Lock()
        
        logger.info("[RuntimeManager] Initialized")
    
    def create(
        self,
        runtime_id: str,
        agent_id: str,
        subagent_id: str,
        ports: dict
    ) -> RuntimeContext:
        """
        创建 Runtime 上下文
        
        Args:
            runtime_id: Runtime 唯一标识
            agent_id: Agent ID
            subagent_id: Subagent ID
            ports: 端口配置 (如 {"vmuse": 8080, "mcp": 9000})
        
        Returns:
            创建的 RuntimeContext 实例
        
        Raises:
            ValueError: 如果 runtime_id 已存在
        """
        if runtime_id in self._runtimes:
            raise ValueError(f"Runtime '{runtime_id}' already exists")
        
        context = RuntimeContext(
            runtime_id=runtime_id,
            agent_id=agent_id,
            subagent_id=subagent_id,
            ports=ports,
            created_at=datetime.now(),
            external_tools=[],
            discovery_task=None,
        )
        
        self._runtimes[runtime_id] = context
        
        logger.info(
            f"[RuntimeManager] Created runtime: {runtime_id}, "
            f"agent={agent_id}, subagent={subagent_id}, ports={ports}"
        )
        
        return context
    
    def get(self, runtime_id: str) -> Optional[RuntimeContext]:
        """
        获取 Runtime 上下文
        
        Args:
            runtime_id: Runtime 唯一标识
        
        Returns:
            RuntimeContext 实例，如果不存在则返回 None
        """
        return self._runtimes.get(runtime_id)
    
    def delete(self, runtime_id: str) -> bool:
        """
        删除 Runtime 上下文
        
        Args:
            runtime_id: Runtime 唯一标识
        
        Returns:
            True 如果成功删除，False 如果不存在
        """
        context = self._runtimes.get(runtime_id)
        if context is None:
            return False
        
        # 取消正在进行的发现任务
        if context.discovery_task and not context.discovery_task.done():
            context.discovery_task.cancel()
            logger.info(f"[RuntimeManager] Cancelled discovery task for runtime: {runtime_id}")
        
        del self._runtimes[runtime_id]
        
        logger.info(f"[RuntimeManager] Deleted runtime: {runtime_id}")
        return True
    
    def list_all(self) -> List[RuntimeContext]:
        """
        列出所有 Runtime 上下文
        
        Returns:
            所有 RuntimeContext 实例的列表
        """
        return list(self._runtimes.values())
    
    async def start_discovery(self, runtime_id: str) -> None:
        """
        启动外部工具发现
        
        使用 ToolRegistry 发现 Runtime 端口上可用的 MCP 工具
        
        Args:
            runtime_id: Runtime 唯一标识
        
        Raises:
            ValueError: 如果 runtime_id 不存在
        """
        context = self._runtimes.get(runtime_id)
        if context is None:
            raise ValueError(f"Runtime '{runtime_id}' not found")
        
        # 取消已有的发现任务
        if context.discovery_task and not context.discovery_task.done():
            context.discovery_task.cancel()
            try:
                await context.discovery_task
            except asyncio.CancelledError:
                pass
        
        # 创建新的发现任务
        context.discovery_task = asyncio.create_task(
            self._discover_tools(runtime_id)
        )
        
        logger.info(f"[RuntimeManager] Started discovery for runtime: {runtime_id}")
    
    async def _discover_tools(self, runtime_id: str) -> None:
        """
        内部方法：执行工具发现
        
        Args:
            runtime_id: Runtime 唯一标识
        """
        context = self._runtimes.get(runtime_id)
        if context is None:
            return
        
        # 初始化或获取 ToolRegistry
        if self._registry is None:
            self._registry = ToolRegistry()
        
        try:
            # 注册端口对应的 MCP 服务器
            for name, port in context.ports.items():
                if isinstance(port, int):
                    self._registry.register_server(
                        name=f"{runtime_id}_{name}",
                        port=port,
                        enabled=True,
                        connect_timeout=5.0,  # 外部服务可能需要更长超时
                    )
                    logger.debug(
                        f"[RuntimeManager] Registered server {name} "
                        f"on port {port} for runtime {runtime_id}"
                    )
            
            # 发现所有工具
            tools = await self._registry.discover_all_tools(use_cache=False)
            
            # 过滤出属于当前 runtime 的工具
            runtime_tools = [
                tool for tool in tools
                if tool.get("_server", "").startswith(f"{runtime_id}_")
            ]
            
            # 更新上下文中的外部工具列表
            async with self._lock:
                if runtime_id in self._runtimes:
                    self._runtimes[runtime_id].external_tools = runtime_tools
            
            logger.info(
                f"[RuntimeManager] Discovered {len(runtime_tools)} tools "
                f"for runtime: {runtime_id}"
            )
            
        except asyncio.CancelledError:
            logger.info(f"[RuntimeManager] Discovery cancelled for runtime: {runtime_id}")
            raise
        except Exception as e:
            logger.error(
                f"[RuntimeManager] Discovery failed for runtime {runtime_id}: {e}"
            )
    
    def get_external_tools(self, runtime_id: str) -> List[dict]:
        """
        获取 Runtime 的外部工具列表
        
        Args:
            runtime_id: Runtime 唯一标识
        
        Returns:
            外部工具列表，如果 runtime 不存在则返回空列表
        """
        context = self._runtimes.get(runtime_id)
        if context is None:
            return []
        return context.external_tools
    
    def get_stats(self) -> dict:
        """
        获取统计信息
        
        Returns:
            包含统计数据的字典
        """
        active_discoveries = sum(
            1 for ctx in self._runtimes.values()
            if ctx.discovery_task and not ctx.discovery_task.done()
        )
        
        total_external_tools = sum(
            len(ctx.external_tools) for ctx in self._runtimes.values()
        )
        
        return {
            "total_runtimes": len(self._runtimes),
            "active_discoveries": active_discoveries,
            "total_external_tools": total_external_tools,
            "runtimes": [
                {
                    "runtime_id": ctx.runtime_id,
                    "agent_id": ctx.agent_id,
                    "subagent_id": ctx.subagent_id,
                    "ports": ctx.ports,
                    "created_at": ctx.created_at.isoformat(),
                    "external_tools_count": len(ctx.external_tools),
                    "discovery_active": (
                        ctx.discovery_task is not None 
                        and not ctx.discovery_task.done()
                    ),
                }
                for ctx in self._runtimes.values()
            ],
        }
    
    async def close(self) -> None:
        """
        关闭 RuntimeManager，清理所有资源
        """
        # 取消所有发现任务
        for runtime_id, context in self._runtimes.items():
            if context.discovery_task and not context.discovery_task.done():
                context.discovery_task.cancel()
                try:
                    await context.discovery_task
                except asyncio.CancelledError:
                    pass
        
        # 关闭 ToolRegistry
        if self._registry:
            await self._registry.close()
            self._registry = None
        
        # 清空运行时
        self._runtimes.clear()
        
        logger.info("[RuntimeManager] Closed and cleaned up all resources")


# 单例实例
_runtime_manager: Optional[RuntimeManager] = None


def get_runtime_manager() -> RuntimeManager:
    """
    获取 RuntimeManager 单例实例
    
    Returns:
        RuntimeManager 实例
    """
    global _runtime_manager
    if _runtime_manager is None:
        _runtime_manager = RuntimeManager()
    return _runtime_manager


async def shutdown_runtime_manager() -> None:
    """
    关闭 RuntimeManager 单例
    """
    global _runtime_manager
    if _runtime_manager is not None:
        await _runtime_manager.close()
        _runtime_manager = None
