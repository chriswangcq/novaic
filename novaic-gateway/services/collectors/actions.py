"""
ActionsCollector

Processes tool_call results and triggers next think or completion.

Post-logic:
- Collect results from all tool_calls
- Add tool_result messages to context
- Decide: continue ReACT loop or complete
"""

import json
from typing import Dict, Any, List, TYPE_CHECKING

from ..collector_worker import BaseCollector, CollectorWorker

if TYPE_CHECKING:
    from ..gateway_client import GatewayClient


@CollectorWorker.register("actions_collector")
class ActionsCollector(BaseCollector):
    """
    Collector that processes action results and continues ReACT loop.
    """
    
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
        Process action results and decide next step.
        """
        # Get runtime_id from args (REQUIRED)
        actual_runtime_id = args.get("runtime_id")
        if not actual_runtime_id:
            raise ValueError(f"runtime_id not found in args: {args}")
        
        round_id = args.get("round_id", "round-1")
        has_done = args.get("has_done", False)
        
        # Get runtime via Gateway API
        runtime = await self.client.get_runtime(actual_runtime_id)
        
        if not runtime:
            raise ValueError(f"Runtime not found: {actual_runtime_id}")
        
        # Get actual agent_id from Runtime (REQUIRED)
        actual_agent_id = runtime.get("agent_id")
        if not actual_agent_id:
            raise ValueError(f"agent_id not found in Runtime {actual_runtime_id}")
        
        current_round_num = runtime.get("current_round_num", 1)
        
        # Add tool results to context
        context = runtime.get("context", [])
        if isinstance(context, str):
            try:
                context = json.loads(context)
            except:
                context = []
        context = list(context) if context else []
        
        has_results = False
        for r in async_results:
            if r.get("task_subtype") == "tool_call":
                # Parse args for tool_call_id (MUST have this to match assistant's tool_calls)
                args_data = r.get("args", {})
                if isinstance(args_data, str):
                    try:
                        args_data = json.loads(args_data)
                    except:
                        args_data = {}
                
                tool_call_id = args_data.get("tool_call_id", "")
                tool_name = args_data.get("tool_name", "tool")
                
                # Get result (even if failed/empty - MUST record to match tool_calls)
                result_data = r.get("result")
                if result_data:
                    has_results = True
                    content = json.dumps(result_data) if isinstance(result_data, dict) else str(result_data)
                else:
                    # Task completed but no result - add error placeholder
                    # This ensures every tool_call has a matching tool_result
                    content = json.dumps({"success": False, "error": "Task completed without result"})
                
                # Only add if we have tool_call_id (required for LLM API)
                if tool_call_id:
                    context.append({
                        "role": "tool_result",
                        "content": content,
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                    })
                else:
                    print(f"[ActionsCollector] Warning: tool_call without tool_call_id, skipping: {tool_name}")
        
        # Update context via Gateway API
        await self.client.update_runtime(actual_runtime_id, context=context)
        
        # Check if should complete
        if has_done:
            print(f"[ActionsCollector] {actual_runtime_id} has done flag, completing")
            return {
                "should_continue": True,
                "next_stage_type": "summarize_launcher",
                "next_args": {
                    "agent_id": actual_agent_id,  # REQUIRED for next tasks
                    "runtime_id": actual_runtime_id,
                },
            }
        
        # Check for unread messages via Gateway API
        has_unread = await self.client.has_unread_messages(actual_agent_id)
        
        # v19: Re-fetch runtime to get latest status (runtime_rest may have changed it during tool_call)
        runtime = await self.client.get_runtime(actual_runtime_id)
        runtime_status = runtime.get("status", "") if runtime else ""
        
        # v18: Check if runtime_rest was called (status = 'resting')
        # If no new messages, skip further think rounds and go to summarize
        if runtime_status == "resting" and not has_unread:
            print(f"[ActionsCollector] {actual_runtime_id} is resting and no new messages, completing")
            return {
                "should_continue": True,
                "next_stage_type": "summarize_launcher",
                "next_args": {
                    "agent_id": actual_agent_id,
                    "runtime_id": actual_runtime_id,
                },
            }
        
        if has_results or has_unread:
            # Continue ReACT loop - advance round
            new_round_num = current_round_num + 1
            new_round_id = f"round-{new_round_num}"
            
            await self.client.update_runtime(
                actual_runtime_id,
                current_round_num=new_round_num,
                current_round_id=new_round_id,
                phase="need_think",
            )
            
            print(f"[ActionsCollector] {actual_runtime_id} advancing to {new_round_id}")
            
            return {
                "should_continue": True,
                "next_stage_type": "think_launcher",
                "next_args": {
                    "agent_id": actual_agent_id,  # REQUIRED for next tasks
                    "runtime_id": actual_runtime_id,
                },
            }
        
        # No more work, complete
        print(f"[ActionsCollector] {actual_runtime_id} no more work, completing")
        
        return {
            "should_continue": True,
            "next_stage_type": "summarize_launcher",
            "next_args": {
                "agent_id": actual_agent_id,  # REQUIRED for next tasks
                "runtime_id": actual_runtime_id,
            },
        }
