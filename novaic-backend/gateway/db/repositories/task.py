"""
Task Repository

Data access layer for agent_tasks table.
Handles four-quadrant task management (Eisenhower Matrix).

Task Status:
- pending: 待处理
- in_progress: 进行中（当前正在执行）
- completed: 已完成（一次性任务）
- ongoing: 持续进行（长期任务，有进展但未结束）
- paused: 暂停（暂时搁置）
- cancelled: 已取消

Task Type:
- one_time: 一次性任务（完成即结束）
- recurring: 周期性任务（定期执行）
- ongoing: 持续性任务（长期跟进，如「关注用户健康」）
"""

import json
from typing import Optional, List, Dict, Any

from common.utils.time import utc_now_iso


class TaskRepository:
    """Repository for agent_tasks table (四象限任务系统)."""
    
    def __init__(self, db):
        self.db = db
    
    def create(
        self,
        agent_id: str,
        title: str,
        quadrant: str,
        source: str,
        description: str = "",
        reasoning: Optional[str] = None,
        due_date: Optional[str] = None,
        context: Optional[str] = None,
        related_profile_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new task.
        
        Args:
            agent_id: Agent ID
            title: Task title
            quadrant: q1/q2/q3/q4 (Eisenhower Matrix quadrant)
            source: Task source (user_request/user_mention/inference/curiosity/learning/self_improvement)
            description: Task description
            reasoning: Why this task was created
            due_date: Due date (ISO format)
            context: Related context (e.g., user's original words)
            related_profile_keys: Related user profile keys
        
        Returns:
            Dict with success status and task info
        """
        now = utc_now_iso()
        profile_keys_json = json.dumps(related_profile_keys or [], ensure_ascii=False)
        
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            cursor = self.db.execute(
                """INSERT INTO agent_tasks 
                   (agent_id, title, description, quadrant, source, reasoning,
                    due_date, context, related_profile_keys, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (agent_id, title, description, quadrant, source, reasoning,
                 due_date, context, profile_keys_json, now, now)
            )
            task_id = cursor.lastrowid
        
        return {
            "success": True,
            "id": task_id,
            "title": title,
            "quadrant": quadrant,
            "source": source,
            "status": "pending",
        }
    
    def get(
        self,
        agent_id: str,
        task_id: int,
    ) -> Dict[str, Any]:
        """Get a single task by ID.
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
        
        Returns:
            Dict with task info or not found
        """
        row = self.db.fetchone(
            """SELECT id, agent_id, title, description, quadrant, status, source,
                      reasoning, due_date, reminder_at, context, related_profile_keys,
                      completed_at, completion_notes, created_at, updated_at
               FROM agent_tasks 
               WHERE id = ? AND agent_id = ?""",
            (task_id, agent_id)
        )
        
        if not row:
            return {"success": True, "found": False, "task": None}
        
        return {
            "success": True,
            "found": True,
            "task": self._row_to_dict(row),
        }
    
    def list_by_quadrant(
        self,
        agent_id: str,
        quadrant: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List tasks by quadrant with optional filters.
        
        Args:
            agent_id: Agent ID
            quadrant: Filter by quadrant (q1/q2/q3/q4)
            status: Filter by status (pending/in_progress/completed/cancelled)
            limit: Maximum number of tasks to return
        
        Returns:
            Dict with task list
        """
        conditions = ["agent_id = ?"]
        params: list = [agent_id]
        
        if quadrant:
            conditions.append("quadrant = ?")
            params.append(quadrant)
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where = " AND ".join(conditions)
        params.append(min(limit, 100))
        
        rows = self.db.fetchall(
            f"""SELECT id, agent_id, title, description, quadrant, status, source,
                       reasoning, due_date, reminder_at, context, related_profile_keys,
                       completed_at, completion_notes, created_at, updated_at
                FROM agent_tasks
                WHERE {where}
                ORDER BY 
                    CASE quadrant 
                        WHEN 'q1' THEN 1 
                        WHEN 'q2' THEN 2 
                        WHEN 'q3' THEN 3 
                        ELSE 4 
                    END,
                    due_date ASC NULLS LAST,
                    created_at DESC
                LIMIT ?""",
            tuple(params)
        )
        
        tasks = [self._row_to_dict(row) for row in rows]
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks),
        }
    
    def get_board_summary(
        self,
        agent_id: str,
    ) -> Dict[str, Any]:
        """Get four-quadrant task board summary for Prompt injection.
        
        Returns compact summary of active tasks grouped by quadrant.
        Only includes pending and in_progress tasks.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Dict with quadrant summaries
        """
        rows = self.db.fetchall(
            """SELECT id, title, quadrant, status, due_date, source
               FROM agent_tasks
               WHERE agent_id = ? AND status IN ('pending', 'in_progress')
               ORDER BY 
                   CASE quadrant 
                       WHEN 'q1' THEN 1 
                       WHEN 'q2' THEN 2 
                       WHEN 'q3' THEN 3 
                       ELSE 4 
                   END,
                   due_date ASC NULLS LAST,
                   created_at DESC""",
            (agent_id,)
        )
        
        # Group by quadrant
        board = {
            "q1": [],  # 紧急且重要
            "q2": [],  # 紧急不重要
            "q3": [],  # 不紧急但重要
            "q4": [],  # 不紧急不重要
        }
        
        for row in rows:
            quadrant = row["quadrant"]
            if quadrant in board:
                board[quadrant].append({
                    "id": row["id"],
                    "title": row["title"],
                    "status": row["status"],
                    "due_date": row["due_date"],
                    "source": row["source"],
                })
        
        total = sum(len(tasks) for tasks in board.values())
        
        return {
            "success": True,
            "board": board,
            "total_active": total,
            "counts": {
                "q1": len(board["q1"]),
                "q2": len(board["q2"]),
                "q3": len(board["q3"]),
                "q4": len(board["q4"]),
            },
        }
    
    def update(
        self,
        agent_id: str,
        task_id: int,
        status: Optional[str] = None,
        quadrant: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing task.
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
            status: New status
            quadrant: New quadrant
            title: New title
            description: New description
            due_date: New due date
            notes: Completion notes (for completed tasks)
        
        Returns:
            Dict with success status
        """
        now = utc_now_iso()
        
        updates = ["updated_at = ?"]
        params: list = [now]
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
            # If completing, set completed_at
            if status == "completed":
                updates.append("completed_at = ?")
                params.append(now)
        
        if quadrant is not None:
            updates.append("quadrant = ?")
            params.append(quadrant)
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date)
        
        if notes is not None:
            updates.append("completion_notes = ?")
            params.append(notes)
        
        if len(updates) == 1:  # only updated_at
            return {"success": True, "message": "No fields to update"}
        
        set_clause = ", ".join(updates)
        params.extend([task_id, agent_id])
        
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            self.db.execute(
                f"""UPDATE agent_tasks 
                    SET {set_clause}
                    WHERE id = ? AND agent_id = ?""",
                tuple(params)
            )
        
        return {"success": True, "id": task_id}
    
    def complete(
        self,
        agent_id: str,
        task_id: int,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mark a task as completed.
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
            notes: Completion notes/reflection
        
        Returns:
            Dict with success status
        """
        now = utc_now_iso()
        
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            self.db.execute(
                """UPDATE agent_tasks 
                   SET status = 'completed', completed_at = ?, 
                       completion_notes = ?, updated_at = ?
                   WHERE id = ? AND agent_id = ?""",
                (now, notes, now, task_id, agent_id)
            )
        
        return {"success": True, "id": task_id, "status": "completed"}
    
    def add_progress(
        self,
        agent_id: str,
        task_id: int,
        note: str,
        set_ongoing: bool = False,
    ) -> Dict[str, Any]:
        """Add progress note to a task (for ongoing/recurring tasks).
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
            note: Progress note
            set_ongoing: If True, also set status to 'ongoing'
        
        Returns:
            Dict with success status
        """
        now = utc_now_iso()
        
        # Get current progress notes
        row = self.db.fetchone(
            "SELECT progress_notes FROM agent_tasks WHERE id = ? AND agent_id = ?",
            (task_id, agent_id)
        )
        
        if not row:
            return {"success": False, "error": "Task not found"}
        
        try:
            progress = json.loads(row["progress_notes"] or "[]")
        except:
            progress = []
        
        # Add new progress entry
        progress.append({
            "timestamp": now,
            "note": note,
        })
        
        # Update task
        status_update = ", status = 'ongoing'" if set_ongoing else ""
        
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            self.db.execute(
                f"""UPDATE agent_tasks 
                   SET progress_notes = ?, updated_at = ?{status_update}
                   WHERE id = ? AND agent_id = ?""",
                (json.dumps(progress, ensure_ascii=False), now, task_id, agent_id)
            )
        
        return {
            "success": True, 
            "id": task_id, 
            "progress_count": len(progress),
        }
    
    def start_task(
        self,
        agent_id: str,
        task_id: int,
    ) -> Dict[str, Any]:
        """Mark a task as in_progress (starting execution).
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
        
        Returns:
            Dict with task info for execution
        """
        now = utc_now_iso()
        
        # Get task details
        task_result = self.get(agent_id, task_id)
        if not task_result.get("found"):
            return {"success": False, "error": "Task not found"}
        
        task = task_result["task"]
        
        # Update status to in_progress
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            self.db.execute(
                """UPDATE agent_tasks 
                   SET status = 'in_progress', updated_at = ?
                   WHERE id = ? AND agent_id = ?""",
                (now, task_id, agent_id)
            )
        
        task["status"] = "in_progress"
        
        return {
            "success": True,
            "task": task,
            "message": f"开始执行任务: {task['title']}",
        }
    
    def delete(
        self,
        agent_id: str,
        task_id: int,
    ) -> Dict[str, Any]:
        """Delete a task.
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
        
        Returns:
            Dict with success status
        """
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            self.db.execute(
                "DELETE FROM agent_tasks WHERE id = ? AND agent_id = ?",
                (task_id, agent_id)
            )
        
        return {"success": True, "id": task_id}
    
    def get_due_soon(
        self,
        agent_id: str,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """Get tasks due within specified hours.
        
        Args:
            agent_id: Agent ID
            hours: Number of hours to look ahead
        
        Returns:
            Dict with due soon tasks
        """
        now = utc_now_iso()
        
        rows = self.db.fetchall(
            """SELECT id, agent_id, title, description, quadrant, status, source,
                      reasoning, due_date, reminder_at, context, related_profile_keys,
                      completed_at, completion_notes, created_at, updated_at
               FROM agent_tasks
               WHERE agent_id = ? 
                 AND status IN ('pending', 'in_progress')
                 AND due_date IS NOT NULL
                 AND due_date <= datetime(?, '+' || ? || ' hours')
               ORDER BY due_date ASC""",
            (agent_id, now, hours)
        )
        
        tasks = [self._row_to_dict(row) for row in rows]
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks),
            "hours": hours,
        }
    
    def cleanup_completed(
        self,
        agent_id: str,
        keep_days: int = 30,
    ) -> Dict[str, Any]:
        """Clean up old completed tasks.
        
        Args:
            agent_id: Agent ID
            keep_days: Number of days to keep completed tasks
        
        Returns:
            Dict with cleanup result
        """
        now = utc_now_iso()
        
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            cursor = self.db.execute(
                """DELETE FROM agent_tasks 
                   WHERE agent_id = ? 
                     AND status IN ('completed', 'cancelled')
                     AND completed_at IS NOT NULL
                     AND completed_at < datetime(?, '-' || ? || ' days')""",
                (agent_id, now, keep_days)
            )
            deleted_count = cursor.rowcount
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "keep_days": keep_days,
        }
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "title": row["title"],
            "description": row["description"],
            "quadrant": row["quadrant"],
            "status": row["status"],
            "source": row["source"],
            "reasoning": row["reasoning"],
            "due_date": row["due_date"],
            "reminder_at": row["reminder_at"],
            "context": row["context"],
            "related_profile_keys": json.loads(row["related_profile_keys"] or "[]"),
            "completed_at": row["completed_at"],
            "completion_notes": row["completion_notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
