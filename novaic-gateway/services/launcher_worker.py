"""
LauncherWorker

Handles 'launcher' type tasks.

Launcher tasks are responsible for:
1. Pre-logic processing (prepare context, check conditions)
2. Creating async tasks for execution
3. Creating a collector task to gather results

Launcher tasks are idempotent - they can be safely re-executed.
"""

import json
import uuid
from typing import Optional, Any, Dict, List, TYPE_CHECKING

from .base import TaskWorker

if TYPE_CHECKING:
    from .gateway_client import GatewayClient


class LauncherWorker(TaskWorker):
    """
    Worker that processes launcher tasks.
    
    Each launcher creates:
    - N async tasks (think, tool_call, etc.)
    - 1 collector task (to gather results and trigger next stage)
    """
    
    name = "launcher-worker"
    poll_interval = 0.1
    claim_timeout_seconds = 60
    
    # Registry of launcher handlers
    _handlers: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, subtype: str):
        """Decorator to register a launcher handler."""
        def decorator(handler_class):
            cls._handlers[subtype] = handler_class
            return handler_class
        return decorator
    
    def get_task_types(self) -> List[str]:
        return ["launcher"]
    
    def get_task_subtypes(self) -> Optional[List[str]]:
        # Handle all launcher subtypes
        return None
    
    async def process(self, task: dict) -> Any:
        """
        Process a launcher task.
        
        1. Get the appropriate handler for task_subtype
        2. Execute pre-logic
        3. Create async tasks
        4. Create collector task
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
        
        self._log(f"Processing {task_subtype} launcher (task: {task_id})")
        
        # Get handler
        handler_class = self._handlers.get(task_subtype)
        if not handler_class:
            raise ValueError(f"No handler registered for launcher subtype: {task_subtype}")
        
        handler = handler_class(self.client, self.config)
        
        # Execute pre-logic
        launch_result = await handler.prepare_and_launch(
            task=task,
            runtime_id=runtime_id,
            stage_id=stage_id,
            agent_id=agent_id,
            args=args,
        )
        
        async_task_ids = launch_result.get("async_task_ids", [])
        collector_args = launch_result.get("collector_args", {})
        next_stage_type = launch_result.get("next_stage_type")
        
        # v18: All tasks require real agent_id
        # (monitor_launcher removed - Monitor is now an independent service)
        actual_agent_id = collector_args.get("agent_id") or args.get("agent_id")
        if not actual_agent_id or actual_agent_id == "system":
            raise ValueError(
                f"Task {task_subtype} requires real agent_id, "
                f"got: collector_args={collector_args.get('agent_id')}, args={args.get('agent_id')}"
            )
        
        # Create collector task (even if no async tasks, collector handles next stage)
        collector_subtype = task_subtype.replace("_launcher", "_collector")
        collector_id = await self.create_task(
            task_type="collector",
            task_subtype=collector_subtype,
            runtime_id=runtime_id,
            stage_id=stage_id,
            agent_id=actual_agent_id,
            args={
                **collector_args,
                "async_task_ids": async_task_ids,
                "next_stage_type": next_stage_type,
            },
            idempotency_key=f"{runtime_id}-{stage_id}-collector",
            expected_tasks=len(async_task_ids),
        )
        
        self._log(f"Created {len(async_task_ids)} async tasks + collector {collector_id}")
        
        return {
            "async_task_ids": async_task_ids,
            "collector_id": collector_id,
            "next_stage_type": next_stage_type,
        }


class BaseLauncher:
    """Base class for launcher implementations."""
    
    def __init__(self, client: 'GatewayClient', config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.gateway_url = client.gateway_url
    
    async def prepare_and_launch(
        self,
        task: dict,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: dict,
    ) -> dict:
        """
        Execute pre-logic and create async tasks.
        
        Returns:
            {
                "async_task_ids": [...],  # IDs of created async tasks
                "collector_args": {...},  # Extra args for collector
                "next_stage_type": "...", # Next launcher subtype to trigger
            }
        """
        raise NotImplementedError
    
    async def create_async_task(
        self,
        task_subtype: str,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: dict,
        idempotency_key: Optional[str] = None,
    ) -> Optional[str]:
        """Helper to create an async task via Gateway API."""
        return await self.client.create_task(
            task_type="async",
            task_subtype=task_subtype,
            runtime_id=runtime_id,
            stage_id=stage_id,
            agent_id=agent_id,
            args=args,
            idempotency_key=idempotency_key,
        )
