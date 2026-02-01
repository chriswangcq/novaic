"""
Worker Repository

Handles worker_processes database operations for process management.
Tracks Worker process status, health monitoring, and auto-scaling.

v11: Created for multi-process architecture.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..database import Database


class WorkerRepository:
    """Repository for Worker process management."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== Worker Registration ====================
    
    async def register(
        self,
        worker_id: str,
        pid: int,
        max_concurrent: int = 10,
    ) -> Dict[str, Any]:
        """
        Register a new Worker process.
        
        Args:
            worker_id: Unique worker ID
            pid: Process ID
            max_concurrent: Maximum concurrent tasks
        
        Returns:
            The registered worker record
        """
        started_at = datetime.now().isoformat()
        
        await self.db.execute(
            """INSERT OR REPLACE INTO worker_processes 
               (id, pid, status, max_concurrent, started_at, last_heartbeat, current_tasks)
               VALUES (?, ?, 'running', ?, ?, ?, '[]')""",
            (worker_id, pid, max_concurrent, started_at, started_at)
        )
        await self.db.commit()
        
        return await self.get(worker_id)
    
    async def unregister(self, worker_id: str) -> bool:
        """
        Unregister a Worker process.
        
        Args:
            worker_id: Worker ID
        
        Returns:
            True if removed
        """
        cursor = await self.db.execute(
            "DELETE FROM worker_processes WHERE id = ?",
            (worker_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0
    
    # ==================== Worker Retrieval ====================
    
    async def get(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get a Worker by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM worker_processes WHERE id = ?",
            (worker_id,)
        )
        if row:
            return self._row_to_worker(row)
        return None
    
    async def get_all(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all Workers with optional status filter."""
        if status:
            rows = await self.db.fetchall(
                "SELECT * FROM worker_processes WHERE status = ? ORDER BY started_at",
                (status,)
            )
        else:
            rows = await self.db.fetchall(
                "SELECT * FROM worker_processes ORDER BY started_at"
            )
        return [self._row_to_worker(row) for row in rows]
    
    async def get_running(self) -> List[Dict[str, Any]]:
        """Get all running Workers."""
        return await self.get_all(status="running")
    
    async def count_running(self) -> int:
        """Count running Workers."""
        row = await self.db.fetchone(
            "SELECT COUNT(*) as count FROM worker_processes WHERE status = 'running'"
        )
        return row["count"] if row else 0
    
    # ==================== Heartbeat ====================
    
    async def heartbeat(
        self,
        worker_id: str,
        current_tasks: Optional[List[str]] = None,
    ) -> bool:
        """
        Update Worker heartbeat.
        
        Args:
            worker_id: Worker ID
            current_tasks: List of current task IDs
        
        Returns:
            True if updated
        """
        now = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE worker_processes 
               SET last_heartbeat = ?, current_tasks = ?
               WHERE id = ? AND status = 'running'""",
            (now, json.dumps(current_tasks or []), worker_id)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    async def get_stale_workers(
        self,
        timeout_seconds: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Get Workers that haven't sent heartbeat recently.
        
        Args:
            timeout_seconds: Heartbeat timeout threshold
        
        Returns:
            List of stale Workers
        """
        rows = await self.db.fetchall(
            """SELECT * FROM worker_processes 
               WHERE status = 'running'
               AND last_heartbeat < datetime('now', '-' || ? || ' seconds')""",
            (timeout_seconds,)
        )
        return [self._row_to_worker(row) for row in rows]
    
    # ==================== Status Updates ====================
    
    async def update_status(
        self,
        worker_id: str,
        status: str,
    ) -> bool:
        """
        Update Worker status.
        
        Args:
            worker_id: Worker ID
            status: New status (starting, running, stopping, stopped)
        
        Returns:
            True if updated
        """
        cursor = await self.db.execute(
            "UPDATE worker_processes SET status = ? WHERE id = ?",
            (status, worker_id)
        )
        await self.db.commit()
        return cursor.rowcount > 0
    
    async def set_starting(self, worker_id: str) -> bool:
        """Mark Worker as starting."""
        return await self.update_status(worker_id, "starting")
    
    async def set_running(self, worker_id: str) -> bool:
        """Mark Worker as running."""
        return await self.update_status(worker_id, "running")
    
    async def set_stopping(self, worker_id: str) -> bool:
        """Mark Worker as stopping."""
        return await self.update_status(worker_id, "stopping")
    
    async def set_stopped(self, worker_id: str) -> bool:
        """Mark Worker as stopped."""
        return await self.update_status(worker_id, "stopped")
    
    # ==================== Statistics ====================
    
    async def increment_completed(self, worker_id: str) -> bool:
        """Increment completed task counter."""
        cursor = await self.db.execute(
            """UPDATE worker_processes 
               SET tasks_completed = tasks_completed + 1
               WHERE id = ?""",
            (worker_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0
    
    async def increment_failed(self, worker_id: str) -> bool:
        """Increment failed task counter."""
        cursor = await self.db.execute(
            """UPDATE worker_processes 
               SET tasks_failed = tasks_failed + 1
               WHERE id = ?""",
            (worker_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0
    
    async def set_error(
        self,
        worker_id: str,
        error: str,
    ) -> bool:
        """Record last error for a Worker."""
        cursor = await self.db.execute(
            "UPDATE worker_processes SET last_error = ? WHERE id = ?",
            (error, worker_id)
        )
        await self.db.commit()
        return cursor.rowcount > 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall Worker statistics."""
        row = await self.db.fetchone(
            """SELECT 
               COUNT(*) as total,
               SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
               SUM(CASE WHEN status = 'stopped' THEN 1 ELSE 0 END) as stopped,
               SUM(tasks_completed) as total_completed,
               SUM(tasks_failed) as total_failed
               FROM worker_processes"""
        )
        
        if row:
            return {
                "total_workers": row["total"] or 0,
                "running_workers": row["running"] or 0,
                "stopped_workers": row["stopped"] or 0,
                "total_tasks_completed": row["total_completed"] or 0,
                "total_tasks_failed": row["total_failed"] or 0,
            }
        
        return {
            "total_workers": 0,
            "running_workers": 0,
            "stopped_workers": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
        }
    
    # ==================== Capacity ====================
    
    async def get_total_capacity(self) -> int:
        """Get total task capacity across all running Workers."""
        row = await self.db.fetchone(
            """SELECT SUM(max_concurrent) as total
               FROM worker_processes WHERE status = 'running'"""
        )
        return row["total"] or 0 if row else 0
    
    async def get_current_load(self) -> int:
        """Get current number of tasks being processed."""
        rows = await self.db.fetchall(
            """SELECT current_tasks FROM worker_processes 
               WHERE status = 'running'"""
        )
        total = 0
        for row in rows:
            try:
                tasks = json.loads(row["current_tasks"] or "[]")
                total += len(tasks)
            except json.JSONDecodeError:
                pass
        return total
    
    async def get_available_capacity(self) -> int:
        """Get available task capacity."""
        total = await self.get_total_capacity()
        current = await self.get_current_load()
        return max(0, total - current)
    
    # ==================== Cleanup ====================
    
    async def cleanup_stopped(self) -> int:
        """Remove stopped Worker records."""
        cursor = await self.db.execute(
            "DELETE FROM worker_processes WHERE status = 'stopped'"
        )
        await self.db.commit()
        return cursor.rowcount
    
    async def mark_stale_as_stopped(
        self,
        timeout_seconds: int = 120,
    ) -> int:
        """
        Mark stale Workers as stopped.
        
        Args:
            timeout_seconds: Heartbeat timeout threshold
        
        Returns:
            Number of Workers marked as stopped
        """
        cursor = await self.db.execute(
            """UPDATE worker_processes 
               SET status = 'stopped'
               WHERE status = 'running'
               AND last_heartbeat < datetime('now', '-' || ? || ' seconds')""",
            (timeout_seconds,)
        )
        await self.db.commit()
        return cursor.rowcount
    
    # ==================== Helper Methods ====================
    
    def _row_to_worker(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a Worker dict."""
        current_tasks = []
        if row.get("current_tasks"):
            try:
                current_tasks = json.loads(row["current_tasks"])
            except json.JSONDecodeError:
                pass
        
        return {
            "id": row["id"],
            "pid": row.get("pid"),
            "status": row["status"],
            "max_concurrent": row.get("max_concurrent", 10),
            "started_at": row.get("started_at"),
            "last_heartbeat": row.get("last_heartbeat"),
            "current_tasks": current_tasks,
            "tasks_completed": row.get("tasks_completed", 0),
            "tasks_failed": row.get("tasks_failed", 0),
            "last_error": row.get("last_error"),
        }
