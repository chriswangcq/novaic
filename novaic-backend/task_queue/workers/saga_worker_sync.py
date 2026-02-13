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

import os
import time
import uuid
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback
from queue import Queue
import httpx

from task_queue.client import SagaClient, TaskQueueClient
from task_queue.heartbeat_sync import HeartbeatSync
from task_queue.saga import StepType
from common.config import ServiceConfig
from common.utils.time import utc_now_iso


# 可重试的基础设施异常类型
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.NetworkError,
    ConnectionError,
    TimeoutError,
    OSError,  # 包含网络相关的 socket 错误
)

# 最大重试次数（超过后才标记 failed）
MAX_SAGA_RETRIES = 3


@dataclass
class SagaWorkerMetrics:
    """性能指标"""
    sagas_processed: int = 0
    sagas_succeeded: int = 0
    sagas_failed: int = 0
    sagas_retried: int = 0  # 因可重试错误释放回 pending 的次数
    steps_executed: int = 0
    tasks_published: int = 0
    tasks_waited: int = 0
    progress_update_failed: int = 0  # 被静默忽略的 update_progress 失败次数
    last_saga_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "sagas_processed": self.sagas_processed,
            "sagas_succeeded": self.sagas_succeeded,
            "sagas_failed": self.sagas_failed,
            "sagas_retried": self.sagas_retried,
            "steps_executed": self.steps_executed,
            "tasks_published": self.tasks_published,
            "tasks_waited": self.tasks_waited,
            "progress_update_failed": self.progress_update_failed,
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
        gateway_url: str = None,
        queue_service_url: str = None,
        poll_interval: float = None,
        step_timeout: float = None,
        max_concurrent: int = None,
    ):
        self.saga_types = saga_types
        self.gateway_url = gateway_url or ServiceConfig.GATEWAY_URL
        # Queue Service URL: 参数 > 环境变量 > 默认值
        self.queue_service_url = queue_service_url or os.environ.get("QUEUE_SERVICE_URL", ServiceConfig.QUEUE_SERVICE_URL)
        self.poll_interval = poll_interval if poll_interval is not None else ServiceConfig.POLL_INTERVAL
        self.step_timeout = step_timeout if step_timeout is not None else ServiceConfig.SAGA_STEP_TIMEOUT
        self.max_concurrent = max_concurrent if max_concurrent is not None else ServiceConfig.MAX_CONCURRENT_SAGAS
        self.worker_id = f"saga-sync-{uuid.uuid4().hex[:8]}"
        
        # 使用现有的同步 SDK
        self.saga_client = SagaClient(self.queue_service_url, timeout=step_timeout)  # 连接 Queue Service
        self.task_client = TaskQueueClient(self.queue_service_url, timeout=step_timeout)  # 连接 Queue Service
        
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
        self.metrics.started_at = utc_now_iso()
        
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
            # 输出最终指标
            self._log(f"Final metrics: processed={self.metrics.sagas_processed}, succeeded={self.metrics.sagas_succeeded}, failed={self.metrics.sagas_failed}, progress_update_failed={self.metrics.progress_update_failed}")
            if self.metrics.progress_update_failed > 0:
                self._log(f"⚠️  {self.metrics.progress_update_failed} update_progress calls were silently ignored!", level="warning")
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
        """执行 Saga（同步）- 实现"Saga 永不失败"机制"""
        saga_id = saga["id"]
        saga_type = saga["saga_type"]
        context = saga.get("context", {})
        current_step = saga.get("current_step", 0)
        step_results = saga.get("step_results", {})
        
        if isinstance(context, str):
            context = json.loads(context)
        if isinstance(step_results, str):
            step_results = json.loads(step_results)
        
        # 获取重试计数（存储在 step_results 的 _retry_count 字段）
        retry_count = step_results.get("_retry_count", 0)
        
        self.metrics.sagas_processed += 1
        self.metrics.last_saga_at = utc_now_iso()
        
        self._log(f"Executing saga {saga_id} (type={saga_type}, step={current_step}, retry={retry_count})")
        
        # 获取 Saga 定义
        definition = self._definitions.get(saga_type)
        if not definition:
            # 配置错误，不可重试，直接失败
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
                
                # 重置重试计数（步骤成功执行后）
                if "_retry_count" in step_results:
                    del step_results["_retry_count"]
                
                # 更新进度
                self._update_progress(saga_id, step_idx + 1, step_results)
            
            # Saga 完成
            self.saga_client.mark_completed(saga_id, step_results)
            self.metrics.sagas_succeeded += 1
            self._log(f"Saga {saga_id} completed")
            
        except Exception as e:
            self._handle_saga_exception(saga_id, e, step_results, retry_count)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """判断是否是可重试的基础设施错误"""
        # 检查是否是已知的可重试异常类型
        if isinstance(error, RETRYABLE_EXCEPTIONS):
            return True
        
        # 检查错误消息中是否包含可重试的关键词
        error_msg = str(error).lower()
        retryable_keywords = [
            "timeout", "connection", "network", "socket",
            "temporarily unavailable", "service unavailable",
            "too many requests", "rate limit",
        ]
        return any(keyword in error_msg for keyword in retryable_keywords)
    
    def _handle_saga_exception(
        self,
        saga_id: str,
        error: Exception,
        step_results: Dict[str, Any],
        retry_count: int,
    ):
        """处理 Saga 执行异常 - 区分可重试和不可重试错误"""
        error_str = str(error)
        
        if self._is_retryable_error(error):
            # 可重试错误
            new_retry_count = retry_count + 1
            
            if new_retry_count < MAX_SAGA_RETRIES:
                # 还可以重试，释放回 pending
                self._log(
                    f"Saga {saga_id} encountered retryable error (attempt {new_retry_count}/{MAX_SAGA_RETRIES}): {error_str}",
                    level="warning"
                )
                
                # 保存重试计数到 step_results
                step_results["_retry_count"] = new_retry_count
                step_results["_last_error"] = error_str
                
                # 先更新进度（保存重试计数）
                try:
                    self.saga_client.update_progress(
                        saga_id,
                        step_results.get("_current_step", 0),
                        step_results,
                        status="running"
                    )
                except Exception as update_err:
                    self._log(f"Failed to update progress before release: {update_err}", level="warning")
                
                # 释放回 pending
                try:
                    released = self.saga_client.release(saga_id, f"Retryable error: {error_str}")
                    if released:
                        self.metrics.sagas_retried += 1
                        self._log(f"Saga {saga_id} released back to pending for retry")
                        return
                    else:
                        self._log(f"Failed to release saga {saga_id}, marking as failed", level="warning")
                except Exception as release_err:
                    self._log(f"Failed to release saga {saga_id}: {release_err}", level="error")
            else:
                # 重试次数耗尽
                self._log(
                    f"Saga {saga_id} exhausted retries ({MAX_SAGA_RETRIES}), marking as failed: {error_str}",
                    level="error"
                )
        else:
            # 不可重试错误（如配置错误、业务逻辑错误）
            self._log(f"Saga {saga_id} failed with non-retryable error: {error_str}", level="error")
        
        # 标记失败
        traceback.print_exc()
        self.saga_client.mark_failed(saga_id, error_str)
        self.metrics.sagas_failed += 1
    
    def _execute_step(
        self,
        saga_id: str,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Any:
        """执行单个步骤（同步）- 支持 optional 步骤"""
        try:
            if step.step_type == StepType.TASK:
                result = self._execute_task_step(saga_id, step, context, step_results)
            elif step.step_type == StepType.DECISION:
                result = self._execute_decision_step(step, context, step_results)
            elif step.step_type == StepType.PARALLEL:
                result = self._execute_parallel_step(saga_id, step, context, step_results)
            else:
                raise ValueError(f"Unknown step type: {step.step_type}")
            
            return result
            
        except Exception as e:
            # 检查是否是 optional 步骤
            is_optional = getattr(step, 'optional', False)
            if is_optional:
                self._log(f"Optional step '{step.name}' failed, continuing: {e}", level="warning")
                return {"success": False, "error": str(e), "optional_skipped": True}
            # 非 optional 步骤，重新抛出异常
            raise
    
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
            # 构建条件检查上下文：合并 context 和 step_results
            # 这样条件函数可以访问 saga context（如 subagent_id）和前一步的结果
            decision = step_results.get("_decision")
            if decision is None:
                prev_step_name = list(step_results.keys())[-1] if step_results else None
                decision = step_results.get(prev_step_name, {}) if prev_step_name else {}
            
            # 合并 context 和 decision，context 优先（用于访问 subagent_id 等）
            condition_ctx = {**decision, **context, "step_results": step_results}
            
            # DEBUG: 打印条件检查信息
            self._log(f"DEBUG condition check for step {step.name}: subagent_id={condition_ctx.get('subagent_id')}, condition_result={step.condition(condition_ctx)}")
            
            if not step.condition(condition_ctx):
                self._log(f"Step {step.name} skipped (condition not met)")
                return {"skipped": True}
        
        # 构建 payload
        payload = self._build_payload(step, context, step_results)
        
        # 1. 发布任务
        # 使用业务 ID（runtime_id）作为幂等键基础
        # 如果有 round_num，也包含在幂等键中，避免不同 round 的 Task 冲突
        business_key = context.get("runtime_id") or context.get("message_id") or saga_id
        round_num = context.get("round_num")
        if round_num is not None:
            idempotency_key = f"{business_key}-round{round_num}-{step.name}"
        else:
            idempotency_key = f"{business_key}-{step.name}"
        
        task_id = self.task_client.publish(
            topic=step.topic,
            payload=payload,
            idempotency_key=idempotency_key,
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
            if task is None:
                # Task 不存在，可能还没创建，继续等待
                time.sleep(0.1)
                continue
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
        """执行决策步骤（同步）- 永不抛出异常"""
        if step.decide:
            try:
                return step.decide(context, step_results)
            except Exception as e:
                self._log(f"Decision step '{step.name}' failed: {e}", level="warning")
                return {"success": False, "error": str(e), "decision_failed": True}
        return {}
    
    def _execute_parallel_step(
        self,
        saga_id: str,
        step: Any,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行并行步骤（同步 + 多线程）
        
        返回结构化结果，让后续 DECISION 步骤可以处理部分失败情况。
        
        Returns:
            {
                "success": bool,
                "results": List[Dict],  # 各任务的结果
                "error": str,           # 失败时的错误信息（可选）
                "partial_failure": bool # 是否部分失败（可选）
            }
        """
        # 构建任务配置
        tasks_config = self._build_parallel_tasks(step, context, step_results)
        
        if not tasks_config:
            return {"success": True, "results": []}
        
        # 1. 发布所有任务
        # 使用业务 ID（runtime_id）作为幂等键
        business_key = context.get("runtime_id") or context.get("message_id") or saga_id
        task_ids = []
        for i, cfg in enumerate(tasks_config):
            try:
                task_id = self.task_client.publish(
                    topic=cfg["topic"],
                    payload=cfg.get("payload", {}),
                    idempotency_key=f"{business_key}-{step.name}-{i}",
                )
                task_ids.append(task_id)
                self.metrics.tasks_published += 1
            except Exception as e:
                task_ids.append(None)
                self._log(f"Failed to publish task {i} for step {step.name}: {e}", level="warning")
        
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
                result = {"success": False, "error": "Failed to publish"}
            
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
        sorted_results = [r[1] for r in results]
        
        # 3. 检查失败并根据策略处理
        failure_policy = getattr(step, 'failure_policy', 'fail_fast')
        
        # 检测失败的结果
        failed_results = [
            r for r in sorted_results 
            if r.get("success") is False or r.get("error")
        ]
        
        if failed_results:
            failed_count = len(failed_results)
            total_count = len(sorted_results)
            
            if failure_policy == 'ignore_failures':
                # 忽略失败，继续执行
                self._log(
                    f"Parallel step '{step.name}': {failed_count}/{total_count} tasks failed (ignored per policy)",
                    level="warning"
                )
                return {"success": True, "results": sorted_results, "failures_ignored": failed_count}
            else:
                # fail_fast 或 require_all：返回失败结果（不抛异常，让 DECISION 处理）
                error_msg = f"{failed_count}/{total_count} tasks failed"
                self._log(f"Parallel step '{step.name}': {error_msg}", level="warning")
                return {
                    "success": False,
                    "error": error_msg,
                    "results": sorted_results,
                    "partial_failure": True,
                }
        
        return {"success": True, "results": sorted_results}
    
    def _build_payload(self, step: Any, context: Dict[str, Any], step_results: Dict[str, Any]) -> Dict[str, Any]:
        """构建步骤的 payload
        
        payload builder 函数可以通过 ctx["step_results"] 访问之前步骤的结果。
        """
        if step.build_payload:
            import inspect
            sig = inspect.signature(step.build_payload)
            params = list(sig.parameters.keys())
            
            # 将 step_results 添加到 context 中，让 payload builder 可以访问
            ctx_with_results = {**context, "step_results": step_results}
            
            if len(params) == 1:
                return step.build_payload(ctx_with_results)
            elif len(params) == 2:
                decision = step_results.get("_decision")
                if decision is None:
                    prev_step_name = list(step_results.keys())[-1] if step_results else None
                    decision = step_results.get(prev_step_name, {}) if prev_step_name else {}
                return step.build_payload(ctx_with_results, decision)
            else:
                return step.build_payload(ctx_with_results)
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
            self.metrics.progress_update_failed += 1
            self._log(f"Failed to update progress (silently ignored, total={self.metrics.progress_update_failed}): {e}", level="error")
    
    def _log(self, msg: str, level: str = "info"):
        """日志输出"""
        timestamp = utc_now_iso()
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
    queue_service_url: str = None,
    gateway_url: str = None,
    max_concurrent: int = None,
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
    
    queue_service_url = os.environ.get("QUEUE_SERVICE_URL", ServiceConfig.QUEUE_SERVICE_URL)
    gateway_url = os.environ.get("GATEWAY_URL", ServiceConfig.GATEWAY_URL)
    max_concurrent = int(os.environ.get("MAX_CONCURRENT", str(ServiceConfig.MAX_CONCURRENT_SAGAS)))
    
    print("=" * 60)
    print("同步 SagaWorker (多线程)")
    print("=" * 60)
    print(f"Queue Service: {queue_service_url}")
    print(f"Gateway: {gateway_url}")
    print(f"Max Concurrent: {max_concurrent}")
    print("=" * 60)
    print()
    
    start_worker(gateway_url=gateway_url, max_concurrent=max_concurrent)
