"""
Three-Task Architecture

A robust, stateless task processing system with:
- LauncherTask: Pre-logic + create executor tasks + create collector
- CollectorTask: Wait for results + post-logic + trigger next stage
- ExecutorTask: Pure execution (LLM calls, tool execution)

All database operations go through GatewayClient (HTTP API).
Services can run independently from Gateway.

Usage:
    from services import GatewayClient, LauncherWorker, CollectorWorker, ExecutorWorker
    from services import run_workers
    
    # Create client
    client = GatewayClient(gateway_url="http://127.0.0.1:19999")
    
    # Register handlers
    from services.launchers import *
    from services.collectors import *
    from services.executors import *
    
    # Run workers
    await run_workers(
        LauncherWorker(client),
        CollectorWorker(client),
        ExecutorWorker(client),
    )
"""

from .gateway_client import GatewayClient
from .base import TaskWorker, WorkerMetrics, run_workers
from .launcher_worker import LauncherWorker, BaseLauncher
from .collector_worker import CollectorWorker, BaseCollector
from .executor_worker import ExecutorWorker, BaseExecutor
from .health_monitor import HealthMonitor
from .monitor_worker import MonitorWorker  # v18: Event-driven monitor

# Register all handlers by importing them
from . import launchers
from . import collectors
from . import executors

__all__ = [
    # Client
    "GatewayClient",
    
    # Base classes
    "TaskWorker",
    "WorkerMetrics",
    "run_workers",
    
    # Workers
    "LauncherWorker",
    "CollectorWorker", 
    "ExecutorWorker",
    "HealthMonitor",
    "MonitorWorker",  # v18
    
    # Handler base classes
    "BaseLauncher",
    "BaseCollector",
    "BaseExecutor",
]
