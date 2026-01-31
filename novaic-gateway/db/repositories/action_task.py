"""
Action Task Repository

Handles all action_tasks database operations for the multi-process
Worker architecture. Supports task queue management with competitive
claiming and ID hierarchy tracking.

v11: Created for multi-process architecture.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..database import Database


class ActionTaskRepository:
    """Repository for action tasks (task queue for Workers)."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== Task Creation ====================
    
    async def create(
        self,
        id: str,
        agent_id: str,
        subagent_id: str,
        round_id: str,
        mcpcall_id: str,
        type: str,
        action: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        status: str = "pending",
    ) -> Dict[str, Any]:
        """
        Create a new action task.
        
        Args:
            id: Task ID
            agent_id: Agent ID
            subagent_id: Runtime instance ID (main-xxx or sub-xxx)
            round_id: ReACT round ID (round-1, round-2, ...)
            mcpcall_id: MCP call ID within round (mc-1, mc-2, ...)
            type: Task type (tool_call, reply, subagent)
            action: MCP tool name (for type=tool_call)
            args: Task arguments
            message_id: Associated message ID
            parent_task_id: Parent task ID (for subagent tasks)
            depends_on: List of task IDs this depends on
            status: Initial status (pending or blocked)
        
        Returns:
            The created task
        """
        idempotency_key = f"{agent_id}-{subagent_id}-{round_id}-{mcpcall_id}"
        created_at = datetime.now().isoformat()
        
        await self.db.execute(
            """INSERT INTO action_tasks 
               (id, agent_id, subagent_id, round_id, mcpcall_id, idempotency_key,
                type, action, args, message_id, parent_task_id, depends_on,
                status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                id,
                agent_id,
                subagent_id,
                round_id,
                mcpcall_id,
                idempotency_key,
                type,
                action,
                json.dumps(args or {}),
                message_id,
                parent_task_id,
                json.dumps(depends_on or []),
                status,
                created_at,
            )
        )
        await self.db.commit()
        
        return await self.get(id)
    
    # ==================== Task Retrieval ====================
    
    async def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM action_tasks WHERE id = ?",
            (task_id,)
        )
        if row:
            return self._row_to_task(row)
        return None
    
    async def get_by_idempotency_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a task by idempotency key."""
        row = await self.db.fetchone(
            "SELECT * FROM action_tasks WHERE idempotency_key = ?",
            (key,)
        )
        if row:
            return self._row_to_task(row)
        return None
    
    async def get_pending_tasks(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get pending tasks (not yet claimed)."""
        if agent_id:
            rows = await self.db.fetchall(
                """SELECT * FROM action_tasks 
                   WHERE status = 'pending' AND agent_id = ?
                   ORDER BY created_at ASC LIMIT ?""",
                (agent_id, limit)
            )
        else:
            rows = await self.db.fetchall(
                """SELECT * FROM action_tasks 
                   WHERE status = 'pending'
                   ORDER BY created_at ASC LIMIT ?""",
                (limit,)
            )
        return [self._row_to_task(row) for row in rows]
    
    async def get_tasks_by_round(
        self,
        subagent_id: str,
        round_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all tasks for a specific round."""
        rows = await self.db.fetchall(
            """SELECT * FROM action_tasks 
               WHERE subagent_id = ? AND round_id = ?
               ORDER BY created_at ASC""",
            (subagent_id, round_id)
        )
        return [self._row_to_task(row) for row in rows]
    
    async def get_tasks_by_agent(
        self,
        agent_id: str,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get tasks for an agent with optional status filter."""
        if status:
            rows = await self.db.fetchall(
                """SELECT * FROM action_tasks 
                   WHERE agent_id = ? AND status = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (agent_id, status, limit)
            )
        else:
            rows = await self.db.fetchall(
                """SELECT * FROM action_tasks 
                   WHERE agent_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (agent_id, limit)
            )
        return [self._row_to_task(row) for row in rows]
    
    async def get_child_tasks(self, parent_task_id: str) -> List[Dict[str, Any]]:
        """Get all child tasks of a parent task."""
        rows = await self.db.fetchall(
            """SELECT * FROM action_tasks 
               WHERE parent_task_id = ?
               ORDER BY created_at ASC""",
            (parent_task_id,)
        )
        return [self._row_to_task(row) for row in rows]
    
    # ==================== Task Claiming ====================
    
    async def claim(
        self,
        task_id: str,
        worker_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Atomically claim a task for a worker.
        
        Args:
            task_id: Task ID to claim
            worker_id: Worker ID claiming the task
        
        Returns:
            The claimed task if successful, None if already claimed
        """
        claimed_at = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE action_tasks 
               SET status = 'executing', claimed_by = ?, claimed_at = ?, updated_at = ?
               WHERE id = ? AND status = 'pending' AND claimed_by IS NULL""",
            (worker_id, claimed_at, claimed_at, task_id)
        )
        await self.db.commit()
        
        if cursor.rowcount > 0:
            return await self.get(task_id)
        return None
    
    async def release(self, task_id: str) -> bool:
        """
        Release a claimed task back to pending.
        
        Args:
            task_id: Task ID to release
        
        Returns:
            True if released, False otherwise
        """
        updated_at = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE action_tasks 
               SET status = 'pending', claimed_by = NULL, claimed_at = NULL, updated_at = ?
               WHERE id = ? AND status = 'executing'""",
            (updated_at, task_id)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    # ==================== Task Status Updates ====================
    
    async def update_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Update task status.
        
        Args:
            task_id: Task ID
            status: New status (done, failed, timeout, etc.)
            result: Execution result (for done status)
            error: Error message (for failed status)
        
        Returns:
            True if updated
        """
        updated_at = datetime.now().isoformat()
        executed_at = updated_at if status in ("done", "failed", "timeout") else None
        
        cursor = await self.db.execute(
            """UPDATE action_tasks 
               SET status = ?, result = ?, error = ?, executed_at = ?, updated_at = ?
               WHERE id = ?""",
            (
                status,
                json.dumps(result) if result else None,
                error,
                executed_at,
                updated_at,
                task_id,
            )
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    async def complete(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark a task as done."""
        return await self.update_status(task_id, "done", result=result)
    
    async def fail(
        self,
        task_id: str,
        error: str,
    ) -> bool:
        """Mark a task as failed."""
        return await self.update_status(task_id, "failed", error=error)
    
    async def timeout(self, task_id: str) -> bool:
        """Mark a task as timed out."""
        return await self.update_status(task_id, "timeout")
    
    async def cancel(self, task_id: str) -> bool:
        """Cancel a task."""
        return await self.update_status(task_id, "cancelled")
    
    # ==================== Round Status ====================
    
    async def is_round_complete(
        self,
        subagent_id: str,
        round_id: str,
    ) -> bool:
        """
        Check if all tasks in a round have reached final state.
        
        Args:
            subagent_id: Runtime instance ID
            round_id: Round ID
        
        Returns:
            True if all tasks are done/failed/timeout/cancelled
        """
        row = await self.db.fetchone(
            """SELECT COUNT(*) as count FROM action_tasks 
               WHERE subagent_id = ? AND round_id = ?
               AND status NOT IN ('done', 'failed', 'timeout', 'cancelled')""",
            (subagent_id, round_id)
        )
        return row["count"] == 0 if row else True
    
    async def get_round_status(
        self,
        subagent_id: str,
        round_id: str,
    ) -> Dict[str, Any]:
        """
        Get round status with all mcpcall statuses.
        
        Returns:
            {
                "subagent_id": str,
                "round_id": str,
                "status": "executing" | "waiting_results" | "completed",
                "mcpcalls": [{"id": str, "status": str}, ...],
                "all_completed": bool
            }
        """
        tasks = await self.get_tasks_by_round(subagent_id, round_id)
        
        mcpcalls = [
            {"id": t["mcpcall_id"], "status": t["status"]}
            for t in tasks
        ]
        
        all_completed = all(
            t["status"] in ("done", "failed", "timeout", "cancelled")
            for t in tasks
        )
        
        has_executing = any(t["status"] == "executing" for t in tasks)
        
        if all_completed:
            status = "completed"
        elif has_executing:
            status = "executing"
        else:
            status = "waiting_results"
        
        return {
            "subagent_id": subagent_id,
            "round_id": round_id,
            "status": status,
            "mcpcalls": mcpcalls,
            "all_completed": all_completed,
        }
    
    # ==================== Dependency Management ====================
    
    async def unblock_dependents(self, task_id: str) -> int:
        """
        Unblock tasks that depend on the completed task.
        
        Args:
            task_id: Completed task ID
        
        Returns:
            Number of tasks unblocked
        """
        updated_at = datetime.now().isoformat()
        
        # Find all blocked tasks that depend on this task
        rows = await self.db.fetchall(
            """SELECT id, depends_on FROM action_tasks 
               WHERE status = 'blocked' AND depends_on LIKE ?""",
            (f'%"{task_id}"%',)
        )
        
        unblocked = 0
        for row in rows:
            depends_on = json.loads(row["depends_on"] or "[]")
            depends_on = [d for d in depends_on if d != task_id]
            
            if not depends_on:
                # All dependencies resolved, unblock
                await self.db.execute(
                    """UPDATE action_tasks 
                       SET status = 'pending', depends_on = '[]', updated_at = ?
                       WHERE id = ?""",
                    (updated_at, row["id"])
                )
                unblocked += 1
            else:
                # Still has dependencies, update list
                await self.db.execute(
                    """UPDATE action_tasks 
                       SET depends_on = ?, updated_at = ?
                       WHERE id = ?""",
                    (json.dumps(depends_on), updated_at, row["id"])
                )
        
        await self.db.commit()
        return unblocked
    
    # ==================== Recovery ====================
    
    async def recover_stuck_tasks(
        self,
        timeout_minutes: int = 5,
    ) -> int:
        """
        Recover tasks that have been executing for too long (Worker crashed).
        
        Args:
            timeout_minutes: Timeout threshold
        
        Returns:
            Number of tasks recovered
        """
        updated_at = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE action_tasks 
               SET status = 'pending', claimed_by = NULL, claimed_at = NULL, updated_at = ?
               WHERE status = 'executing' 
               AND claimed_at < datetime('now', '-' || ? || ' minutes')""",
            (updated_at, timeout_minutes)
        )
        await self.db.commit()
        
        return cursor.rowcount
    
    async def release_worker_tasks(self, worker_id: str) -> int:
        """
        Release all tasks claimed by a specific worker.
        
        Args:
            worker_id: Worker ID
        
        Returns:
            Number of tasks released
        """
        updated_at = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE action_tasks 
               SET status = 'pending', claimed_by = NULL, claimed_at = NULL, updated_at = ?
               WHERE status = 'executing' AND claimed_by = ?""",
            (updated_at, worker_id)
        )
        await self.db.commit()
        
        return cursor.rowcount
    
    # ==================== Cleanup ====================
    
    async def cleanup_old_tasks(
        self,
        agent_id: str,
        keep_count: int = 1000,
    ) -> int:
        """Delete old completed tasks, keeping the most recent ones."""
        cursor = await self.db.execute(
            """DELETE FROM action_tasks 
               WHERE agent_id = ? 
               AND status IN ('done', 'failed', 'timeout', 'cancelled')
               AND id NOT IN (
                   SELECT id FROM action_tasks 
                   WHERE agent_id = ?
                   ORDER BY created_at DESC 
                   LIMIT ?
               )""",
            (agent_id, agent_id, keep_count)
        )
        await self.db.commit()
        return cursor.rowcount
    
    # ==================== Helper Methods ====================
    
    def _row_to_task(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a task dict."""
        args = {}
        if row.get("args"):
            try:
                args = json.loads(row["args"])
            except json.JSONDecodeError:
                pass
        
        depends_on = []
        if row.get("depends_on"):
            try:
                depends_on = json.loads(row["depends_on"])
            except json.JSONDecodeError:
                pass
        
        result = None
        if row.get("result"):
            try:
                result = json.loads(row["result"])
            except json.JSONDecodeError:
                result = row["result"]
        
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "subagent_id": row["subagent_id"],
            "round_id": row["round_id"],
            "mcpcall_id": row["mcpcall_id"],
            "idempotency_key": row["idempotency_key"],
            "type": row["type"],
            "action": row.get("action"),
            "args": args,
            "message_id": row.get("message_id"),
            "parent_task_id": row.get("parent_task_id"),
            "depends_on": depends_on,
            "status": row["status"],
            "claimed_by": row.get("claimed_by"),
            "claimed_at": row.get("claimed_at"),
            "executed_at": row.get("executed_at"),
            "result": result,
            "error": row.get("error"),
            "async_task_id": row.get("async_task_id"),
            "created_at": row["created_at"],
            "updated_at": row.get("updated_at"),
        }
