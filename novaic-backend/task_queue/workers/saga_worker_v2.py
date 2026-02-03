"""
SagaWorker v2 - Saga 执行器

基于 Task Queue v2 架构，通过 HTTP API 与 Gateway 通信。

流程：
1. claim Saga (POST /internal/tq/sagas/claim)
2. 逐步执行 Saga 步骤
3. 每个步骤通过 TaskQueue 发布任务，等待 TaskWorker 执行
4. 更新进度并发送心跳
5. complete/fail Saga

特性：
- 多任务并发：可同时处理多个 Saga
- 超时控制：等待 Task 有超时限制
- 故障恢复：通过心跳和 idempotency_key 支持重入
"""

import asyncio
import uuid
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback
import httpx

from task_queue.saga import StepType


@dataclass
class SagaWorkerMetrics:
    """性能指标"""
    sagas_processed: int = 0
    sagas_succeeded: int = 0
    sagas_failed: int = 0
    steps_executed: int = 0
    tasks_published: int = 0
    tasks_waited: int = 0
    last_saga_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "sagas_processed": self.sagas_processed,
            "sagas_succeeded": self.sagas_succeeded,
            "sagas_failed": self.sagas_failed,
            "steps_executed": self.steps_executed,
            "tasks_published": self.tasks_published,
            "tasks_waited": self.tasks_waited,
            "last_saga_at": self.last_saga_at,
            "started_at": self.started_at,
        }


@dataclass
class RunningSaga:
    """运行中的 Saga 信息"""
    saga_id: str
    task: asyncio.Task
    heartbeat_task: asyncio.Task
    started_at: float = field(default_factory=time.time)


class SagaWorkerV2:
    """
    Saga 执行器 (v2)
    
    职责：
    1. 认领 pending 状态的 Saga
    2. 从当前步骤继续执行
    3. 每个步骤发布 Task 到 TaskQueue，等待完成
    4. 维护心跳和进度
    
    特性：
    - 多任务并发：通过 max_concurrent 控制并发数
    - 超时控制：step_timeout 控制单步超时
    """
    
    name = "saga-worker-v2"
    
    def __init__(
        self,
        saga_types: List[str],
        gateway_url: str = "http://127.0.0.1:19999",
        poll_interval: float = 0.1,
        heartbeat_interval: float = 10.0,
        step_timeout: float = 300.0,
        max_concurrent: int = 10,
    ):
        self.saga_types = saga_types
        self.gateway_url = gateway_url.rstrip("/")
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.step_timeout = step_timeout
        self.max_concurrent = max_concurrent
        self.worker_id = f"saga-{uuid.uuid4().hex[:8]}"
        
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._client: Optional[httpx.AsyncClient] = None
        
        # 多任务并发管理
        self._running_sagas: Dict[str, RunningSaga] = {}
        
        # Saga 定义（从 Gateway 获取或本地注册）
        self._definitions: Dict[str, Any] = {}
        
        self.metrics = SagaWorkerMetrics()
    
    def register_definition(self, saga_type: str, definition: Any):
        """注册 Saga 定义"""
        self._definitions[saga_type] = definition
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.gateway_url,
                timeout=self.step_timeout,
            )
        return self._client
    
    async def run(self):
        """主循环 - 支持多任务并发"""
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log(f"Starting (worker_id: {self.worker_id}, saga_types: {self.saga_types}, max_concurrent: {self.max_concurrent})...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # 1. 清理已完成的 Saga
                    await self._cleanup_finished_sagas()
                    
                    # 2. 有空位时 claim 新 Saga
                    if len(self._running_sagas) < self.max_concurrent:
                        saga = await self._claim_saga()
                        
                        if saga:
                            saga_id = saga["id"]
                            
                            # 启动心跳任务
                            heartbeat_task = asyncio.create_task(
                                self._heartbeat_loop(saga_id)
                            )
                            
                            # 启动执行任务（不等待，异步执行）
                            exec_task = asyncio.create_task(
                                self._execute_saga_with_cleanup(saga, heartbeat_task)
                            )
                            
                            self._running_sagas[saga_id] = RunningSaga(
                                saga_id=saga_id,
                                task=exec_task,
                                heartbeat_task=heartbeat_task,
                            )
                            
                            self._log(f"Started saga {saga_id} (running: {len(self._running_sagas)})")
                    
                    await asyncio.sleep(self.poll_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    await asyncio.sleep(self.poll_interval)
        
        finally:
            self._running = False
            
            # 优雅关闭：等待所有运行中的 Saga 完成
            if self._running_sagas:
                self._log(f"Waiting for {len(self._running_sagas)} running sagas to complete...")
                await self._wait_for_all_sagas(timeout=30.0)
            
            if self._client:
                await self._client.aclose()
            self._log("Stopped")
    
    async def _cleanup_finished_sagas(self):
        """清理已完成的 Saga"""
        finished = []
        for saga_id, running in self._running_sagas.items():
            if running.task.done():
                finished.append(saga_id)
                # 确保心跳任务也停止
                if not running.heartbeat_task.done():
                    running.heartbeat_task.cancel()
                    try:
                        await running.heartbeat_task
                    except asyncio.CancelledError:
                        pass
        
        for saga_id in finished:
            del self._running_sagas[saga_id]
    
    async def _wait_for_all_sagas(self, timeout: float):
        """等待所有 Saga 完成"""
        if not self._running_sagas:
            return
        
        tasks = [r.task for r in self._running_sagas.values()]
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            self._log(f"Timeout waiting for sagas, cancelling...", level="error")
            for r in self._running_sagas.values():
                r.task.cancel()
                r.heartbeat_task.cancel()
    
    async def _execute_saga_with_cleanup(self, saga: Dict[str, Any], heartbeat_task: asyncio.Task):
        """执行 Saga 并清理心跳"""
        try:
            await self._execute_saga(saga)
        finally:
            # 停止心跳
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
    
    async def shutdown(self):
        """优雅关闭"""
        self._log("Shutting down...")
        self._shutdown_event.set()
    
    async def _claim_saga(self) -> Optional[Dict[str, Any]]:
        """认领 Saga"""
        client = await self._get_client()
        
        try:
            resp = await client.post(
                "/internal/tq/sagas/claim",
                json={
                    "saga_types": self.saga_types,
                    "worker_id": self.worker_id,
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("saga")
            return None
            
        except Exception as e:
            self._log(f"Failed to claim saga: {e}", level="error")
            return None
    
    async def _execute_saga(self, saga: Dict[str, Any]):
        """执行 Saga"""
        saga_id = saga["id"]
        saga_type = saga["saga_type"]
        context = saga.get("context", {})
        current_step = saga.get("current_step", 0)
        step_results = saga.get("step_results", {})
        
        if isinstance(context, str):
            context = json.loads(context)
        if isinstance(step_results, str):
            step_results = json.loads(step_results)
        
        self.metrics.sagas_processed += 1
        self.metrics.last_saga_at = datetime.utcnow().isoformat()
        
        self._log(f"Executing saga {saga_id} (type={saga_type}, step={current_step})")
        
        # 获取 Saga 定义
        definition = self._definitions.get(saga_type)
        if not definition:
            await self._fail_saga(saga_id, f"Unknown saga type: {saga_type}")
            self.metrics.sagas_failed += 1
            return
        
        # 从当前步骤继续执行
        try:
            for step_idx in range(current_step, len(definition.steps)):
                step = definition.steps[step_idx]
                
                self._log(f"Saga {saga_id}: executing step {step_idx} ({step.name})")
                
                # 执行步骤
                result = await self._execute_step(saga_id, step, context, step_results)
                
                # 保存步骤结果
                step_results[step.name] = result
                if step.step_type == StepType.DECISION:
                    step_results["_decision"] = result
                self.metrics.steps_executed += 1
                
                # 更新进度
                await self._update_progress(saga_id, step_idx + 1, step_results)
            
            # Saga 完成
            await self._complete_saga(saga_id, step_results)
            self.metrics.sagas_succeeded += 1
            
        except Exception as e:
            self._log(f"Saga {saga_id} failed: {e}", level="error")
            traceback.print_exc()
            await self._fail_saga(saga_id, str(e))
            self.metrics.sagas_failed += 1
    
    async def _execute_step(
        self,
        saga_id: str,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行单个步骤"""
        from task_queue.saga import StepType
        
        if step.step_type == StepType.TASK:
            return await self._execute_task_step(saga_id, step, context, step_results)
        elif step.step_type == StepType.DECISION:
            return self._execute_decision_step(step, context, step_results)
        elif step.step_type == StepType.PARALLEL:
            return await self._execute_parallel_step(saga_id, step, context, step_results)
        else:
            raise ValueError(f"Unknown step type: {step.step_type}")
    
    async def _execute_task_step(
        self,
        saga_id: str,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行 Task 步骤 - 通过 TaskQueue 发布任务，等待完成"""
        # 检查条件（条件来自决策步骤结果）
        if step.condition:
            decision = step_results.get("_decision")
            if decision is None:
                prev_step_name = list(step_results.keys())[-1] if step_results else None
                decision = step_results.get(prev_step_name, {}) if prev_step_name else {}
            if not step.condition(decision):
                self._log(f"Step {step.name} skipped (condition not met)")
                return {"skipped": True}
        
        # 构建 payload
        if step.build_payload:
            import inspect
            sig = inspect.signature(step.build_payload)
            params = list(sig.parameters.keys())
            
            if len(params) == 1:
                payload = step.build_payload(context)
            elif len(params) == 2:
                decision = step_results.get("_decision")
                if decision is None:
                    prev_step_name = list(step_results.keys())[-1] if step_results else None
                    decision = step_results.get(prev_step_name, {}) if prev_step_name else {}
                payload = step.build_payload(context, decision)
            else:
                payload = step.build_payload(context)
        else:
            payload = {}
        
        client = await self._get_client()
        
        # 1. 发布任务到 TaskQueue（使用 idempotency_key 保证幂等）
        resp = await client.post(
            "/internal/tq/tasks/publish",
            json={
                "topic": step.topic,
                "payload": payload,
                "idempotency_key": f"{saga_id}-{step.name}",
            }
        )
        
        if resp.status_code != 200:
            raise Exception(f"Failed to publish task: {resp.status_code}")
        
        task_id = resp.json()["task_id"]
        self.metrics.tasks_published += 1
        
        # 2. 等待任务完成（带超时）
        return await self._wait_for_task(task_id, step.name)
    
    async def _wait_for_task(self, task_id: str, step_name: str) -> Dict[str, Any]:
        """
        等待任务完成（带超时）
        
        返回值：
        - Task done: 返回 result（可能包含 success=False 的业务失败）
        - Task failed: 返回 {"success": False, "error": "..."} 而不是抛异常
        - 超时: 抛 TimeoutError（这是基础设施问题，需要重试）
        """
        client = await self._get_client()
        start_time = time.time()
        
        self.metrics.tasks_waited += 1
        
        while True:
            # 检查超时（基础设施问题，抛异常触发 Saga 重试）
            elapsed = time.time() - start_time
            if elapsed > self.step_timeout:
                raise TimeoutError(f"Task {task_id} (step={step_name}) timed out after {elapsed:.1f}s")
            
            resp = await client.get(f"/internal/tq/tasks/{task_id}")
            
            if resp.status_code != 200:
                raise Exception(f"Failed to get task {task_id}: {resp.status_code}")
            
            task = resp.json().get("task", {})
            status = task.get("status")
            
            if status == "done":
                result = task.get("result")
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except:
                        pass
                return result or {}
            elif status == "failed":
                # Task 重试耗尽后的最终失败 → 返回结果，让 Saga 决定如何处理
                error = task.get("error", "Task exhausted retries")
                self._log(f"Task {task_id} failed after retries: {error}", level="error")
                return {"success": False, "error": error, "task_failed": True}
            
            # 继续等待
            await asyncio.sleep(0.1)
    
    def _execute_decision_step(
        self,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行决策步骤"""
        if step.decide:
            return step.decide(context, step_results)
        return {}
    
    async def _execute_parallel_step(
        self,
        saga_id: str,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """执行并行步骤 - 并行发布多个任务到 TaskQueue"""
        # 构建任务配置
        if step.build_tasks:
            import inspect
            sig = inspect.signature(step.build_tasks)
            params = list(sig.parameters.keys())
            
            if len(params) == 1:
                tasks_config = step.build_tasks(context)
            elif len(params) == 2:
                prev_step_name = list(step_results.keys())[-1] if step_results else None
                prev_result = step_results.get(prev_step_name, []) if prev_step_name else []
                tasks_config = step.build_tasks(context, prev_result)
            else:
                tasks_config = step.build_tasks(context)
        else:
            tasks_config = []
        
        if not tasks_config:
            return []
        
        client = await self._get_client()
        
        # 1. 发布所有任务
        task_ids = []
        for i, cfg in enumerate(tasks_config):
            resp = await client.post(
                "/internal/tq/tasks/publish",
                json={
                    "topic": cfg["topic"],
                    "payload": cfg.get("payload", {}),
                    "idempotency_key": f"{saga_id}-{step.name}-{i}",
                }
            )
            
            if resp.status_code == 200:
                task_ids.append(resp.json()["task_id"])
                self.metrics.tasks_published += 1
            else:
                task_ids.append(None)
        
        async def _publish_failed():
            return {"error": "Failed to publish"}

        # 2. 并行等待所有任务完成
        results = await asyncio.gather(*[
            self._wait_for_task(tid, f"{step.name}-{i}") if tid else _publish_failed()
            for i, tid in enumerate(task_ids)
        ], return_exceptions=True)
        
        return [
            {"success": False, "error": str(r)} if isinstance(r, Exception) else r
            for r in results
        ]
    
    async def _update_progress(
        self,
        saga_id: str,
        current_step: int,
        step_results: Dict[str, Any],
    ):
        """更新 Saga 进度"""
        client = await self._get_client()
        
        try:
            await client.post(
                f"/internal/tq/sagas/{saga_id}/progress",
                json={
                    "current_step": current_step,
                    "step_results": step_results,
                    "status": "running",
                }
            )
        except Exception as e:
            self._log(f"Failed to update progress: {e}", level="error")
    
    async def _complete_saga(self, saga_id: str, step_results: Dict[str, Any]):
        """标记 Saga 完成"""
        client = await self._get_client()
        
        try:
            await client.post(
                f"/internal/tq/sagas/{saga_id}/complete",
                json={"step_results": step_results}
            )
            self._log(f"Saga {saga_id} completed")
        except Exception as e:
            self._log(f"Failed to complete saga: {e}", level="error")
    
    async def _fail_saga(self, saga_id: str, error: str):
        """标记 Saga 失败"""
        client = await self._get_client()
        
        try:
            await client.post(
                f"/internal/tq/sagas/{saga_id}/fail",
                json={"error": error}
            )
            self._log(f"Saga {saga_id} failed: {error}")
        except Exception as e:
            self._log(f"Failed to mark saga failed: {e}", level="error")
    
    async def _heartbeat_loop(self, saga_id: str):
        """心跳循环"""
        client = await self._get_client()
        
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await client.post(f"/internal/tq/sagas/{saga_id}/heartbeat")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"Heartbeat error for saga {saga_id}: {e}", level="error")
    
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
    
    def get_running_count(self) -> int:
        """获取当前运行中的 Saga 数量"""
        return len(self._running_sagas)
