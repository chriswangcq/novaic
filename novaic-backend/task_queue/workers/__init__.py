"""
Task Queue Workers (同步版本)

基于 Task Queue 架构的 Worker 服务：
- Watchdog: 消息监视器（发现 sending 消息，触发 Saga）
- SagaWorkerSync: Saga 执行器
- TaskWorkerSync: 任务执行器
- HealthWorkerSync: 健康监控

所有 Worker 通过 HTTP API 与 Queue Service 通信。

Usage:
    from task_queue.workers import Watchdog, SagaWorkerSync, TaskWorkerSync, HealthWorkerSync
    
    # 启动 Watchdog
    watchdog = Watchdog(gateway_url="http://127.0.0.1:19999")
    watchdog.run()
"""

from .watchdog import Watchdog, MessageWorkerV2  # MessageWorkerV2 is alias for backward compat
from .saga_worker_sync import SagaWorkerSync
from .task_worker_sync import TaskWorkerSync
from .health_worker_sync import HealthWorkerSync

# Backward compat aliases
SagaWorkerV2 = SagaWorkerSync
TaskWorkerV2 = TaskWorkerSync
HealthWorkerV2 = HealthWorkerSync

__all__ = [
    "Watchdog",
    "MessageWorkerV2",  # backward compat alias
    "SagaWorkerSync",
    "TaskWorkerSync",
    "HealthWorkerSync",
    # Backward compat aliases
    "SagaWorkerV2",
    "TaskWorkerV2",
    "HealthWorkerV2",
]
