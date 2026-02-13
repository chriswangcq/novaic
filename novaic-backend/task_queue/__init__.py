"""
Task Queue v3 - 通用任务队列基础设施 (同步版本)

三层架构：
- Layer 1: TaskQueue - 纯粹的任务队列
- Layer 2: Idempotent Tasks - 幂等的业务操作
- Layer 3: Saga - 业务流程编排

部署模型：
- Gateway 进程: TaskQueue + SagaRepository (直接操作 DB)
- Worker 进程: TaskQueueClient + SagaWorkerSync (通过 HTTP 访问 Gateway)

核心特性：
- 原子性任务认领 (CAS)
- 心跳 + 超时恢复
- 重试次数控制
- 使用 runtime_id 作为幂等键，保证重试安全
- 与业务完全解耦

v3 变更：
- 删除异步版本（SagaWorker, SagaExecutor）
- 使用同步版本 SagaWorkerSync
"""

from .exceptions import RetryableError, TaskNotFoundError, SagaError
from .client import TaskQueueClient, SagaClient
from .saga import SagaDefinition, SagaStep, StepType

# Gateway 端模块（可选导入，避免强制依赖 aiohttp）
try:
    from .queue import TaskQueue
    _GATEWAY_MODULES_AVAILABLE = True
except ImportError:
    _GATEWAY_MODULES_AVAILABLE = False
    # Worker 端不需要这些模块
    TaskQueue = None

if _GATEWAY_MODULES_AVAILABLE:
    try:
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
    except ImportError:
        pass
else:
    create_task_queue_router = None
    create_recovery_router = None
    create_handler_router = None
    create_business_router = None
    init_task_queue = None
    init_saga_orchestrator = None
    get_task_queue = None
    get_saga_orchestrator = None
    set_handler_context = None
    get_handler_context = None
    shutdown_task_queue = None

__all__ = [
    # Core (Gateway side)
    "TaskQueue",
    "SagaDefinition",
    "SagaStep",
    "StepType",
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
    # Exceptions
    "RetryableError",
    "TaskNotFoundError",
    "SagaError",
]
