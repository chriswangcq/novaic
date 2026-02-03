"""
CollectorWorker

Handles 'collector' type tasks.

Collector tasks are responsible for:
1. Waiting for all async tasks in a stage to complete
2. Post-logic processing (aggregate results, decide next step)
3. Creating the next launcher task to continue the pipeline

Collector tasks are idempotent - they can be safely re-executed.
The collector only becomes 'pending' when all async tasks are done.
"""

import json
import uuid
from typing import Optional, Any, Dict, List, TYPE_CHECKING

from .base import TaskWorker

if TYPE_CHECKING:
    from .gateway_client import GatewayClient


class CollectorWorker(TaskWorker):
    """
    Worker that processes collector tasks.
    
    Each collector:
    - Waits for expected_tasks count to reach completed_tasks
    - Gathers results from all async tasks
    - Creates the next launcher task
    """
    
    name = "collector-worker"
    poll_interval = 0.1
    claim_timeout_seconds = 60
    
    # Registry of collector handlers
    _handlers: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, subtype: str):
        """Decorator to register a collector handler."""
        def decorator(handler_class):
            cls._handlers[subtype] = handler_class
            return handler_class
        return decorator
    
    def get_task_types(self) -> List[str]:
        return ["collector"]
    
    def get_task_subtypes(self) -> Optional[List[str]]:
        # Handle all collector subtypes
        return None
    
    async def process(self, task: dict) -> Any:
        """
        Process a collector task.
        
        1. Gather results from all async tasks
        2. Get the appropriate handler for task_subtype
        3. Execute post-logic
        4. Create next launcher task if needed
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
        
        async_task_ids = args.get("async_task_ids", [])
        next_stage_type = args.get("next_stage_type")
        
        self._log(f"Processing {task_subtype} collector (task: {task_id})")
        
        # Gather async task results via Gateway API
        async_results = []
        if async_task_ids:
            tasks = await self.client.get_tasks_by_stage(stage_id)
            
            for t in tasks:
                if t.get("task_type") == "async":
                    async_results.append({
                        "task_id": t.get("id"),
                        "task_subtype": t.get("task_subtype"),
                        "status": t.get("status"),
                        "result": t.get("result"),
                        "error": t.get("error"),
                        "args": t.get("args"),
                    })
        
        # Get handler
        handler_class = self._handlers.get(task_subtype)
        if not handler_class:
            raise ValueError(f"No handler registered for collector subtype: {task_subtype}")
        
        handler = handler_class(self.client, self.config)
        
        # Execute post-logic
        collect_result = await handler.collect_and_trigger(
            task=task,
            runtime_id=runtime_id,
            stage_id=stage_id,
            agent_id=agent_id,
            args=args,
            async_results=async_results,
        )
        
        # Create next launcher if specified
        next_launcher_id = None
        should_continue = collect_result.get("should_continue", False)
        next_stage_type = collect_result.get("next_stage_type") or next_stage_type
        next_args = collect_result.get("next_args", {})
        
        if should_continue and next_stage_type:
            next_stage_id = f"stage-{uuid.uuid4().hex[:12]}"
            
            # v18: All tasks now require real IDs from next_args
            # (monitor_launcher removed - Monitor is now an independent service)
            next_runtime_id = next_args.get("runtime_id")
            next_agent_id = next_args.get("agent_id")
            
            # For runtime_launcher, agent_id is required
            if next_stage_type == "runtime_launcher":
                if not next_agent_id or next_agent_id == "system":
                    raise ValueError(
                        f"runtime_launcher requires real agent_id in next_args, got: {next_agent_id}"
                    )
                next_runtime_id = next_runtime_id or "pending"  # Will be created
            # For other non-system tasks, runtime_id is required
            elif not next_runtime_id or next_runtime_id == "system":
                raise ValueError(
                    f"{next_stage_type} requires real runtime_id in next_args, got: {next_runtime_id}"
                )
            
            # agent_id can be inherited for tasks after runtime_launcher
            if not next_agent_id:
                next_agent_id = agent_id
                if next_agent_id == "system":
                    raise ValueError(
                        f"{next_stage_type} cannot use system agent_id"
                    )
            
            next_launcher_id = await self.create_task(
                task_type="launcher",
                task_subtype=next_stage_type,
                runtime_id=next_runtime_id,
                stage_id=next_stage_id,
                agent_id=next_agent_id,
                args=next_args,
                idempotency_key=f"{next_runtime_id}-{next_stage_id}-launcher",
            )
            
            self._log(f"Created next launcher {next_launcher_id} ({next_stage_type})")
        
        return {
            "async_results_count": len(async_results),
            "next_launcher_id": next_launcher_id,
            "should_continue": should_continue,
        }


class BaseCollector:
    """Base class for collector implementations."""
    
    def __init__(self, client: 'GatewayClient', config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.gateway_url = client.gateway_url
    
    async def collect_and_trigger(
        self,
        task: dict,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: dict,
        async_results: List[dict],
    ) -> dict:
        """
        Execute post-logic and decide next step.
        
        Returns:
            {
                "should_continue": bool,    # Whether to continue pipeline
                "next_stage_type": "...",   # Next launcher subtype (override)
                "next_args": {...},         # Args for next launcher
            }
        """
        raise NotImplementedError
