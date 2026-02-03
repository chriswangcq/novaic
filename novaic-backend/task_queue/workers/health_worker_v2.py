"""
HealthWorker v2 - 健康监控

基于 Task Queue v2 架构，通过 HTTP API 与 Gateway 通信。

职责：
1. 定期恢复超时任务
2. 定期恢复超时 Saga
3. 系统健康检查
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import traceback
import httpx


@dataclass
class HealthWorkerMetrics:
    """性能指标"""
    checks_performed: int = 0
    tasks_recovered: int = 0
    sagas_recovered: int = 0
    errors: int = 0
    last_check_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "checks_performed": self.checks_performed,
            "tasks_recovered": self.tasks_recovered,
            "sagas_recovered": self.sagas_recovered,
            "errors": self.errors,
            "last_check_at": self.last_check_at,
            "started_at": self.started_at,
        }


class HealthWorkerV2:
    """
    健康监控 Worker (v2)
    
    职责：
    1. 定期调用 Gateway 的恢复 API
    2. 恢复超时的任务和 Saga
    """
    
    name = "health-worker-v2"
    
    def __init__(
        self,
        gateway_url: str = "http://127.0.0.1:19999",
        check_interval: float = 30.0,
        task_timeout: int = 60,
        saga_timeout: int = 120,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.check_interval = check_interval
        self.task_timeout = task_timeout
        self.saga_timeout = saga_timeout
        self.worker_id = f"health-{uuid.uuid4().hex[:8]}"
        
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._client: Optional[httpx.AsyncClient] = None
        
        self.metrics = HealthWorkerMetrics()
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.gateway_url,
                timeout=30.0,
            )
        return self._client
    
    async def run(self):
        """主循环"""
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log(f"Starting (worker_id: {self.worker_id})...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    await self._perform_check()
                    
                    # 等待下一次检查
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=self.check_interval
                        )
                        break  # shutdown event was set
                    except asyncio.TimeoutError:
                        pass  # continue checking
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    self.metrics.errors += 1
                    await asyncio.sleep(self.check_interval)
        
        finally:
            self._running = False
            if self._client:
                await self._client.aclose()
            self._log("Stopped")
    
    async def shutdown(self):
        """优雅关闭"""
        self._log("Shutting down...")
        self._shutdown_event.set()
    
    async def _perform_check(self):
        """执行健康检查"""
        self.metrics.checks_performed += 1
        self.metrics.last_check_at = datetime.utcnow().isoformat()
        
        client = await self._get_client()
        
        try:
            # 调用统一恢复 API
            resp = await client.post(
                "/internal/tq/recover/all",
                params={
                    "task_timeout": self.task_timeout,
                    "saga_timeout": self.saga_timeout,
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                tasks_recovered = data.get("tasks_recovered", 0)
                sagas_recovered = data.get("sagas_recovered", 0)
                
                self.metrics.tasks_recovered += tasks_recovered
                self.metrics.sagas_recovered += sagas_recovered
                
                if tasks_recovered > 0 or sagas_recovered > 0:
                    self._log(
                        f"Recovered: {tasks_recovered} tasks, {sagas_recovered} sagas"
                    )
            else:
                self._log(f"Gateway error: {resp.status_code}", level="error")
                self.metrics.errors += 1
                
        except Exception as e:
            self._log(f"Health check failed: {e}", level="error")
            self.metrics.errors += 1
    
    def _log(self, msg: str, level: str = "info"):
        """日志输出"""
        prefix = f"[{self.name}]"
        if level == "error":
            print(f"{prefix} ERROR: {msg}")
        else:
            print(f"{prefix} {msg}")
    
    def get_metrics(self) -> dict:
        """获取指标"""
        return self.metrics.to_dict()
