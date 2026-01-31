"""
Process Module

Manages Worker processes for the multi-process architecture.
Handles process lifecycle, health monitoring, and auto-scaling.

v11: Created for multi-process architecture.
"""

from .manager import ProcessManager, ProcessConfig, get_process_manager

__all__ = [
    "ProcessManager",
    "ProcessConfig",
    "get_process_manager",
]
