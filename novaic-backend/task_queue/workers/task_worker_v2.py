"""
TaskWorker v2 - 通用任务执行器

基于 Task Queue v2 架构，通过 HTTP API 与 Gateway 通信。

SagaWorker 通过 TaskQueue 发布任务，TaskWorker 负责执行这些任务。
这种分离设计支持：
- 异步执行：SagaWorker 发布任务后可以处理其他 Saga
- 负载均衡：多个 TaskWorker 可以分担任务
- 故障恢复：任务有 idempotency_key，支持重入

流程：
1. claim 任务 (POST /internal/tq/tasks/claim)
2. 执行 Handler (POST /internal/tq/handlers/execute)
3. complete/fail 任务 (POST /internal/tq/tasks/{id}/complete or fail)
4. 定期发送心跳 (POST /internal/tq/tasks/{id}/heartbeat)
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback
import httpx


@dataclass
class TaskWorkerMetrics:
    """性能指标"""
    tasks_processed: int = 0
    tasks_succeeded: int = 0
    tasks_failed: int = 0
    tasks_retried: int = 0
    last_task_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "tasks_processed": self.tasks_processed,
            "tasks_succeeded": self.tasks_succeeded,
            "tasks_failed": self.tasks_failed,
            "tasks_retried": self.tasks_retried,
            "last_task_at": self.last_task_at,
            "started_at": self.started_at,
        }


class TaskWorkerV2:
    """
    通用任务执行器 (v2)
    
    职责：
    1. 认领指定 topics 的任务
    2. 通过 Gateway API 执行 Handler
    3. 报告任务结果
    4. 维护心跳
    """
    
    name = "task-worker-v2"
    
    def __init__(
        self,
        topics: List[str],
        gateway_url: str = "http://127.0.0.1:19999",
        poll_interval: float = 0.1,
        heartbeat_interval: float = 10.0,
        timeout: float = 60.0,
    ):
        self.topics = topics
        self.gateway_url = gateway_url.rstrip("/")
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timeout
        self.worker_id = f"task-{uuid.uuid4().hex[:8]}"
        
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._client: Optional[httpx.AsyncClient] = None
        self._current_task: Optional[Dict[str, Any]] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        self.metrics = TaskWorkerMetrics()
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.gateway_url,
                timeout=self.timeout,
            )
        return self._client
    
    async def run(self):
        """主循环"""
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log(f"Starting (worker_id: {self.worker_id}, topics: {self.topics})...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # 1. 认领任务
                    task = await self._claim_task()
                    
                    if task:
                        self._current_task = task
                        
                        # 启动心跳
                        self._heartbeat_task = asyncio.create_task(
                            self._heartbeat_loop(task["id"])
                        )
                        
                        try:
                            # 2. 执行任务
                            await self._execute_task(task)
                        finally:
                            # 停止心跳
                            if self._heartbeat_task:
                                self._heartbeat_task.cancel()
                                try:
                                    await self._heartbeat_task
                                except asyncio.CancelledError:
                                    pass
                            self._current_task = None
                    else:
                        await asyncio.sleep(self.poll_interval)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    await asyncio.sleep(self.poll_interval)
        
        finally:
            self._running = False
            if self._client:
                await self._client.aclose()
            self._log("Stopped")
    
    async def shutdown(self):
        """优雅关闭"""
        self._log("Shutting down...")
        self._shutdown_event.set()
    
    async def _claim_task(self) -> Optional[Dict[str, Any]]:
        """认领任务"""
        client = await self._get_client()
        
        try:
            resp = await client.post(
                "/internal/tq/tasks/claim",
                json={
                    "topics": self.topics,
                    "worker_id": self.worker_id,
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("task")
            return None
            
        except Exception as e:
            self._log(f"Failed to claim task: {e}", level="error")
            return None
    
    async def _execute_task(self, task: Dict[str, Any]):
        """
        执行任务
        
        HTTP 状态码处理：
        - 200: Handler 正常返回（无论业务成功还是失败）→ complete
        - 503: 基础设施故障（RetryableError）→ fail + retry
        - 其他: Gateway 错误 → fail + retry
        """
        task_id = task["id"]
        topic = task["topic"]
        payload = task.get("payload", {})
        
        self.metrics.tasks_processed += 1
        self.metrics.last_task_at = datetime.utcnow().isoformat()
        
        self._log(f"Executing task {task_id} (topic={topic})")
        
        client = await self._get_client()
        
        try:
            # 调用 Gateway 执行 Handler
            resp = await client.post(
                "/internal/tq/handlers/execute",
                json={
                    "topic": topic,
                    "payload": payload,
                }
            )
            
            if resp.status_code == 200:
                # Handler 正常返回（业务成功或业务失败都在 result 里）→ complete
                data = resp.json()
                if topic == "saga.trigger":
                    self._log(f"Handler response for task {task_id}: {data}")
                await self._complete_task(task_id, data.get("result"))
                self.metrics.tasks_succeeded += 1
                
            elif resp.status_code == 503:
                # 基础设施故障 → 重试
                error = f"Retryable error: {resp.text}"
                self._log(f"Task {task_id} hit retryable error: {error}", level="error")
                await self._fail_task(task_id, error, retry=True)
                self.metrics.tasks_retried += 1
                
            else:
                # 其他 Gateway 错误 → 重试
                error = f"Gateway error: {resp.status_code}"
                self._log(f"Task {task_id} gateway error: {error}", level="error")
                await self._fail_task(task_id, error, retry=True)
                self.metrics.tasks_retried += 1
                
        except Exception as e:
            # 网络异常等 → 重试
            self._log(f"Task {task_id} execution error: {e}", level="error")
            await self._fail_task(task_id, str(e), retry=True)
            self.metrics.tasks_failed += 1
    
    async def _complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None):
        """标记任务完成"""
        client = await self._get_client()
        
        try:
            resp = await client.post(
                f"/internal/tq/tasks/{task_id}/complete",
                json={"result": result}
            )
            if resp.status_code != 200:
                self._log(
                    f"Complete failed for task {task_id}: {resp.status_code} {resp.text}",
                    level="error",
                )
                return
            try:
                payload = resp.json()
            except Exception:
                payload = None
            if payload and payload.get("success") is False:
                self._log(
                    f"Complete returned success=false for task {task_id}: {payload}",
                    level="error",
                )
                return
            self._log(f"Task {task_id} completed")
        except Exception as e:
            self._log(f"Failed to complete task: {e}", level="error")
    
    async def _fail_task(self, task_id: str, error: str, retry: bool = True):
        """标记任务失败"""
        client = await self._get_client()
        
        try:
            resp = await client.post(
                f"/internal/tq/tasks/{task_id}/fail",
                json={"error": error, "retry": retry}
            )
            if resp.status_code != 200:
                self._log(
                    f"Fail task request failed for {task_id}: {resp.status_code} {resp.text}",
                    level="error",
                )
                return
            self._log(f"Task {task_id} failed: {error}")
        except Exception as e:
            self._log(f"Failed to mark task failed: {e}", level="error")
    
    async def _heartbeat_loop(self, task_id: str):
        """心跳循环"""
        client = await self._get_client()
        
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await client.post(f"/internal/tq/tasks/{task_id}/heartbeat")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"Heartbeat error: {e}", level="error")
    
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
