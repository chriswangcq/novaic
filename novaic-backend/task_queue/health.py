"""
Health Monitor - 健康监控服务

两种运行模式：
1. Gateway 内嵌模式: 直接操作 TaskQueue/SagaRepository
2. 独立进程模式: 通过 HTTP API 调用 Gateway

职责：
1. 定时恢复超时任务
2. 检测卡住的 Saga
3. 记录健康指标
"""

import asyncio
import aiohttp
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Protocol


# ============================================================
# Protocol for TaskQueue (支持本地和远程)
# ============================================================

class RecoverableProtocol(Protocol):
    """可恢复任务的接口"""
    async def recover_stale(self, timeout_seconds: int) -> int: ...


@dataclass
class HealthMetrics:
    """健康监控指标"""
    checks: int = 0
    recovered_tasks: int = 0
    recovered_sagas: int = 0
    last_check_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "checks": self.checks,
            "recovered_tasks": self.recovered_tasks,
            "recovered_sagas": self.recovered_sagas,
            "last_check_at": self.last_check_at,
            "started_at": self.started_at,
        }


class HealthMonitor:
    """
    健康监控服务 (Gateway 内嵌模式)
    
    使用方式：
        monitor = HealthMonitor(queue)
        await monitor.run()
    """
    
    def __init__(
        self,
        queue: RecoverableProtocol,
        saga_repository: Optional[Any] = None,
        check_interval: float = 30.0,
        task_timeout: int = 60,
        saga_timeout: int = 300,
        name: str = "health-monitor",
    ):
        self.queue = queue
        self.saga_repository = saga_repository
        self.check_interval = check_interval
        self.task_timeout = task_timeout
        self.saga_timeout = saga_timeout
        self.name = name
        
        self._running = False
        self._shutdown_event = asyncio.Event()
        self.metrics = HealthMetrics()
    
    async def run(self):
        """主循环"""
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log("Starting...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    await self._check_and_recover()
                    self.metrics.checks += 1
                    self.metrics.last_check_at = datetime.utcnow().isoformat()
                except Exception as e:
                    self._log(f"Error: {e}", level="error")
                
                await asyncio.sleep(self.check_interval)
        finally:
            self._running = False
            self._log("Stopped")
    
    async def _check_and_recover(self):
        """检查并恢复"""
        # 恢复超时任务
        recovered = await self.queue.recover_stale(self.task_timeout)
        if recovered > 0:
            self.metrics.recovered_tasks += recovered
            self._log(f"Recovered {recovered} stale task(s)")
        
        # 恢复卡住的 Saga
        if self.saga_repository:
            recovered = await self._recover_stale_sagas()
            if recovered > 0:
                self.metrics.recovered_sagas += recovered
                self._log(f"Recovered {recovered} stale saga(s)")
    
    async def _recover_stale_sagas(self) -> int:
        """恢复卡住的 Saga"""
        pending = await self.saga_repository.get_pending()
        
        recovered = 0
        for saga in pending:
            created_at = saga.get("created_at")
            if not created_at:
                continue
            
            try:
                created_time = datetime.fromisoformat(created_at)
                elapsed = (datetime.utcnow() - created_time).total_seconds()
                
                if elapsed > self.saga_timeout:
                    try:
                        await self.saga_repository.resume(saga["id"])
                        recovered += 1
                    except Exception as e:
                        self._log(f"Failed to resume {saga['id']}: {e}", level="error")
            except (ValueError, TypeError):
                pass
        
        return recovered
    
    async def shutdown(self):
        self._log("Shutdown requested...")
        self._shutdown_event.set()
    
    def _log(self, message: str, level: str = "info"):
        prefix = f"[{self.name}]"
        if level == "error":
            print(f"{prefix} ERROR: {message}")
        elif level == "warning":
            print(f"{prefix} WARNING: {message}")
        else:
            print(f"{prefix} {message}")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def get_status(self) -> dict:
        return {
            "name": self.name,
            "running": self._running,
            "metrics": self.metrics.to_dict(),
        }


class HealthMonitorClient:
    """
    健康监控服务 (独立进程模式)
    
    通过 HTTP API 调用 Gateway 执行恢复操作。
    
    使用方式：
        monitor = HealthMonitorClient("http://localhost:8716")
        await monitor.run()
    """
    
    def __init__(
        self,
        gateway_url: str,
        check_interval: float = 30.0,
        task_timeout: int = 60,
        name: str = "health-monitor-client",
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.check_interval = check_interval
        self.task_timeout = task_timeout
        self.name = name
        
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._session: Optional[aiohttp.ClientSession] = None
        self.metrics = HealthMetrics()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def run(self):
        """主循环"""
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log("Starting...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    await self._check_and_recover()
                    self.metrics.checks += 1
                    self.metrics.last_check_at = datetime.utcnow().isoformat()
                except Exception as e:
                    self._log(f"Error: {e}", level="error")
                
                await asyncio.sleep(self.check_interval)
        finally:
            self._running = False
            await self.close()
            self._log("Stopped")
    
    async def _check_and_recover(self):
        """通过 HTTP API 恢复超时任务"""
        session = await self._get_session()
        url = f"{self.gateway_url}/internal/tq/recover-stale"
        
        try:
            async with session.post(url, params={"timeout_seconds": self.task_timeout}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    recovered = data.get("recovered", 0)
                    if recovered > 0:
                        self.metrics.recovered_tasks += recovered
                        self._log(f"Recovered {recovered} stale task(s)")
                else:
                    self._log(f"API error: {resp.status}", level="error")
        except aiohttp.ClientError as e:
            self._log(f"HTTP error: {e}", level="error")
    
    async def shutdown(self):
        self._log("Shutdown requested...")
        self._shutdown_event.set()
    
    def _log(self, message: str, level: str = "info"):
        prefix = f"[{self.name}]"
        if level == "error":
            print(f"{prefix} ERROR: {message}")
        elif level == "warning":
            print(f"{prefix} WARNING: {message}")
        else:
            print(f"{prefix} {message}")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def get_status(self) -> dict:
        return {
            "name": self.name,
            "running": self._running,
            "metrics": self.metrics.to_dict(),
        }


async def run_health_monitor(
    queue: Optional[RecoverableProtocol] = None,
    gateway_url: Optional[str] = None,
    **kwargs,
):
    """
    运行健康监控服务
    
    Args:
        queue: TaskQueue 实例 (本地模式)
        gateway_url: Gateway URL (远程模式)
        **kwargs: 配置参数
    """
    if gateway_url:
        monitor = HealthMonitorClient(gateway_url, **kwargs)
    elif queue:
        monitor = HealthMonitor(queue, **kwargs)
    else:
        raise ValueError("Must provide either queue or gateway_url")
    
    await monitor.run()
