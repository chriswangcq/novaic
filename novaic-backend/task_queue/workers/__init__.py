"""
Task Queue v2 Workers

基于 Task Queue v2 架构的 Worker 服务：
- Watchdog: 消息监视器（发现 sending 消息，触发 Saga）
- SagaWorkerV2: Saga 执行器
- TaskWorkerV2: 任务执行器
- HealthWorkerV2: 健康监控

所有 Worker 通过 HTTP API 与 Gateway 通信，不直接访问数据库。

Usage:
    from task_queue.workers import Watchdog, SagaWorkerV2, TaskWorkerV2, HealthWorkerV2
    
    # 启动 Watchdog
    watchdog = Watchdog(gateway_url="http://127.0.0.1:19999")
    await watchdog.run()
"""

from .watchdog import Watchdog, MessageWorkerV2  # MessageWorkerV2 is alias for backward compat
from .saga_worker_v2 import SagaWorkerV2
from .task_worker_v2 import TaskWorkerV2
from .health_worker_v2 import HealthWorkerV2

__all__ = [
    "Watchdog",
    "MessageWorkerV2",  # backward compat alias
    "SagaWorkerV2",
    "TaskWorkerV2",
    "HealthWorkerV2",
]
