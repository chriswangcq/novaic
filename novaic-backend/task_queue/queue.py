"""
TaskQueue gateway DB 实现的薄封装。

非 gateway 代码不要直接访问 DB；实际实现位于 `queue_service.queue_db`.
"""

from queue_service.queue_db import TaskQueue

__all__ = ["TaskQueue"]
