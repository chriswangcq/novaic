"""
Task Queue v2 - 通用任务队列基础设施

三层架构：
- Layer 1: TaskQueue - 纯粹的任务队列
- Layer 2: Idempotent Tasks - 幂等的业务操作
- Layer 3: Saga - 业务流程编排

部署模型：
- Gateway 进程: TaskQueue + SagaOrchestrator + HealthMonitor (直接操作 DB)
- Worker 进程: TaskQueueClient + Worker (通过 HTTP 访问 Gateway)

核心特性：
- 原子性任务认领 (CAS)
- 心跳 + 超时恢复
- 重试次数控制
- 与业务完全解耦
"""

from .exceptions import RetryableError, TaskNotFoundError, SagaError
from .queue import TaskQueue
from .worker import Worker, MultiTopicWorker, run_workers
from .saga import SagaOrchestrator, SagaRepository, SagaWorker, SagaExecutor, SagaDefinition, SagaStep, StepType
from .health import HealthMonitor, HealthMonitorClient
from .client import TaskQueueClient, SagaClient
from .routes import (
    create_task_queue_router, 
    create_recovery_router,
    create_handler_router,
    create_business_router,
)
from .instance import (
    init_task_queue,
    init_saga_orchestrator,
    get_task_queue,
    get_saga_orchestrator,
    set_handler_context,
    get_handler_context,
    shutdown_task_queue,
)

__all__ = [
    # Core (Gateway side)
    "TaskQueue",
    "SagaOrchestrator",  # 兼容旧接口
    "SagaRepository",    # Gateway 端 DB 操作
    "SagaDefinition",
    "SagaStep",
    "StepType",
    "HealthMonitor",
    "HealthMonitorClient",
    # API Routes (Gateway side)
    "create_task_queue_router",
    "create_recovery_router",
    "create_handler_router",
    "create_business_router",
    # Instance Management (Gateway side)
    "init_task_queue",
    "init_saga_orchestrator",
    "get_task_queue",
    "get_saga_orchestrator",
    "set_handler_context",
    "get_handler_context",
    "shutdown_task_queue",
    # Client (Worker side)
    "TaskQueueClient",
    "SagaClient",
    # Worker
    "Worker",
    "MultiTopicWorker",
    "run_workers",
    # Saga Worker (Worker side)
    "SagaWorker",
    "SagaExecutor",
    # Exceptions
    "RetryableError",
    "TaskNotFoundError",
    "SagaError",
]
