"""
TaskWorker Base Class

Three-Task Architecture base class with heartbeat mechanism.

Task Types:
- launcher: Creates async tasks + collector (pre-logic + launch)
- collector: Waits for async tasks + creates next launcher (post-logic + trigger)
- async: Pure execution (LLM calls, tool execution)

All tasks support:
- Atomic claim via Gateway API
- Heartbeat-based liveness detection
- Automatic recovery of stale tasks
- Idempotent operations where possible
"""

import asyncio
import json
import signal
import sys
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any, Dict, List, TYPE_CHECKING
import traceback

if TYPE_CHECKING:
    from .gateway_client import GatewayClient


class RetryableError(Exception):
    """
    Exception indicating the task should be released back to pending for retry.
    
    Used by launchers when a transient failure occurs (e.g., MCP creation failed)
    that should be retried instead of marking the task as failed.
    """
    pass


@dataclass
class WorkerMetrics:
    """Metrics for monitoring worker performance."""
    claimed: int = 0
    processed: int = 0
    failed: int = 0
    total_process_time_ms: float = 0.0
    last_claim_at: Optional[str] = None
    last_process_at: Optional[str] = None
    started_at: Optional[str] = None
    
    @property
    def avg_process_time_ms(self) -> float:
        if self.processed == 0:
            return 0.0
        return self.total_process_time_ms / self.processed
    
    def to_dict(self) -> dict:
        return {
            "claimed": self.claimed,
            "processed": self.processed,
            "failed": self.failed,
            "avg_process_time_ms": round(self.avg_process_time_ms, 2),
            "last_claim_at": self.last_claim_at,
            "last_process_at": self.last_process_at,
            "started_at": self.started_at,
        }


class TaskWorker(ABC):
    """
    Base class for all task workers in the three-task architecture.
    
    Uses GatewayClient for all database operations (no direct DB access).
    
    Subclasses must implement:
    - get_task_types(): Return list of task_type values to claim
    - get_task_subtypes(): Return list of subtypes or None for all
    - process(): Process the claimed task
    
    Optional overrides:
    - on_success(): Called after successful processing
    - on_failure(): Called after failed processing
    """
    
    # Worker configuration (override in subclass)
    name: str = "task-worker"
    poll_interval: float = 0.1  # seconds between polls when idle
    heartbeat_interval: float = 10.0  # seconds between heartbeats
    claim_timeout_seconds: int = 60  # seconds before task considered stale
    
    def __init__(self, client: 'GatewayClient', config: Optional[Dict[str, Any]] = None):
        """
        Initialize the worker.
        
        Args:
            client: GatewayClient for API calls
            config: Optional configuration overrides
        """
        self.client = client
        self.config = config or {}
        
        # Generate worker ID
        self.worker_id = self.config.get("worker_id") or f"{self.name}-{uuid.uuid4().hex[:8]}"
        
        # Apply config overrides
        if "poll_interval" in self.config:
            self.poll_interval = self.config["poll_interval"]
        if "heartbeat_interval" in self.config:
            self.heartbeat_interval = self.config["heartbeat_interval"]
        if "claim_timeout_seconds" in self.config:
            self.claim_timeout_seconds = self.config["claim_timeout_seconds"]
        
        # Gateway URL
        self.gateway_url = client.gateway_url
        
        # Runtime state
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._current_task: Optional[dict] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = WorkerMetrics()
    
    # ==================== Abstract Methods ====================
    
    @abstractmethod
    def get_task_types(self) -> List[str]:
        """
        Return list of task_type values this worker handles.
        
        E.g., ['launcher'] for LauncherWorker, ['async'] for ExecutorWorker
        """
        pass
    
    @abstractmethod
    def get_task_subtypes(self) -> Optional[List[str]]:
        """
        Return list of task_subtype values this worker handles.
        
        Return None to handle all subtypes of the task_type.
        E.g., ['think'] for ThinkerWorker, ['tool_call'] for ExecutorWorker
        """
        pass
    
    @abstractmethod
    async def process(self, task: dict) -> Any:
        """
        Process a claimed task.
        
        Args:
            task: The claimed task dict
            
        Returns:
            Result of processing (passed to on_success)
            
        Raises:
            Exception: On failure (passed to on_failure)
        """
        pass
    
    # ==================== Claim Logic ====================
    
    async def claim(self) -> Optional[dict]:
        """
        Atomically claim one task via Gateway API.
        
        Filters by task_type and optionally task_subtype.
        """
        task_types = self.get_task_types()
        task_subtypes = self.get_task_subtypes()
        
        # For collector, only claim when all tasks done
        collector_ready_only = "collector" in task_types
        
        return await self.client.claim_task(
            task_types=task_types,
            task_subtypes=task_subtypes,
            worker_id=self.worker_id,
            collector_ready_only=collector_ready_only,
        )
    
    # ==================== Success/Failure Handlers ====================
    
    async def on_success(self, task: dict, result: Any):
        """
        Called after successful processing.
        
        Default: Marks task as done with result via Gateway API.
        """
        task_id = task.get("id")
        await self.client.mark_task_done(task_id, result)
        self._log(f"Task {task_id} completed")
    
    async def on_failure(self, task: dict, error: Exception):
        """
        Called after failed processing.
        
        - RetryableError: Release task back to pending for retry.
        - Other errors: Mark task as failed.
        """
        task_id = task.get("id")
        
        if isinstance(error, RetryableError):
            # Release task back to pending for retry
            await self.client.release_task(task_id)
            self._log(f"Task {task_id} released for retry: {error}", level="warning")
        else:
            # Mark task as permanently failed
            await self.client.mark_task_failed(task_id, str(error))
            self._log(f"Task {task_id} failed: {error}", level="error")
    
    # ==================== Heartbeat ====================
    
    async def _heartbeat_loop(self):
        """Background task to update heartbeat for current task."""
        while not self._shutdown_event.is_set():
            try:
                if self._current_task:
                    task_id = self._current_task.get("id")
                    await self.client.update_heartbeat(task_id)
                
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"Heartbeat error: {e}", level="error")
                await asyncio.sleep(self.heartbeat_interval)
    
    # ==================== Main Loop ====================
    
    async def run(self):
        """
        Main worker loop.
        
        Polls for work, claims tasks atomically, processes them with heartbeat.
        Handles graceful shutdown on SIGTERM/SIGINT.
        """
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        # Setup signal handlers
        self._setup_signals()
        
        # Start heartbeat background task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        self._log(f"Starting (worker_id: {self.worker_id})...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # Try to claim work
                    task = await self.claim()
                    
                    if task:
                        self._current_task = task
                        self.metrics.claimed += 1
                        self.metrics.last_claim_at = datetime.utcnow().isoformat()
                        
                        # Process
                        await self._process_task(task)
                        
                        self._current_task = None
                    else:
                        # No work, sleep
                        await asyncio.sleep(self.poll_interval)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    await asyncio.sleep(self.poll_interval)
        
        finally:
            self._running = False
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            self._log("Stopped")
    
    async def _process_task(self, task: dict):
        """Process a single task with timing and error handling."""
        start_time = time.time()
        task_id = task.get("id")
        
        try:
            result = await self.process(task)
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics.processed += 1
            self.metrics.total_process_time_ms += elapsed_ms
            self.metrics.last_process_at = datetime.utcnow().isoformat()
            
            await self.on_success(task, result)
            
        except Exception as e:
            self.metrics.failed += 1
            self._log(f"Process failed for {task_id}: {e}", level="error")
            traceback.print_exc()
            
            try:
                await self.on_failure(task, e)
            except Exception as e2:
                self._log(f"on_failure also failed: {e2}", level="error")
    
    # ==================== Shutdown ====================
    
    def _setup_signals(self):
        """Setup signal handlers for graceful shutdown."""
        if sys.platform == "win32":
            return  # Windows doesn't support these signals well
        
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
    
    async def shutdown(self):
        """Initiate graceful shutdown."""
        self._log("Shutdown requested...")
        self._shutdown_event.set()
    
    # ==================== Utilities ====================
    
    def _log(self, message: str, level: str = "info"):
        """Log a message with worker name prefix."""
        prefix = f"[{self.name}]"
        if level == "error":
            print(f"{prefix} ERROR: {message}")
        else:
            print(f"{prefix} {message}")
    
    @property
    def is_running(self) -> bool:
        """Whether the worker is currently running."""
        return self._running
    
    def get_status(self) -> dict:
        """Get current worker status for monitoring."""
        return {
            "name": self.name,
            "worker_id": self.worker_id,
            "running": self._running,
            "has_current_task": self._current_task is not None,
            "current_task_id": self._current_task.get("id") if self._current_task else None,
            "metrics": self.metrics.to_dict(),
        }
    
    # ==================== Task Creation Helpers ====================
    
    async def create_task(
        self,
        task_type: str,
        task_subtype: str,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: Optional[dict] = None,
        idempotency_key: Optional[str] = None,
        expected_tasks: int = 0,
    ) -> Optional[str]:
        """
        Create a new pipeline task via Gateway API.
        
        Returns task_id if created, None if idempotency conflict.
        """
        return await self.client.create_task(
            task_type=task_type,
            task_subtype=task_subtype,
            runtime_id=runtime_id,
            stage_id=stage_id,
            agent_id=agent_id,
            args=args,
            idempotency_key=idempotency_key,
            expected_tasks=expected_tasks,
        )
    
    async def increment_collector_count(self, stage_id: str) -> Optional[dict]:
        """
        Atomically increment completed_tasks count for a collector.
        
        Returns {"expected": int, "completed": int, "all_done": bool} or None.
        """
        result = await self.client.increment_collector_count(stage_id)
        
        if result and result.get("all_done"):
            self._log(f"Stage {stage_id} complete: {result.get('completed')}/{result.get('expected')}")
        
        return result


# ==================== Convenience Runner ====================

async def run_workers(*workers: TaskWorker):
    """
    Run multiple workers concurrently.
    
    Args:
        workers: TaskWorker instances to run
        
    Example:
        await run_workers(
            LauncherWorker(client),
            CollectorWorker(client),
            ExecutorWorker(client),
        )
    """
    tasks = [asyncio.create_task(w.run()) for w in workers]
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for w in workers:
            await w.shutdown()
        await asyncio.gather(*tasks, return_exceptions=True)
