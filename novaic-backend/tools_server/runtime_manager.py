"""
RuntimeManager - 管理 Runtime 的工具上下文

负责：
- 内存存储 Runtime 上下文信息
- 创建、获取、删除 Runtime 上下文
- 管理外部 MCP 工具发现
- 通过 Gateway API 持久化注册信息，重启后可恢复
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

import httpx

from common.config import ServiceConfig
from common.http.clients import internal_client, internal_async_client
from mcp_client.registry import ToolRegistry
from tools_server.reliability import get_tools_reliability_policy

# /internal/runtimes* must target Runtime Orchestrator, not Gateway
RO_URL = getattr(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None) or ServiceConfig.GATEWAY_URL

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
    execution_semaphore: Optional[asyncio.Semaphore] = None  # 每个 runtime 的工具并发隔离


class RuntimeManager:
    """
    Runtime 上下文管理器
    
    功能：
    - 内存存储所有 Runtime 上下文
    - 支持 CRUD 操作
    - 管理外部 MCP 工具发现
    - 通过 Gateway API 持久化 tool_ports，重启后自动恢复
    """
    
    def __init__(self, gateway_url: Optional[str] = None):
        """初始化 RuntimeManager
        
        Args:
            gateway_url: Gateway base URL (for persisting tool_ports)
        """
        self._runtimes: Dict[str, RuntimeContext] = {}
        self._registry: Optional[ToolRegistry] = None
        self._lock = asyncio.Lock()
        self._gateway_url = gateway_url
        self._reliability_policy = get_tools_reliability_policy()
        self._max_concurrent_tools_per_runtime = (
            self._reliability_policy.max_concurrent_tools_per_runtime
        )
        
        logger.info(f"[RuntimeManager] Initialized (gateway={gateway_url})")
    
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
            created_at=datetime.utcnow(),
            external_tools=[],
            discovery_task=None,
            execution_semaphore=asyncio.Semaphore(self._max_concurrent_tools_per_runtime),
        )
        
        self._runtimes[runtime_id] = context
        
        # Persist tool_ports to Gateway for recovery after restart
        self._persist_tool_ports(runtime_id, ports)
        
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
        
        # Clear tool_ports in Gateway
        self._persist_tool_ports(runtime_id, None)
        
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
            
            # 发现所有工具（MCP 服务器）
            tools = await self._registry.discover_all_tools(use_cache=False)
            
            # 过滤出属于当前 runtime 的工具
            runtime_tools = [
                tool for tool in tools
                if tool.get("_server", "").startswith(f"{runtime_id}_")
            ]
            
            # NOTE: VM 工具不在这里添加！
            # VM 工具已经在 tools.py 的 get_all_tools() 中作为 builtin 添加
            # 这里的 external_tools 只应该包含真正的外部 MCP 服务器工具
            # 如果在这里再次添加 VM 工具，会导致重复
            
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
    
    # ========================================
    # Gateway Persistence
    # ========================================
    
    def _persist_tool_ports(self, runtime_id: str, ports: Optional[dict]) -> None:
        """Persist tool_ports to RO DB via API (best-effort, non-blocking).
        /internal/runtimes* targets Runtime Orchestrator, not Gateway.
        
        Args:
            runtime_id: Runtime ID
            ports: MCP ports dict, or None to clear
        """
        base = self._gateway_url or RO_URL
        if not base:
            return
        try:
            with internal_client(base_url=RO_URL, timeout=5.0) as client:
                client.post(
                    f"/internal/runtimes/{runtime_id}/tool-ports",
                    json={"ports": ports},
                )
            logger.debug(f"[RuntimeManager] Persisted tool_ports for {runtime_id}: {ports}")
        except Exception as e:
            # Best-effort: don't fail runtime creation/deletion if Gateway is unreachable
            logger.warning(f"[RuntimeManager] Failed to persist tool_ports for {runtime_id}: {e}")
    
    async def restore_from_gateway(self, max_retries: int = 5, retry_delay: float = 3.0) -> int:
        """Restore runtime contexts from Gateway on startup.
        
        Queries Gateway for active runtimes with tool_ports set,
        re-creates them in memory and starts tool discovery.
        
        Retries with delay to handle startup race condition where
        Gateway may not be ready yet when Tools Server starts.
        
        Returns:
            Number of runtimes restored
        """
        if not self._gateway_url:
            logger.info("[RuntimeManager] No gateway_url configured, skipping restore")
            return 0
        
        data = None
        for attempt in range(1, max_retries + 1):
            try:
                async with internal_async_client(base_url=RO_URL, timeout=10.0) as client:
                    resp = await client.get("/internal/runtimes/with-tools")
                    resp.raise_for_status()
                    data = resp.json()
                    break  # Success
            except Exception as e:
                if attempt < max_retries:
                    logger.info(
                        f"[RuntimeManager] Gateway not ready (attempt {attempt}/{max_retries}), "
                        f"retrying in {retry_delay}s... ({e})"
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    logger.warning(
                        f"[RuntimeManager] Failed to query Gateway after {max_retries} attempts: {e}"
                    )
                    return 0
        
        if data is None:
            return 0
        
        runtimes = data.get("runtimes", [])
        if not runtimes:
            logger.info("[RuntimeManager] No active runtimes with tools to restore")
            return 0
        
        restored = 0
        for rt in runtimes:
            runtime_id = rt.get("runtime_id")
            agent_id = rt.get("agent_id")
            subagent_id = rt.get("subagent_id")
            ports = rt.get("tool_ports", {})
            
            if runtime_id in self._runtimes:
                logger.debug(f"[RuntimeManager] Runtime {runtime_id} already in memory, skipping")
                continue
            
            try:
                context = RuntimeContext(
                    runtime_id=runtime_id,
                    agent_id=agent_id,
                    subagent_id=subagent_id,
                    ports=ports,
                    created_at=datetime.utcnow(),
                    external_tools=[],
                    discovery_task=None,
                    execution_semaphore=asyncio.Semaphore(self._max_concurrent_tools_per_runtime),
                )
                self._runtimes[runtime_id] = context
                
                # Start tool discovery only if there are external MCP ports
                if ports:
                    await self.start_discovery(runtime_id)
                
                restored += 1
                logger.info(
                    f"[RuntimeManager] Restored runtime: {runtime_id}, "
                    f"agent={agent_id}, subagent={subagent_id}, ports={ports}"
                )
            except Exception as e:
                logger.error(f"[RuntimeManager] Failed to restore runtime {runtime_id}: {e}")
        
        logger.info(f"[RuntimeManager] Restored {restored}/{len(runtimes)} runtimes from Gateway")
        return restored
    
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


def init_runtime_manager(gateway_url: Optional[str] = None) -> RuntimeManager:
    """
    初始化 RuntimeManager 单例（带 gateway_url 参数）
    
    应在 Tools Server 启动时调用一次。
    
    Args:
        gateway_url: Gateway base URL for persistence
        
    Returns:
        RuntimeManager 实例
    """
    global _runtime_manager
    _runtime_manager = RuntimeManager(gateway_url=gateway_url)
    return _runtime_manager


async def shutdown_runtime_manager() -> None:
    """
    关闭 RuntimeManager 单例
    """
    global _runtime_manager
    if _runtime_manager is not None:
        await _runtime_manager.close()
        _runtime_manager = None
