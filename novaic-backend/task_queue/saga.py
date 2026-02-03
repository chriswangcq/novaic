"""
Saga - 业务流程编排

架构（异步模式）：
┌─────────────────────────────────────────────────────────┐
│                    Gateway 进程                          │
│  SagaRepository (DB 操作) + API Routes                   │
│  - create(): 创建记录 + 发布 saga.run Task → 立即返回    │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Saga Worker 进程                        │
│  SagaExecutor + Worker(topics=["saga.run"])             │
│  - 认领 saga.run Task → 执行 Saga 逻辑                   │
│  - 内部通过 TaskQueueClient 发布/等待子 Task             │
└─────────────────────────────────────────────────────────┘

设计原则：
- Saga 只做编排，不执行副作用
- 所有副作用通过 Task 完成
- 崩溃后可从断点继续
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Protocol
from enum import Enum

from .exceptions import SagaError, SagaStepError


# ============================================================
# Step Types and Definitions
# ============================================================

class StepType(Enum):
    """步骤类型"""
    TASK = "task"           # 触发 Task
    PARALLEL = "parallel"   # 并行触发多个 Task
    DECISION = "decision"   # 纯计算决策
    SAGA = "saga"           # 触发另一个 Saga


@dataclass
class SagaStep:
    """Saga 步骤定义"""
    name: str
    step_type: StepType = StepType.TASK
    
    # Task 类型步骤
    topic: Optional[str] = None
    build_payload: Optional[Callable] = None
    
    # Parallel 类型步骤
    build_tasks: Optional[Callable] = None
    
    # Decision 类型步骤
    decide: Optional[Callable] = None
    
    # Saga 类型步骤
    saga_type: Optional[str] = None
    build_saga_context: Optional[Callable] = None
    
    # 条件执行
    condition: Optional[Callable] = None
    
    # 是否可选（失败不影响后续）
    optional: bool = False


@dataclass
class SagaDefinition:
    """Saga 定义"""
    name: str
    steps: List[SagaStep] = field(default_factory=list)
    
    def add_task_step(
        self,
        name: str,
        topic: str,
        build_payload: Callable,
        condition: Optional[Callable] = None,
        optional: bool = False,
    ) -> 'SagaDefinition':
        """添加 Task 步骤"""
        self.steps.append(SagaStep(
            name=name,
            step_type=StepType.TASK,
            topic=topic,
            build_payload=build_payload,
            condition=condition,
            optional=optional,
        ))
        return self
    
    def add_parallel_step(
        self,
        name: str,
        build_tasks: Callable,
        condition: Optional[Callable] = None,
        optional: bool = False,
    ) -> 'SagaDefinition':
        """添加并行步骤"""
        self.steps.append(SagaStep(
            name=name,
            step_type=StepType.PARALLEL,
            build_tasks=build_tasks,
            condition=condition,
            optional=optional,
        ))
        return self
    
    def add_decision_step(
        self,
        name: str,
        decide: Callable,
    ) -> 'SagaDefinition':
        """添加决策步骤"""
        self.steps.append(SagaStep(
            name=name,
            step_type=StepType.DECISION,
            decide=decide,
        ))
        return self
    
    def add_saga_step(
        self,
        name: str,
        saga_type: str,
        build_saga_context: Callable,
        condition: Optional[Callable] = None,
    ) -> 'SagaDefinition':
        """添加触发子 Saga 步骤"""
        self.steps.append(SagaStep(
            name=name,
            step_type=StepType.SAGA,
            saga_type=saga_type,
            build_saga_context=build_saga_context,
            condition=condition,
        ))
        return self


# ============================================================
# Protocols (接口协议)
# ============================================================

class TaskQueueProtocol(Protocol):
    """TaskQueue/TaskQueueClient 通用接口"""
    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
    ) -> str: ...
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]: ...


class SagaClientProtocol(Protocol):
    """SagaRepository/SagaClient 通用接口"""
    async def claim(self, saga_types: List[str], worker_id: str) -> Optional[Dict[str, Any]]: ...
    async def heartbeat(self, saga_id: str) -> bool: ...
    async def get(self, saga_id: str) -> Optional[Dict[str, Any]]: ...
    async def update_progress(self, saga_id: str, current_step: int, step_results: Dict[str, Any], status: str = "running"): ...
    async def mark_completed(self, saga_id: str, step_results: Dict[str, Any]): ...
    async def mark_failed(self, saga_id: str, error: str): ...
    async def start(self, saga_type: str, context: Dict[str, Any], idempotency_key: Optional[str] = None) -> str: ...


# ============================================================
# SagaRepository - Gateway 端 (DB 操作)
# ============================================================

class SagaRepository:
    """
    Gateway DB 实现位于 `gateway.task_queue.saga_repo`.
    这里仅作为薄封装，避免非 gateway 模块直接触库。
    """

    def __new__(cls, *args, **kwargs):
        from gateway.task_queue.saga_repo import SagaRepository as Impl
        return Impl(*args, **kwargs)


# ============================================================
# SagaExecutor - Worker 端 (执行逻辑)
# ============================================================

class SagaWorker:
    """
    Saga Worker - 轮询并执行 Saga
    
    使用方式 (Saga Worker 进程)：
        # 方式 1: 使用 SagaClient (HTTP)
        worker = SagaWorker(
            saga_client=SagaClient("http://gateway:8716"),
            queue=TaskQueueClient("http://gateway:8716"),
        )
        
        # 方式 2: 使用 SagaRepository (本地 DB，测试用)
        worker = SagaWorker(
            saga_client=saga_repo,
            queue=task_queue,
        )
        
        worker.register(my_saga_definition)
        await worker.run()
    """
    
    def __init__(
        self,
        saga_client: SagaClientProtocol,
        queue: TaskQueueProtocol,
        worker_id: Optional[str] = None,
        poll_interval: float = 0.1,
        heartbeat_interval: float = 10.0,
        name: str = "saga-worker",
    ):
        self.saga_client = saga_client
        self.queue = queue
        self.worker_id = worker_id or f"{name}-{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.name = name
        
        self._definitions: Dict[str, SagaDefinition] = {}
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._current_saga: Optional[Dict] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    def register(self, definition: SagaDefinition):
        """注册 Saga 定义"""
        self._definitions[definition.name] = definition
    
    @property
    def saga_types(self) -> List[str]:
        """已注册的 Saga 类型"""
        return list(self._definitions.keys())
    
    async def run(self):
        """主循环"""
        self._running = True
        self._shutdown_event.clear()
        
        # 启动心跳
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        print(f"[{self.name}] Starting (types: {self.saga_types})...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # 认领 Saga
                    saga = await self.saga_client.claim(self.saga_types, self.worker_id)
                    
                    if saga:
                        self._current_saga = saga
                        await self._execute(saga)
                        self._current_saga = None
                    else:
                        await asyncio.sleep(self.poll_interval)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[{self.name}] Error: {e}")
                    import traceback
                    traceback.print_exc()
                    await asyncio.sleep(self.poll_interval)
        finally:
            self._running = False
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            print(f"[{self.name}] Stopped")
    
    async def _heartbeat_loop(self):
        """心跳"""
        while not self._shutdown_event.is_set():
            try:
                if self._current_saga:
                    await self.saga_client.heartbeat(self._current_saga["id"])
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                pass
    
    async def shutdown(self):
        self._shutdown_event.set()
    
    async def _execute(self, saga: Dict[str, Any]):
        """执行 Saga"""
        saga_id = saga["id"]
        definition = self._definitions.get(saga["saga_type"])
        
        if not definition:
            await self.saga_client.mark_failed(saga_id, f"Unknown type: {saga['saga_type']}")
            return
        
        context = saga["context"]
        step_results = saga["step_results"]
        current_step = saga["current_step"]
        
        print(f"[{self.name}] Executing {saga_id} (type: {saga['saga_type']}, step: {current_step})")
        
        # 执行步骤
        executor = SagaExecutor(self.queue, self.saga_client, self._definitions)
        
        try:
            for i in range(current_step, len(definition.steps)):
                step = definition.steps[i]
                
                # 条件检查
                if step.condition:
                    decision = step_results.get("_decision", {})
                    if not step.condition(decision):
                        continue
                
                # 执行
                try:
                    result = await executor._execute_step(saga_id, step, context, step_results)
                    
                    if step.step_type == StepType.DECISION:
                        step_results["_decision"] = result
                    else:
                        step_results[step.name] = result
                    
                    await self.saga_client.update_progress(saga_id, i + 1, step_results)
                    
                except Exception as e:
                    if step.optional:
                        step_results[step.name] = {"error": str(e)}
                        await self.saga_client.update_progress(saga_id, i + 1, step_results)
                    else:
                        raise
            
            # 完成
            await self.saga_client.mark_completed(saga_id, step_results)
            print(f"[{self.name}] Completed {saga_id}")
            
        except Exception as e:
            await self.saga_client.mark_failed(saga_id, str(e))
            print(f"[{self.name}] Failed {saga_id}: {e}")


class SagaExecutor:
    """
    Saga 步骤执行器 (内部使用)
    """
    
    def __init__(
        self,
        queue: TaskQueueProtocol,
        saga_client: SagaClientProtocol,
        definitions: Dict[str, SagaDefinition],
    ):
        self.queue = queue
        self.saga_client = saga_client
        self._definitions = definitions
    
    async def execute(self, saga_id: str):
        """执行 Saga"""
        saga = await self.saga_client.get(saga_id)
        if not saga:
            raise SagaError(f"Saga not found: {saga_id}")
        
        if saga["status"] == "completed":
            return
        if saga["status"] == "failed":
            raise SagaError(f"Saga already failed: {saga_id}")
        
        definition = self._definitions.get(saga["saga_type"])
        if not definition:
            raise SagaError(f"Unknown saga type: {saga['saga_type']}")
        
        context = saga["context"]
        step_results = saga["step_results"]
        current_step = saga["current_step"]
        
        # 标记运行中
        await self.saga_client.update_progress(saga_id, current_step, step_results, "running")
        
        # 执行步骤
        for i in range(current_step, len(definition.steps)):
            step = definition.steps[i]
            
            try:
                # 条件检查
                if step.condition:
                    decision = step_results.get("_decision", {})
                    if not step.condition(decision):
                        continue
                
                # 执行
                result = await self._execute_step(saga_id, step, context, step_results)
                
                # 保存结果
                if step.step_type == StepType.DECISION:
                    step_results["_decision"] = result
                else:
                    step_results[step.name] = result
                
                # 更新进度
                await self.saga_client.update_progress(saga_id, i + 1, step_results)
                
            except Exception as e:
                if step.optional:
                    step_results[step.name] = {"error": str(e)}
                    await self.saga_client.update_progress(saga_id, i + 1, step_results)
                    continue
                else:
                    await self.saga_client.mark_failed(saga_id, f"Step '{step.name}': {e}")
                    raise SagaStepError(step.name, str(e), e)
        
        # 完成
        await self.saga_client.mark_completed(saga_id, step_results)
    
    async def _execute_step(
        self,
        saga_id: str,
        step: SagaStep,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Any:
        """执行单个步骤"""
        if step.step_type == StepType.TASK:
            return await self._execute_task(saga_id, step, context, step_results)
        elif step.step_type == StepType.PARALLEL:
            return await self._execute_parallel(saga_id, step, context, step_results)
        elif step.step_type == StepType.DECISION:
            return self._execute_decision(step, context, step_results)
        elif step.step_type == StepType.SAGA:
            return await self._execute_child_saga(saga_id, step, context, step_results)
        else:
            raise SagaError(f"Unknown step type: {step.step_type}")
    
    async def _execute_task(
        self,
        saga_id: str,
        step: SagaStep,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行 Task 步骤"""
        payload = self._build_payload(step.build_payload, context, step_results)
        
        task_id = await self.queue.publish(
            topic=step.topic,
            payload=payload,
            idempotency_key=f"{saga_id}-{step.name}",
        )
        
        return await self._wait_for_task(task_id)
    
    async def _execute_parallel(
        self,
        saga_id: str,
        step: SagaStep,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """执行并行步骤"""
        tasks_config = self._build_payload(step.build_tasks, context, step_results) or []
        
        task_ids = []
        for i, cfg in enumerate(tasks_config):
            task_id = await self.queue.publish(
                topic=cfg["topic"],
                payload=cfg.get("payload", {}),
                idempotency_key=f"{saga_id}-{step.name}-{i}",
            )
            task_ids.append(task_id)
        
        results = await asyncio.gather(*[
            self._wait_for_task(tid) for tid in task_ids
        ], return_exceptions=True)
        
        return [
            {"status": "failed", "error": str(r)} if isinstance(r, Exception) else r
            for r in results
        ]
    
    def _execute_decision(
        self,
        step: SagaStep,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行决策步骤"""
        if step.decide:
            return step.decide(context, step_results)
        return {}
    
    async def _execute_child_saga(
        self,
        saga_id: str,
        step: SagaStep,
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """触发子 Saga"""
        child_context = self._build_payload(step.build_saga_context, context, step_results) or context
        
        child_saga_id = await self.saga_client.start(
            saga_type=step.saga_type,
            context=child_context,
            idempotency_key=f"{saga_id}-{step.name}",
        )
        
        return await self._wait_for_saga(child_saga_id)
    
    def _build_payload(
        self,
        builder: Optional[Callable],
        context: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Any:
        """构建 payload"""
        if not builder:
            return {}
        
        import inspect
        sig = inspect.signature(builder)
        params = list(sig.parameters.keys())
        
        if len(params) >= 2:
            prev = self._get_previous_result(step_results)
            return builder(context, prev)
        return builder(context)
    
    def _get_previous_result(self, step_results: Dict[str, Any]) -> Any:
        """获取上一步结果"""
        results = {k: v for k, v in step_results.items() if not k.startswith("_")}
        if results:
            return list(results.values())[-1]
        return None
    
    async def _wait_for_task(
        self,
        task_id: str,
        poll_interval: float = 0.1,
        timeout: float = 300,
    ) -> Dict[str, Any]:
        """等待 Task 完成"""
        start = asyncio.get_event_loop().time()
        
        while True:
            task = await self.queue.get_task(task_id)
            
            if not task:
                raise SagaError(f"Task not found: {task_id}")
            
            if task["status"] == "done":
                return task.get("result") or {}
            
            if task["status"] == "failed":
                raise SagaError(f"Task failed: {task.get('error', 'Unknown')}")
            
            if asyncio.get_event_loop().time() - start > timeout:
                raise SagaError(f"Task timeout: {task_id}")
            
            await asyncio.sleep(poll_interval)
    
    async def _wait_for_saga(
        self,
        saga_id: str,
        poll_interval: float = 0.5,
        timeout: float = 600,
    ) -> Dict[str, Any]:
        """等待子 Saga 完成"""
        start = asyncio.get_event_loop().time()
        
        while True:
            saga = await self.saga_client.get(saga_id)
            
            if not saga:
                raise SagaError(f"Saga not found: {saga_id}")
            
            if saga["status"] == "completed":
                return {"saga_id": saga_id, "results": saga.get("step_results", {})}
            
            if saga["status"] == "failed":
                raise SagaError(f"Saga failed: {saga.get('error', 'Unknown')}")
            
            if asyncio.get_event_loop().time() - start > timeout:
                raise SagaError(f"Saga timeout: {saga_id}")
            
            await asyncio.sleep(poll_interval)


# ============================================================
# SagaOrchestrator - 兼容旧接口 (同步模式，用于测试)
# ============================================================

class SagaOrchestrator(SagaRepository):
    """
    Gateway DB 实现位于 `gateway.task_queue.saga_repo`.
    这里仅作为薄封装，避免非 gateway 模块直接触库。
    """

    def __new__(cls, *args, **kwargs):
        from gateway.task_queue.saga_repo import SagaOrchestrator as Impl
        return Impl(*args, **kwargs)
