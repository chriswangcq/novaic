"""
Process Manager

Manages Worker process lifecycle including:
- Starting/stopping Worker processes
- Health monitoring via heartbeat
- Automatic crash recovery
- Auto-scaling based on queue depth

v11: Created for multi-process architecture.
"""

import asyncio
import os
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from db import get_database
from db.repositories import WorkerRepository, ActionTaskRepository


@dataclass
class ProcessConfig:
    """Process Manager configuration."""
    
    # Worker count
    min_workers: int = 2
    max_workers: int = 5
    
    # Worker configuration
    max_concurrent_per_worker: int = 10
    
    # Gateway connection
    gateway_url: str = "http://localhost:9527"
    
    # Health check
    heartbeat_timeout: int = 60  # seconds
    health_check_interval: int = 30  # seconds
    
    # Auto-scaling
    scale_up_threshold: int = 10  # queue depth
    scale_down_threshold: int = 2  # queue depth
    scale_cooldown: int = 60  # seconds between scaling operations
    
    # Recovery
    task_timeout_minutes: int = 5
    recovery_interval: int = 60  # seconds


class WorkerProcess:
    """Represents a managed Worker process."""
    
    def __init__(
        self,
        worker_id: str,
        process: subprocess.Popen,
        started_at: datetime,
    ):
        self.worker_id = worker_id
        self.process = process
        self.started_at = started_at
        self.last_heartbeat = started_at
    
    @property
    def pid(self) -> int:
        """Process ID."""
        return self.process.pid
    
    @property
    def is_running(self) -> bool:
        """Check if process is still running."""
        return self.process.poll() is None
    
    @property
    def return_code(self) -> Optional[int]:
        """Get process return code (None if still running)."""
        return self.process.poll()


class ProcessManager:
    """
    Manages Worker processes for the multi-process architecture.
    
    Features:
    - Worker lifecycle management (start/stop)
    - Health monitoring via heartbeat
    - Automatic crash recovery
    - Auto-scaling based on queue depth
    - Graceful shutdown handling
    
    Usage:
        config = ProcessConfig(min_workers=2, max_workers=5)
        manager = ProcessManager(config)
        
        # Start manager
        await manager.start()
        
        # Manager will maintain min_workers and auto-scale as needed
        
        # Stop manager
        await manager.stop()
    """
    
    def __init__(self, config: Optional[ProcessConfig] = None):
        """
        Initialize Process Manager.
        
        Args:
            config: Process manager configuration
        """
        self.config = config or ProcessConfig()
        
        # Worker processes
        self._workers: Dict[str, WorkerProcess] = {}
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._recovery_task: Optional[asyncio.Task] = None
        self._auto_scale_task: Optional[asyncio.Task] = None
        
        # State
        self._running = False
        self._last_scale_time: Optional[datetime] = None
        
        # Repositories
        self._worker_repo: Optional[WorkerRepository] = None
        self._task_repo: Optional[ActionTaskRepository] = None
    
    @property
    def worker_repo(self) -> WorkerRepository:
        """Get WorkerRepository instance."""
        if self._worker_repo is None:
            db = get_database()
            self._worker_repo = WorkerRepository(db)
        return self._worker_repo
    
    @property
    def task_repo(self) -> ActionTaskRepository:
        """Get ActionTaskRepository instance."""
        if self._task_repo is None:
            db = get_database()
            self._task_repo = ActionTaskRepository(db)
        return self._task_repo
    
    @property
    def worker_count(self) -> int:
        """Number of managed Worker processes."""
        return len(self._workers)
    
    @property
    def running_workers(self) -> List[str]:
        """IDs of running Workers."""
        return [
            wid for wid, wp in self._workers.items()
            if wp.is_running
        ]
    
    # ==================== Lifecycle ====================
    
    async def start(self):
        """
        Start the Process Manager.
        
        - Starts minimum number of Workers
        - Begins health monitoring
        - Begins crash recovery
        - Begins auto-scaling
        
        Note: In PyInstaller frozen mode, Workers are disabled to prevent
        infinite process spawning (sys.executable points to Gateway binary).
        """
        if self._running:
            return
        
        self._running = True
        
        # Check if running as PyInstaller bundle
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            print(f"[ProcessManager] Running in PyInstaller frozen mode - subprocess Workers disabled")
            print(f"[ProcessManager] Workers will be started by Tauri (novaic-worker binary)")
            # Only start recovery task for stuck tasks cleanup
            await self._recover_stuck_tasks()
            self._recovery_task = asyncio.create_task(self._recovery_loop())
            return
        
        print(f"[ProcessManager] Starting with config: min={self.config.min_workers}, max={self.config.max_workers}")
        
        # Recover stuck tasks from previous run
        await self._recover_stuck_tasks()
        
        # Start minimum workers
        for _ in range(self.config.min_workers):
            await self.start_worker()
        
        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._recovery_task = asyncio.create_task(self._recovery_loop())
        self._auto_scale_task = asyncio.create_task(self._auto_scale_loop())
        
        print(f"[ProcessManager] Started with {self.worker_count} workers")
    
    async def stop(self):
        """
        Stop the Process Manager.
        
        - Stops all background tasks
        - Gracefully stops all Workers
        """
        if not self._running:
            return
        
        self._running = False
        print("[ProcessManager] Stopping...")
        
        # Cancel background tasks
        for task in [self._health_check_task, self._recovery_task, self._auto_scale_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Stop all workers
        worker_ids = list(self._workers.keys())
        for worker_id in worker_ids:
            await self.stop_worker(worker_id)
        
        print("[ProcessManager] Stopped")
    
    # ==================== Worker Management ====================
    
    async def start_worker(self) -> Optional[str]:
        """
        Start a new Worker process.
        
        Returns:
            Worker ID if started, None if at max capacity
        """
        # CRITICAL: Check if running as PyInstaller bundle
        # In frozen mode, sys.executable points to the Gateway binary, NOT Python!
        # Starting subprocess with sys.executable would create infinite Gateway spawning.
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            print(f"[ProcessManager] WARNING: Running in PyInstaller frozen mode - Worker subprocess disabled")
            print(f"[ProcessManager] Multi-process Workers are only supported in development mode")
            # In production (frozen), all work is done in the main process
            # This is a limitation of PyInstaller bundled apps
            return None
        
        if self.worker_count >= self.config.max_workers:
            print(f"[ProcessManager] At max workers ({self.config.max_workers}), cannot start more")
            return None
        
        # Generate worker ID
        from worker import IDGenerator
        worker_id = IDGenerator.worker_id()
        
        # Build command - run as module to support relative imports
        # NOTE: Only safe in non-frozen mode where sys.executable is Python interpreter
        python_path = sys.executable
        gateway_dir = Path(__file__).parent.parent  # novaic-gateway directory
        
        cmd = [
            python_path,
            "-m", "worker.worker",  # Run as module
            "--gateway", self.config.gateway_url,
            "--max-concurrent", str(self.config.max_concurrent_per_worker),
            "--worker-id", worker_id,
        ]
        
        try:
            # Start process with gateway directory as cwd for proper module resolution
            process = subprocess.Popen(
                cmd,
                stdout=None,  # Inherit parent's stdout
                stderr=None,  # Inherit parent's stderr
                start_new_session=True,  # Detach from parent
                cwd=str(gateway_dir),  # Set working directory to gateway root
            )
            
            # Track worker
            worker = WorkerProcess(
                worker_id=worker_id,
                process=process,
                started_at=datetime.now(),
            )
            self._workers[worker_id] = worker
            
            # Register in database
            await self.worker_repo.register(
                worker_id=worker_id,
                pid=process.pid,
                max_concurrent=self.config.max_concurrent_per_worker,
            )
            
            print(f"[ProcessManager] Started worker {worker_id} (pid={process.pid})")
            return worker_id
            
        except Exception as e:
            print(f"[ProcessManager] Failed to start worker: {e}")
            return None
    
    async def stop_worker(self, worker_id: str, graceful: bool = True) -> bool:
        """
        Stop a Worker process.
        
        Args:
            worker_id: Worker ID to stop
            graceful: If True, send SIGTERM first; if False, send SIGKILL
        
        Returns:
            True if stopped successfully
        """
        if worker_id not in self._workers:
            return False
        
        worker = self._workers[worker_id]
        
        try:
            if worker.is_running:
                if graceful:
                    # Send SIGTERM for graceful shutdown
                    worker.process.terminate()
                    
                    # Wait for graceful shutdown (up to 10 seconds)
                    try:
                        worker.process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        # Force kill if doesn't stop
                        worker.process.kill()
                        worker.process.wait()
                else:
                    worker.process.kill()
                    worker.process.wait()
            
            # Release worker's tasks
            released = await self.task_repo.release_worker_tasks(worker_id)
            if released > 0:
                print(f"[ProcessManager] Released {released} tasks from worker {worker_id}")
            
            # Update database
            await self.worker_repo.set_stopped(worker_id)
            
            # Remove from tracking
            del self._workers[worker_id]
            
            print(f"[ProcessManager] Stopped worker {worker_id}")
            return True
            
        except Exception as e:
            print(f"[ProcessManager] Error stopping worker {worker_id}: {e}")
            return False
    
    async def restart_worker(self, worker_id: str) -> Optional[str]:
        """
        Restart a Worker process.
        
        Args:
            worker_id: Worker ID to restart
        
        Returns:
            New Worker ID
        """
        await self.stop_worker(worker_id)
        return await self.start_worker()
    
    # ==================== Health Monitoring ====================
    
    async def _health_check_loop(self):
        """Background task for health checking."""
        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._check_worker_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ProcessManager] Health check error: {e}")
    
    async def _check_worker_health(self):
        """Check health of all Workers."""
        now = datetime.now()
        stale_workers = []
        crashed_workers = []
        
        for worker_id, worker in list(self._workers.items()):
            # Check if process crashed
            if not worker.is_running:
                crashed_workers.append(worker_id)
                continue
            
            # Check heartbeat (from database)
            db_worker = await self.worker_repo.get(worker_id)
            if db_worker:
                last_heartbeat = db_worker.get("last_heartbeat")
                if last_heartbeat:
                    heartbeat_time = datetime.fromisoformat(last_heartbeat)
                    elapsed = (now - heartbeat_time).total_seconds()
                    
                    if elapsed > self.config.heartbeat_timeout:
                        stale_workers.append(worker_id)
        
        # Handle crashed workers
        for worker_id in crashed_workers:
            print(f"[ProcessManager] Worker {worker_id} crashed, restarting...")
            await self.restart_worker(worker_id)
        
        # Handle stale workers
        for worker_id in stale_workers:
            print(f"[ProcessManager] Worker {worker_id} heartbeat timeout, restarting...")
            await self.restart_worker(worker_id)
        
        # Ensure minimum workers
        while self.worker_count < self.config.min_workers:
            print(f"[ProcessManager] Below minimum workers, starting new worker...")
            await self.start_worker()
    
    # ==================== Recovery ====================
    
    async def _recovery_loop(self):
        """Background task for task recovery."""
        while self._running:
            try:
                await asyncio.sleep(self.config.recovery_interval)
                await self._recover_stuck_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ProcessManager] Recovery error: {e}")
    
    async def _recover_stuck_tasks(self):
        """Recover tasks that have been executing for too long."""
        # Recover stuck action_tasks
        recovered = await self.task_repo.recover_stuck_tasks(
            timeout_minutes=self.config.task_timeout_minutes
        )
        
        if recovered > 0:
            print(f"[ProcessManager] Recovered {recovered} stuck tasks")
        
        # Mark stale MCP executions as timeout
        from db.repositories import MCPExecutionRepository
        db = get_database()
        mcp_repo = MCPExecutionRepository(db)
        
        timed_out = await mcp_repo.mark_stale_as_timeout(
            timeout_minutes=self.config.task_timeout_minutes * 2
        )
        
        if timed_out > 0:
            print(f"[ProcessManager] Marked {timed_out} MCP executions as timeout")
    
    # ==================== Auto-scaling ====================
    
    async def _auto_scale_loop(self):
        """Background task for auto-scaling."""
        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._check_auto_scale()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ProcessManager] Auto-scale error: {e}")
    
    async def _check_auto_scale(self):
        """Check if scaling is needed."""
        # Check cooldown
        if self._last_scale_time:
            elapsed = (datetime.now() - self._last_scale_time).total_seconds()
            if elapsed < self.config.scale_cooldown:
                return
        
        # Get queue depth
        pending_tasks = await self.task_repo.get_pending_tasks(limit=100)
        queue_depth = len(pending_tasks)
        
        # Get current capacity
        capacity = await self.worker_repo.get_available_capacity()
        
        # Scale up if queue is deep and not at max
        if queue_depth > self.config.scale_up_threshold and self.worker_count < self.config.max_workers:
            print(f"[ProcessManager] Queue depth={queue_depth}, scaling up...")
            await self.start_worker()
            self._last_scale_time = datetime.now()
            return
        
        # Scale down if queue is shallow and above minimum
        if queue_depth < self.config.scale_down_threshold and self.worker_count > self.config.min_workers:
            # Find least busy worker to stop
            workers = await self.worker_repo.get_running()
            
            for w in workers:
                if not w.get("current_tasks"):
                    print(f"[ProcessManager] Queue depth={queue_depth}, scaling down...")
                    await self.stop_worker(w["id"])
                    self._last_scale_time = datetime.now()
                    break
    
    # ==================== Status ====================
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Process Manager status."""
        stats = await self.worker_repo.get_statistics()
        
        workers = []
        for worker_id, worker in self._workers.items():
            db_worker = await self.worker_repo.get(worker_id)
            workers.append({
                "id": worker_id,
                "pid": worker.pid,
                "is_running": worker.is_running,
                "started_at": worker.started_at.isoformat(),
                "db_status": db_worker.get("status") if db_worker else "unknown",
                "current_tasks": db_worker.get("current_tasks", []) if db_worker else [],
            })
        
        return {
            "running": self._running,
            "config": {
                "min_workers": self.config.min_workers,
                "max_workers": self.config.max_workers,
                "max_concurrent_per_worker": self.config.max_concurrent_per_worker,
            },
            "workers": workers,
            "statistics": stats,
        }


# Singleton instance
_process_manager: Optional[ProcessManager] = None


def get_process_manager() -> ProcessManager:
    """Get the global ProcessManager instance."""
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager


async def init_process_manager(config: Optional[ProcessConfig] = None) -> ProcessManager:
    """Initialize and start the global ProcessManager."""
    global _process_manager
    _process_manager = ProcessManager(config)
    await _process_manager.start()
    return _process_manager


async def shutdown_process_manager():
    """Shutdown the global ProcessManager."""
    global _process_manager
    if _process_manager:
        await _process_manager.stop()
        _process_manager = None
