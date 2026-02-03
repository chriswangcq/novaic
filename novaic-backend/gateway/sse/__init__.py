"""
SSE (Server-Sent Events) Module

Provides real-time event broadcasting for the multi-process Worker architecture.
v12: Master uses SSE to broadcast tasks to Workers.
"""

from .broadcaster import (
    WorkerBroadcaster, 
    SSEEvent, 
    get_worker_broadcaster,
    init_worker_broadcaster,
    shutdown_worker_broadcaster,
)

__all__ = [
    "WorkerBroadcaster",
    "SSEEvent",
    "get_worker_broadcaster",
    "init_worker_broadcaster",
    "shutdown_worker_broadcaster",
]
