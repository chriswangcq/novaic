"""
Master Module

Core scheduler for the multi-process architecture.
Master = Monitor + Scheduler + Runtime Manager

Responsibilities:
- Monitor: Watch inbox for unread messages, create new Runtimes
- Scheduler: Drive Rounds for each active Runtime
- Runtime Manager: Manage Runtime lifecycle and state
- Broadcaster: Send SSE events to Workers

v12: Created for Master-driven architecture.
"""

from .master import Master, MasterConfig, get_master, set_master
from .monitor import Monitor
from .scheduler import Scheduler

__all__ = [
    "Master",
    "MasterConfig",
    "Monitor",
    "Scheduler",
    "get_master",
    "set_master",
]
