"""
同步 SagaWorker - 基于多线程并发

特点：
- 纯同步代码（无 async/await）
- 使用现有的 SagaClient（同步 SDK）
- 心跳通过后台线程自动管理
- 多线程并发（支持并发处理多个 Saga）

对比异步版本：
- 代码更简单（无 asyncio 复杂性）
- 更易调试（同步执行流程）
- 性能相当（都是 I/O 密集型）
"""

import time
import uuid
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback
from queue import Queue

from task_queue.client import SagaClient, TaskQueueClient
from task_queue.heartbeat_sync import HeartbeatSync
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
    thread: threading.Thread
    heartbeat: HeartbeatSync
    started_at: float = field(default_factory=time.time)


class SagaWorkerSync:
    """
    同步 Saga 执行器
    
    优势：
    1. 代码简单 - 无需 async/await
    2. 易于调试 - 同步执行流程清晰
    3. 心跳自动 - 通过 HeartbeatSync 管理
    4. 多线程并发 - 支持同时处理多个 Saga
    """
    
    name = "saga-worker-sync"
    
    def __init__(
        self,
        saga_types: List[str],
        gateway_url: str = "http://127.0.0.1:19999",
        poll_interval: float = 0.1,
        step_timeout: float = 300.0,
        max_concurrent: int = 10,
    ):
        self.saga_types = saga_types
        self.gateway_url = gateway_url
        self.poll_interval = poll_interval
        self.step_timeout = step_timeout
        self.max_concurrent = max_concurrent
        self.worker_id = f"saga-sync-{uuid.uuid4().hex[:8]}"
        
        # 使用现有的同步 SDK
        self.saga_client = SagaClient(queue_service_url, timeout=step_timeout)  # 连接 Queue Service
        self.task_client = TaskQueueClient(queue_service_url, timeout=step_timeout)  # 连接 Queue Service
        
        self._running = False
        self._lock = threading.Lock()
        self._running_sagas: Dict[str, RunningSaga] = {}
        self._definitions: Dict[str, Any] = {}
        
        self.metrics = SagaWorkerMetrics()
    
    def register_definition(self, saga_type: str, definition: Any):
        """注册 Saga 定义"""
        self._definitions[saga_type] = definition
    
    def run(self):
        """主循环（同步）"""
        self._running = True
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log(f"Starting (worker_id: {self.worker_id}, saga_types: {self.saga_types}, max_concurrent: {self.max_concurrent})...")
        
        try:
            while self._running:
                try:
                    # 1. 清理已完成的 Saga
                    self._cleanup_finished_sagas()
                    
                    # 2. 有空位时 claim 新 Saga
                    with self._lock:
                        running_count = len(self._running_sagas)
                    
                    if running_count < self.max_concurrent:
                        saga = self._claim_saga()
                        
                        if saga:
                            self._start_saga_thread(saga)
                        else:
                            # 没 Saga 就等待
                            time.sleep(self.poll_interval)
                    else:
                        # 已满，等待
                        time.sleep(self.poll_interval)
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    time.sleep(self.poll_interval)
        
        finally:
            self._running = False
            self._wait_for_all_sagas()
            self.saga_client.close()
            self.task_client.close()
            self._log("Stopped")
    
    def shutdown(self):
        """优雅关闭"""
        self._log("Shutting down...")
        self._running = False
    
    def _claim_saga(self) -> Optional[Dict[str, Any]]:
        """认领 Saga（同步）"""
        try:
            return self.saga_client.claim(self.saga_types, self.worker_id)
        except Exception as e:
            self._log(f"Failed to claim saga: {e}", level="error")
            return None
    
    def _start_saga_thread(self, saga: Dict[str, Any]):
        """启动线程执行 Saga"""
        saga_id = saga["id"]
        
        # 创建心跳器
        def heartbeat_fn() -> bool:
            try:
                return self.saga_client.heartbeat(saga_id)
            except:
                return False
        
        heartbeat = HeartbeatSync(saga_id, heartbeat_fn, interval=10.0)
        
        # 启动线程
        thread = threading.Thread(
            target=self._execute_saga_with_heartbeat,
            args=(saga, heartbeat),
            daemon=True,
            name=f"saga-{saga_id[:8]}"
        )
        thread.start()
        
        with self._lock:
            self._running_sagas[saga_id] = RunningSaga(
                saga_id=saga_id,
                thread=thread,
                heartbeat=heartbeat,
            )
            self._log(f"Started saga {saga_id} (running: {len(self._running_sagas)})")
    
    def _cleanup_finished_sagas(self):
        """清理已完成的 Saga"""
        with self._lock:
            finished = [
                saga_id for saga_id, running in self._running_sagas.items()
                if not running.thread.is_alive()
            ]
            
            for saga_id in finished:
                running = self._running_sagas[saga_id]
                running.heartbeat.stop()
                del self._running_sagas[saga_id]
    
    def _wait_for_all_sagas(self, timeout: float = 30.0):
        """等待所有 Saga 完成"""
        with self._lock:
            sagas = list(self._running_sagas.values())
        
        if not sagas:
            return
        
        self._log(f"Waiting for {len(sagas)} running sagas to complete...")
        
        for running in sagas:
            running.thread.join(timeout=timeout / len(sagas))
            running.heartbeat.stop()
    
    def _execute_saga_with_heartbeat(self, saga: Dict[str, Any], heartbeat: HeartbeatSync):
        """执行 Saga（自动心跳）"""
        try:
            with heartbeat:
                self._execute_saga(saga)
        except Exception as e:
            self._log(f"Saga {saga['id']} execution failed: {e}", level="error")
            traceback.print_exc()
    
    def _execute_saga(self, saga: Dict[str, Any]):
        """执行 Saga（同步）"""
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
            self.saga_client.mark_failed(saga_id, f"Unknown saga type: {saga_type}")
            self.metrics.sagas_failed += 1
            return
        
        # 从当前步骤继续执行
        try:
            for step_idx in range(current_step, len(definition.steps)):
                step = definition.steps[step_idx]
                
                self._log(f"Saga {saga_id}: executing step {step_idx} ({step.name})")
                
                # 执行步骤
                result = self._execute_step(saga_id, step, context, step_results)
                
                # 保存步骤结果
                step_results[step.name] = result
                if step.step_type == StepType.DECISION:
                    step_results["_decision"] = result
                self.metrics.steps_executed += 1
                
                # 更新进度
                self._update_progress(saga_id, step_idx + 1, step_results)
            
            # Saga 完成
            self.saga_client.mark_completed(saga_id, step_results)
            self.metrics.sagas_succeeded += 1
            self._log(f"Saga {saga_id} completed")
            
        except Exception as e:
            self._log(f"Saga {saga_id} failed: {e}", level="error")
            traceback.print_exc()
            self.saga_client.mark_failed(saga_id, str(e))
            self.metrics.sagas_failed += 1
    
    def _execute_step(
        self,
        saga_id: str,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Any:
        """执行单个步骤（同步）"""
        if step.step_type == StepType.TASK:
            return self._execute_task_step(saga_id, step, context, step_results)
        elif step.step_type == StepType.DECISION:
            return self._execute_decision_step(step, context, step_results)
        elif step.step_type == StepType.PARALLEL:
            return self._execute_parallel_step(saga_id, step, context, step_results)
        else:
            raise ValueError(f"Unknown step type: {step.step_type}")
    
    def _execute_task_step(
        self,
        saga_id: str,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行 Task 步骤（同步）"""
        # 检查条件
        if step.condition:
            decision = step_results.get("_decision")
            if decision is None:
                prev_step_name = list(step_results.keys())[-1] if step_results else None
                decision = step_results.get(prev_step_name, {}) if prev_step_name else {}
            if not step.condition(decision):
                self._log(f"Step {step.name} skipped (condition not met)")
                return {"skipped": True}
        
        # 构建 payload
        payload = self._build_payload(step, context, step_results)
        
        # 1. 发布任务
        task_id = self.task_client.publish(
            topic=step.topic,
            payload=payload,
            idempotency_key=f"{saga_id}-{step.name}",
        )
        self.metrics.tasks_published += 1
        
        # 2. 等待任务完成
        return self._wait_for_task(task_id, step.name)
    
    def _wait_for_task(self, task_id: str, step_name: str) -> Dict[str, Any]:
        """等待任务完成（同步，带超时）"""
        start_time = time.time()
        self.metrics.tasks_waited += 1
        
        while True:
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed > self.step_timeout:
                raise TimeoutError(f"Task {task_id} (step={step_name}) timed out after {elapsed:.1f}s")
            
            # 查询任务状态
            task = self.task_client.get_task(task_id)
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
                error = task.get("error", "Task exhausted retries")
                self._log(f"Task {task_id} failed after retries: {error}", level="error")
                return {"success": False, "error": error, "task_failed": True}
            
            # 继续等待
            time.sleep(0.1)
    
    def _execute_decision_step(
        self,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行决策步骤（同步）"""
        if step.decide:
            return step.decide(context, step_results)
        return {}
    
    def _execute_parallel_step(
        self,
        saga_id: str,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """执行并行步骤（同步 + 多线程）"""
        # 构建任务配置
        tasks_config = self._build_parallel_tasks(step, context, step_results)
        
        if not tasks_config:
            return []
        
        # 1. 发布所有任务
        task_ids = []
        for i, cfg in enumerate(tasks_config):
            try:
                task_id = self.task_client.publish(
                    topic=cfg["topic"],
                    payload=cfg.get("payload", {}),
                    idempotency_key=f"{saga_id}-{step.name}-{i}",
                )
                task_ids.append(task_id)
                self.metrics.tasks_published += 1
            except:
                task_ids.append(None)
        
        # 2. 并行等待（使用线程池）
        results = []
        threads = []
        results_lock = threading.Lock()
        
        def wait_task(idx: int, tid: Optional[str]):
            if tid:
                try:
                    result = self._wait_for_task(tid, f"{step.name}-{idx}")
                except Exception as e:
                    result = {"success": False, "error": str(e)}
            else:
                result = {"error": "Failed to publish"}
            
            with results_lock:
                results.append((idx, result))
        
        for i, tid in enumerate(task_ids):
            t = threading.Thread(target=wait_task, args=(i, tid))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        # 按索引排序
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]
    
    def _build_payload(self, step: Any, context: Dict[str, Any], step_results: Dict[str, Any]) -> Dict[str, Any]:
        """构建步骤的 payload"""
        if step.build_payload:
            import inspect
            sig = inspect.signature(step.build_payload)
            params = list(sig.parameters.keys())
            
            if len(params) == 1:
                return step.build_payload(context)
            elif len(params) == 2:
                decision = step_results.get("_decision")
                if decision is None:
                    prev_step_name = list(step_results.keys())[-1] if step_results else None
                    decision = step_results.get(prev_step_name, {}) if prev_step_name else {}
                return step.build_payload(context, decision)
            else:
                return step.build_payload(context)
        return {}
    
    def _build_parallel_tasks(self, step: Any, context: Dict[str, Any], step_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建并行任务配置"""
        if step.build_tasks:
            import inspect
            sig = inspect.signature(step.build_tasks)
            params = list(sig.parameters.keys())
            
            if len(params) == 1:
                return step.build_tasks(context)
            elif len(params) == 2:
                prev_step_name = list(step_results.keys())[-1] if step_results else None
                prev_result = step_results.get(prev_step_name, []) if prev_step_name else []
                return step.build_tasks(context, prev_result)
            else:
                return step.build_tasks(context)
        return []
    
    def _update_progress(self, saga_id: str, current_step: int, step_results: Dict[str, Any]):
        """更新 Saga 进度（同步）"""
        try:
            self.saga_client.update_progress(saga_id, current_step, step_results)
        except Exception as e:
            self._log(f"Failed to update progress: {e}", level="error")
    
    def _log(self, msg: str, level: str = "info"):
        """日志输出"""
        timestamp = datetime.utcnow().isoformat()
        prefix = f"[{timestamp}] [{self.worker_id}]"
        
        if level == "error":
            print(f"{prefix} ❌ {msg}")
        elif level == "warning":
            print(f"{prefix} ⚠️  {msg}")
        else:
            print(f"{prefix} {msg}")
    
    def get_metrics(self) -> dict:
        """获取指标"""
        return self.metrics.to_dict()
    
    def get_running_count(self) -> int:
        """获取当前运行中的 Saga 数量"""
        with self._lock:
            return len(self._running_sagas)


# ==================== 启动脚本 ====================

def start_worker(
    saga_types: List[str] = None,
    queue_service_url: str = "http://127.0.0.1:19997",  # 改为 Queue Service
    max_concurrent: int = 10,
):
    """启动一个 SagaWorker"""
    if saga_types is None:
        saga_types = [
            "message_process",
            "runtime_start",
            "react_think",
            "react_actions",
            "runtime_complete",
        ]
    
    worker = SagaWorkerSync(saga_types, gateway_url, max_concurrent=max_concurrent)
    
    # 注册 Saga 定义
    from task_queue.sagas import get_all_saga_definitions
    for saga_def in get_all_saga_definitions():
        worker.register_definition(saga_def.name, saga_def)
    
    worker.run()


if __name__ == "__main__":
    import sys
    import os
    
    queue_service_url = os.environ.get("QUEUE_SERVICE_URL", "http://127.0.0.1:19997")
    max_concurrent = int(os.environ.get("MAX_CONCURRENT", "10"))
    
    print("=" * 60)
    print("同步 SagaWorker (多线程)")
    print("=" * 60)
    print(f"Queue Service: {queue_service_url}")
    print(f"Max Concurrent: {max_concurrent}")
    print("=" * 60)
    print()
    
    start_worker(gateway_url=gateway_url, max_concurrent=max_concurrent)
