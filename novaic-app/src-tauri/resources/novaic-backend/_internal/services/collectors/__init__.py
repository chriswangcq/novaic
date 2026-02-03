"""
Collector implementations for each stage.

Each collector:
- Handles post-logic for a stage
- Processes results from async tasks
- Triggers the next stage launcher

v18: MonitorCollector removed - replaced by event-driven MonitorWorker
"""

from .runtime import RuntimeCollector
from .think import ThinkCollector
from .actions import ActionsCollector
from .summarize import SummarizeCollector

__all__ = [
    "RuntimeCollector",
    "ThinkCollector",
    "ActionsCollector",
    "SummarizeCollector",
]
