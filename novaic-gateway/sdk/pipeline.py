"""
Pipeline Task API
"""

from typing import Optional, Dict, Any, List
from .base import BaseAPI


class PipelineAPI(BaseAPI):
    """
    Pipeline task operations.
    
    Usage:
        task = await sdk.pipeline.claim_task(["launcher"])
        await sdk.pipeline.mark_done(task_id, result)
        await sdk.pipeline.mark_failed(task_id, error)
    """
    
    async def claim_task(
        self,
        task_types: List[str],
        task_subtypes: Optional[List[str]] = None,
        worker_id: str = "unknown",
        collector_ready_only: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Atomically claim a pending pipeline task.
        
        Args:
            task_types: List of task types to claim (e.g., ["launcher", "collector"])
            task_subtypes: Optional filter by subtypes
            worker_id: Worker identifier for tracking
            collector_ready_only: Only claim collector tasks where all async tasks done
        
        Returns:
            Claimed task dict or None if no task available
        """
        data = await self._http.post(
            f"{self.gateway_url}/internal/pipeline/tasks/claim",
            json={
                "task_types": task_types,
                "task_subtypes": task_subtypes,
                "worker_id": worker_id,
                "collector_ready_only": collector_ready_only,
            }
        )
        return data.get("task")
    
    async def create_task(
        self,
        task_type: str,
        task_subtype: str,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        expected_tasks: int = 0,
    ) -> Optional[str]:
        """
        Create a new pipeline task.
        
        Args:
            task_type: "launcher", "collector", or "async"
            task_subtype: Specific handler type (e.g., "think_launcher")
            runtime_id: Associated runtime
            stage_id: Stage identifier
            agent_id: Agent identifier
            args: Task arguments
            idempotency_key: Prevent duplicate creation
            expected_tasks: For collectors, number of async tasks to wait for
        
        Returns:
            Task ID or None if idempotency conflict
        """
        data = await self._http.post(
            f"{self.gateway_url}/internal/pipeline/tasks",
            json={
                "task_type": task_type,
                "task_subtype": task_subtype,
                "runtime_id": runtime_id,
                "stage_id": stage_id,
                "agent_id": agent_id,
                "args": args or {},
                "idempotency_key": idempotency_key,
                "expected_tasks": expected_tasks,
            }
        )
        return data.get("task_id")
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID."""
        from .exceptions import GatewayNotFoundError
        try:
            return await self._http.get(
                f"{self.gateway_url}/internal/pipeline/tasks/{task_id}"
            )
        except GatewayNotFoundError:
            return None
    
    async def get_tasks_by_stage(self, stage_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a stage."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/pipeline/tasks/by-stage/{stage_id}"
        )
        return data.get("tasks", [])
    
    async def mark_done(self, task_id: str, result: Any = None):
        """Mark a task as done with optional result."""
        await self._http.patch(
            f"{self.gateway_url}/internal/pipeline/tasks/{task_id}/done",
            json={"result": result}
        )
    
    async def mark_failed(self, task_id: str, error: str):
        """Mark a task as failed with error message."""
        await self._http.patch(
            f"{self.gateway_url}/internal/pipeline/tasks/{task_id}/failed",
            json={"error": error}
        )
    
    async def heartbeat(self, task_id: str):
        """Update heartbeat for a claimed task (prevents timeout recovery)."""
        await self._http.patch(
            f"{self.gateway_url}/internal/pipeline/tasks/{task_id}/heartbeat"
        )
    
    async def release_task(self, task_id: str):
        """
        Release a claimed task back to pending for retry.
        
        Clears claimed_at/claimed_by so task can be re-claimed.
        Used when a launcher fails but should be retried.
        """
        await self._http.patch(
            f"{self.gateway_url}/internal/pipeline/tasks/{task_id}/release"
        )
    
    async def recover_stale_tasks(
        self,
        task_type: Optional[str] = None,
        timeout_seconds: int = 60
    ) -> int:
        """
        Recover stale (timed out) tasks back to pending.
        
        Returns:
            Number of tasks recovered
        """
        data = await self._http.post(
            f"{self.gateway_url}/internal/pipeline/tasks/recover-stale",
            json={"task_type": task_type, "timeout_seconds": timeout_seconds}
        )
        return data.get("recovered_count", 0)
    
    async def increment_collector_count(self, stage_id: str) -> Dict[str, Any]:
        """
        Increment completed_tasks for a collector.
        
        Called by async tasks when they complete.
        
        Returns:
            {"expected": int, "completed": int, "all_done": bool}
        """
        return await self._http.post(
            f"{self.gateway_url}/internal/pipeline/stages/{stage_id}/increment-completed"
        )
