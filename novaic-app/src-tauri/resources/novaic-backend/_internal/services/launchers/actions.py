"""
ActionsLauncher

Creates tool_call async tasks from LLM actions.

Pre-logic:
- Parse actions from think result
- Create tool_call tasks for each action

Creates N async tasks: tool_call
"""

import json
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from ..launcher_worker import BaseLauncher, LauncherWorker

if TYPE_CHECKING:
    from ..gateway_client import GatewayClient


@LauncherWorker.register("actions_launcher")
class ActionsLauncher(BaseLauncher):
    """
    Launcher that creates tool_call tasks from LLM actions.
    """
    
    async def prepare_and_launch(
        self,
        task: dict,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: dict,
    ) -> dict:
        """
        Create tool_call tasks from actions.
        """
        # Get runtime_id from args (REQUIRED)
        actual_runtime_id = args.get("runtime_id")
        if not actual_runtime_id:
            raise ValueError(f"runtime_id not found in args: {args}")
        
        actions = args.get("actions", [])
        mcp_session_id = args.get("mcp_session_id")
        round_id = args.get("round_id", "round-1")
        has_done = args.get("has_done", False)
        
        # Get Runtime for MCP URL and agent_id via Gateway API
        runtime = await self.client.get_runtime(actual_runtime_id)
        
        if not runtime:
            raise ValueError(f"Runtime not found: {actual_runtime_id}")
        
        mcp_url = runtime.get("mcp_url")
        actual_agent_id = runtime.get("agent_id")
        if not actual_agent_id:
            raise ValueError(f"agent_id not found in Runtime {actual_runtime_id}")
        
        # Create tool_call tasks
        async_task_ids = []
        
        for i, action in enumerate(actions):
            action_type = action.get("type", "tool_call")
            if action_type == "done":
                continue
            
            tool_name = action.get("tool") or action.get("name")
            tool_args = action.get("args", {})
            tool_call_id = action.get("tool_call_id", "")
            
            # Use stage_id in idempotency_key to avoid conflicts
            mcpcall_id = f"mc-{i+1}"
            idempotency_key = f"{actual_runtime_id}-{stage_id}-{mcpcall_id}"
            
            task_id = await self.create_async_task(
                task_subtype="tool_call",
                runtime_id=actual_runtime_id,
                stage_id=stage_id,
                agent_id=actual_agent_id,  # Use actual_agent_id from Runtime
                args={
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "tool_call_id": tool_call_id,
                    "mcp_url": mcp_url,
                    "mcp_session_id": mcp_session_id,
                },
                idempotency_key=idempotency_key,
            )
            
            if not task_id:
                raise ValueError(f"Failed to create tool_call task for {tool_name} in runtime {actual_runtime_id}")
            async_task_ids.append(task_id)
        
        # Determine next stage
        if has_done:
            next_stage_type = "summarize_launcher"
        else:
            next_stage_type = "think_launcher"  # Continue ReACT loop
        
        # Update Runtime phase via Gateway API
        await self.client.update_runtime(actual_runtime_id, phase="waiting_actions")
        
        return {
            "async_task_ids": async_task_ids,
            "collector_args": {
                "agent_id": actual_agent_id,  # REQUIRED for next tasks
                "runtime_id": actual_runtime_id,
                "round_id": round_id,
                "has_done": has_done,
            },
            "next_stage_type": next_stage_type,
        }
