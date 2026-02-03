"""
ExecutorWorker

Handles 'async' type tasks (execution tasks).

Executor tasks are responsible for:
1. Pure execution (LLM calls, tool execution)
2. Updating the collector's completed_tasks count when done

Executor tasks use heartbeat for liveness detection.
If a worker crashes, the task will be recovered and re-claimed.
"""

import json
from typing import Optional, Any, Dict, List, TYPE_CHECKING

from .base import TaskWorker

if TYPE_CHECKING:
    from .gateway_client import GatewayClient


class ExecutorWorker(TaskWorker):
    """
    Worker that processes executor (async) tasks.
    
    Each executor task:
    - Executes its specific logic (think, tool_call, etc.)
    - Updates the stage's collector completed_tasks count
    """
    
    name = "executor-worker"
    poll_interval = 0.1
    claim_timeout_seconds = 300  # 5 minutes for LLM/tool calls
    
    # Registry of executor handlers
    _handlers: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, subtype: str):
        """Decorator to register an executor handler."""
        def decorator(handler_class):
            cls._handlers[subtype] = handler_class
            return handler_class
        return decorator
    
    def get_task_types(self) -> List[str]:
        return ["async"]
    
    def get_task_subtypes(self) -> Optional[List[str]]:
        # Handle all async subtypes
        return None
    
    async def process(self, task: dict) -> Any:
        """
        Process an async (execution) task.
        
        1. Get the appropriate executor for task_subtype
        2. Execute the task
        3. Return result
        """
        task_id = task.get("id")
        task_subtype = task.get("task_subtype")
        runtime_id = task.get("runtime_id")
        stage_id = task.get("stage_id")
        agent_id = task.get("agent_id")
        
        # Parse args
        args = task.get("args", {})
        if isinstance(args, str):
            args = json.loads(args)
        
        self._log(f"Executing {task_subtype} (task: {task_id})")
        
        # Get handler
        handler_class = self._handlers.get(task_subtype)
        if not handler_class:
            raise ValueError(f"No handler registered for async subtype: {task_subtype}")
        
        handler = handler_class(self.client, self.config)
        
        # Execute
        result = await handler.execute(
            task=task,
            runtime_id=runtime_id,
            stage_id=stage_id,
            agent_id=agent_id,
            args=args,
        )
        
        return result
    
    async def on_success(self, task: dict, result: Any):
        """
        Called after successful execution.
        
        Updates task status and increments collector's completed_tasks count.
        """
        task_id = task.get("id")
        stage_id = task.get("stage_id")
        
        # Mark task as done via Gateway API
        await self.client.mark_task_done(task_id, result)
        
        # Increment collector's completed_tasks count
        await self.increment_collector_count(stage_id)
        
        self._log(f"Task {task_id} completed, incremented stage {stage_id} count")
    
    async def on_failure(self, task: dict, error: Exception):
        """
        Called after failed execution.
        
        Updates task status and still increments collector's count
        (collector will see the failed status and handle appropriately).
        """
        task_id = task.get("id")
        stage_id = task.get("stage_id")
        
        # Mark task as failed via Gateway API
        await self.client.mark_task_failed(task_id, str(error))
        
        # Still increment collector's count (it needs to know this task is done)
        await self.increment_collector_count(stage_id)
        
        self._log(f"Task {task_id} failed: {error}", level="error")


class BaseExecutor:
    """Base class for executor implementations."""
    
    def __init__(self, client: 'GatewayClient', config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.gateway_url = client.gateway_url
    
    async def execute(
        self,
        task: dict,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: dict,
    ) -> Any:
        """
        Execute the task.
        
        Returns:
            Result of execution (will be stored in task.result)
        """
        raise NotImplementedError
