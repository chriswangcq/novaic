"""
Saga - 业务流程编排 (v3 同步版本)

架构：
┌─────────────────────────────────────────────────────────┐
│                  Saga Worker 进程                        │
│  SagaWorkerSync (同步执行)                               │
│  - 认领 Saga → 执行步骤 → 发布 Task → 等待完成           │
└─────────────────────────────────────────────────────────┘

设计原则：
- Saga 只做编排，不执行副作用
- 所有副作用通过 Task 完成
- 崩溃后可从断点继续
- 使用 runtime_id 作为幂等键，保证重试安全

v3 变更：
- 删除异步版本（SagaWorker, SagaExecutor）
- 只保留定义类（StepType, SagaStep, SagaDefinition）
- 实际执行由 saga_worker_sync.py 处理
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum


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
    
    # 并行步骤失败策略
    # - fail_fast: 任一失败则返回失败结果（默认）
    # - ignore_failures: 忽略失败，继续执行
    # - require_all: 同 fail_fast
    failure_policy: str = "fail_fast"


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
        failure_policy: str = "fail_fast",
    ) -> 'SagaDefinition':
        """添加并行步骤
        
        Args:
            failure_policy: 失败策略
                - fail_fast: 任一失败则返回失败结果（默认）
                - ignore_failures: 忽略失败，继续执行
                - require_all: 同 fail_fast
        """
        self.steps.append(SagaStep(
            name=name,
            step_type=StepType.PARALLEL,
            build_tasks=build_tasks,
            condition=condition,
            optional=optional,
            failure_policy=failure_policy,
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
