"""
ThinkCollector

Processes think result and triggers actions or completion.

Post-logic:
- Parse think result (actions, done flag)
- Add assistant message to context
- Clean up image data in tool_results (already processed by LLM)
- Decide: create actions_launcher or summarize_launcher
"""

import json
from typing import Dict, Any, List, TYPE_CHECKING

from ..collector_worker import BaseCollector, CollectorWorker

if TYPE_CHECKING:
    from ..gateway_client import GatewayClient

# Import multimodal utilities for image cleanup
try:
    from utils import multimodal
except ImportError:
    multimodal = None


@CollectorWorker.register("think_collector")
class ThinkCollector(BaseCollector):
    """
    Collector that processes think result and decides next step.
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
        Process think result and decide next step.
        """
        # Get REQUIRED fields from args
        actual_runtime_id = args.get("runtime_id")
        if not actual_runtime_id:
            raise ValueError(f"runtime_id not found in args: {args}")
        
        actual_agent_id = args.get("agent_id")
        if not actual_agent_id or actual_agent_id == "system":
            raise ValueError(f"think_collector requires real agent_id in args, got: {actual_agent_id}")
        
        round_id = args.get("round_id", "round-1")
        round_num = args.get("round_num", 1)
        
        # Get think result
        think_result = None
        for r in async_results:
            if r.get("task_subtype") == "think" and r.get("result"):
                think_result = r["result"]
                break
        
        if not think_result:
            # Think failed or no result - check async_results for error
            error = None
            for r in async_results:
                if r.get("error"):
                    error = r["error"]
                    break
            
            error_msg = error or "Think failed"
            print(f"[ThinkCollector] No think result for {actual_runtime_id}: {error_msg}")
            
            # Mark runtime as failed via Gateway API
            await self.client.update_runtime(
                actual_runtime_id,
                status="failed",
                error=error_msg,
            )
            
            # Get subagent_id for summarize
            runtime = await self.client.get_runtime(actual_runtime_id)
            subagent_id = runtime.get("subagent_id") if runtime else None
            
            # Trigger summarize to record failure context
            return {
                "should_continue": True,
                "next_stage_type": "summarize_launcher",
                "next_args": {
                    "agent_id": actual_agent_id,
                    "runtime_id": actual_runtime_id,
                    "subagent_id": subagent_id,
                    "simple_summary": f"Runtime failed: {error_msg}",
                    "is_failure": True,
                },
            }
        
        # Check if think succeeded
        if not think_result.get("success", True):
            error = think_result.get("error", "Unknown think error")
            print(f"[ThinkCollector] Think failed for {actual_runtime_id}: {error}")
            
            await self.client.update_runtime(
                actual_runtime_id,
                status="failed",
                error=error,
            )
            
            # Get subagent_id for summarize
            runtime = await self.client.get_runtime(actual_runtime_id)
            subagent_id = runtime.get("subagent_id") if runtime else None
            
            # Trigger summarize to record failure context
            return {
                "should_continue": True,
                "next_stage_type": "summarize_launcher",
                "next_args": {
                    "agent_id": actual_agent_id,
                    "runtime_id": actual_runtime_id,
                    "subagent_id": subagent_id,
                    "simple_summary": f"Think failed: {error}",
                    "is_failure": True,
                },
            }
        
        # Parse actions
        actions = think_result.get("actions", [])
        has_done = any(a.get("type") == "done" for a in actions)
        action_tasks = [a for a in actions if a.get("type") != "done"]
        mcp_session_id = think_result.get("mcp_session_id")
        reasoning = think_result.get("reasoning", "")
        
        # Get runtime context via Gateway API
        runtime = await self.client.get_runtime(actual_runtime_id)
        
        if runtime:
            context = runtime.get("context", [])
            if isinstance(context, str):
                try:
                    context = json.loads(context)
                except:
                    context = []
            context = list(context) if context else []
            
            # Clean up image data in tool_results (already processed by LLM)
            if multimodal:
                for msg in context:
                    if msg.get('role') == 'tool_result':
                        content = msg.get('content', '')
                        if isinstance(content, str):
                            try:
                                result_data = json.loads(content)
                                if isinstance(result_data, dict) and multimodal.has_images(result_data):
                                    msg['content'] = multimodal.result_to_text_only(result_data)
                            except (json.JSONDecodeError, TypeError):
                                pass  # Not JSON, skip
            
            # Add assistant message with tool_calls
            if action_tasks:
                tool_calls = []
                for a in action_tasks:
                    if a.get("tool_call_id"):
                        tool_calls.append({
                            "id": a.get("tool_call_id"),
                            "type": "function",
                            "function": {
                                "name": a.get("tool"),
                                "arguments": json.dumps(a.get("args", {})),
                            }
                        })
                
                if tool_calls:
                    assistant_msg = {
                        "role": "assistant",
                        "content": reasoning,
                        "tool_calls": tool_calls,
                    }
                    if reasoning:
                        assistant_msg["reasoning_content"] = reasoning
                    context.append(assistant_msg)
            
            # Always update context via Gateway API
            await self.client.update_runtime(actual_runtime_id, context=context)
        
        # Decide next step
        if action_tasks:
            # Has actions to execute
            print(f"[ThinkCollector] {actual_runtime_id} has {len(action_tasks)} actions")
            
            return {
                "should_continue": True,
                "next_stage_type": "actions_launcher",
                "next_args": {
                    "agent_id": actual_agent_id,  # REQUIRED for next tasks
                    "runtime_id": actual_runtime_id,
                    "actions": action_tasks,
                    "mcp_session_id": mcp_session_id,
                    "round_id": round_id,
                    "has_done": has_done,
                },
            }
        
        if has_done:
            # Done signal, no more actions
            print(f"[ThinkCollector] {actual_runtime_id} is done")
            
            return {
                "should_continue": True,
                "next_stage_type": "summarize_launcher",
                "next_args": {
                    "agent_id": actual_agent_id,  # REQUIRED for next tasks
                    "runtime_id": actual_runtime_id,
                },
            }
        
        # No actions and no done - complete anyway
        print(f"[ThinkCollector] {actual_runtime_id} has no actions, completing")
        
        return {
            "should_continue": True,
            "next_stage_type": "summarize_launcher",
            "next_args": {
                "agent_id": actual_agent_id,  # REQUIRED for next tasks
                "runtime_id": actual_runtime_id,
            },
        }
