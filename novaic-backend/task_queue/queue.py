"""
TaskQueue gateway DB 实现的薄封装。

非 gateway 代码不要直接访问 DB；实际实现位于 `gateway.task_queue.queue_db`.
"""

from gateway.task_queue.queue_db import TaskQueue

__all__ = ["TaskQueue"]
