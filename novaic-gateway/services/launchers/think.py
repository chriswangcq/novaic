"""
ThinkLauncher

Prepares context and creates a think async task.

Pre-logic:
- Get Runtime state
- Prepare context (historical summary, inbox messages)
- Apply context compaction if needed

Creates one async task: think
"""

import json
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from ..launcher_worker import BaseLauncher, LauncherWorker

if TYPE_CHECKING:
    from ..gateway_client import GatewayClient


# Model context window limits (tokens)
MODEL_CONTEXT_LIMITS = {
    "moonshot-v1-8k": 8192,
    "moonshot-v1-32k": 32768,
    "moonshot-v1-128k": 131072,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "claude-3.5-sonnet": 200000,
    "kimi-k2.5": 131072,
    "default": 8192,
}


def get_model_context_limit(model_name: str) -> int:
    """Get context limit for a model."""
    if not model_name:
        return MODEL_CONTEXT_LIMITS["default"]
    
    model_lower = model_name.lower()
    
    if model_lower in MODEL_CONTEXT_LIMITS:
        return MODEL_CONTEXT_LIMITS[model_lower]
    
    for key, limit in MODEL_CONTEXT_LIMITS.items():
        if key in model_lower or model_lower in key:
            return limit
    
    return MODEL_CONTEXT_LIMITS["default"]


@LauncherWorker.register("think_launcher")
class ThinkLauncher(BaseLauncher):
    """
    Launcher that prepares context and creates think task.
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
        Prepare context and create think async task.
        """
        # Get runtime_id from args (REQUIRED - no fallback to avoid using "system")
        actual_runtime_id = args.get("runtime_id")
        if not actual_runtime_id:
            raise ValueError(f"runtime_id not found in args: {args}")
        
        # Get Runtime via Gateway API
        runtime = await self.client.get_runtime(actual_runtime_id)
        
        if not runtime:
            raise ValueError(f"Runtime not found: {actual_runtime_id}")
        
        mcp_url = runtime.get("mcp_url")
        if not mcp_url:
            raise ValueError(f"Runtime {actual_runtime_id} has no MCP URL")
        
        subagent_id = runtime.get("subagent_id")
        round_num = runtime.get("current_round_num", 1)
        round_id = runtime.get("current_round_id", "round-1")
        
        # Get actual agent_id from Runtime (REQUIRED - task's agent_id is "system")
        actual_agent_id = runtime.get("agent_id")
        if not actual_agent_id:
            raise ValueError(f"agent_id not found in Runtime {actual_runtime_id}")
        
        # Prepare context
        context = await self._prepare_context(runtime, actual_agent_id, subagent_id)
        
        # Get subagent type
        subagent_type = await self._get_subagent_type(actual_agent_id, subagent_id)
        
        # Create think async task
        # Use stage_id in idempotency_key to avoid conflicts with previous rounds
        think_task_id = await self.create_async_task(
            task_subtype="think",
            runtime_id=actual_runtime_id,
            stage_id=stage_id,
            agent_id=actual_agent_id,  # Use actual_agent_id, not task's agent_id
            args={
                "context": context,
                "mcp_url": mcp_url,
                "subagent_type": subagent_type,
                "round_id": round_id,
                "round_num": round_num,
            },
            idempotency_key=f"{actual_runtime_id}-{stage_id}-think",
        )
        
        if not think_task_id:
            raise ValueError(f"Failed to create think async task for runtime {actual_runtime_id}")
        async_task_ids = [think_task_id]
        
        # Update Runtime context via Gateway API
        await self.client.update_runtime(
            actual_runtime_id,
            context=context,
            phase="waiting_think",
        )
        
        return {
            "async_task_ids": async_task_ids,
            "collector_args": {
                "agent_id": actual_agent_id,  # REQUIRED for next tasks
                "runtime_id": actual_runtime_id,
                "round_id": round_id,
                "round_num": round_num,
            },
            "next_stage_type": "actions_launcher",  # Think collector decides
        }
    
    async def _prepare_context(
        self, 
        runtime: dict, 
        agent_id: str, 
        subagent_id: str
    ) -> List[Dict[str, Any]]:
        """Prepare context for thinking."""
        round_num = runtime.get("current_round_num", 1)
        runtime_id = runtime.get("runtime_id")
        
        # Start with existing context
        context = runtime.get("context", [])
        if isinstance(context, str):
            try:
                context = json.loads(context)
            except:
                context = []
        context = list(context) if context else []
        
        # Add historical context for first round
        if round_num == 1 and not context:
            try:
                subagent = await self.client.get_subagent(agent_id, subagent_id)
                
                if subagent:
                    historical_summary = subagent.get("historical_summary")
                    if historical_summary:
                        context.append({
                            'role': 'system',
                            'content': f"## Historical Context Summary\n\n{historical_summary}\n\n---",
                            'metadata': {'type': 'historical_summary'},
                        })
                    
                    # Add recent runtime summaries
                    latest_runtimes = await self.client.get_latest_runtimes(
                        agent_id, subagent_id, limit=10
                    )
                    
                    for r in latest_runtimes:
                        summary = r.get("summary")
                        if summary and r.get("runtime_id") != runtime_id:
                            context.append({
                                'role': 'system',
                                'content': f"## Previous Session Summary\n\n{summary}\n\n---",
                                'metadata': {'type': 'runtime_summary'},
                            })
            except Exception as e:
                print(f"[ThinkLauncher] Warning: Could not load historical context: {e}")
        
        # Get unread inbox messages via Gateway API
        messages = await self.client.get_unread_messages(agent_id)
        
        # Add to context and mark as processed
        message_ids = []
        for msg in messages:
            message_ids.append(msg.get("id"))
            msg_type = msg.get("type", "")
            metadata = msg.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            context.append({
                'role': 'user' if msg_type == 'USER_MESSAGE' else 'system',
                'content': msg.get("content", ""),
                'metadata': metadata,
                'timestamp': msg.get("created_at"),
            })
        
        if message_ids:
            await self.client.mark_messages_processed(message_ids)
        
        # Apply compaction if needed
        try:
            agent = await self.client.get_agent(agent_id)
            
            model_name = "gpt-4o"
            if agent:
                config = agent.get("config", {})
                if isinstance(config, str):
                    try:
                        config = json.loads(config)
                    except:
                        config = {}
                model_name = config.get("default_model", "gpt-4o")
            
            context_limit = get_model_context_limit(model_name)
            context = await self._compact_context_if_needed(agent_id, context, context_limit)
        except Exception as e:
            print(f"[ThinkLauncher] Warning: Context compaction error: {e}")
        
        return context
    
    async def _compact_context_if_needed(
        self,
        agent_id: str,
        context: List[Dict[str, Any]],
        context_limit: int = 8000,
        threshold_ratio: float = 0.8,
        target_ratio: float = 0.3,
        min_messages_to_keep: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Compact context using LLM if it exceeds token threshold.
        
        Uses LLM to generate a summary of older messages rather than
        simply truncating them, preserving important context.
        """
        if len(context) <= min_messages_to_keep:
            return context
        
        # Estimate tokens
        def estimate_tokens(messages):
            total_chars = sum(len(str(msg.get('content', ''))) + 50 for msg in messages)
            return total_chars // 4
        
        trigger_tokens = int(context_limit * threshold_ratio)
        target_tokens = int(context_limit * target_ratio)
        estimated_tokens = estimate_tokens(context)
        
        if estimated_tokens <= trigger_tokens:
            return context
        
        print(f"[ThinkLauncher] Context compaction triggered: ~{estimated_tokens} tokens > {trigger_tokens} threshold")
        print(f"[ThinkLauncher] Target: ~{target_tokens} tokens ({target_ratio*100:.0f}% of {context_limit})")
        
        # Separate system messages and conversation
        system_messages = [
            m for m in context 
            if m.get('role') == 'system' and 'compaction_summary' not in str(m.get('metadata', {}))
        ]
        conversation = [
            m for m in context 
            if m.get('role') != 'system' or 'compaction_summary' in str(m.get('metadata', {}))
        ]
        
        # Calculate messages to keep
        summary_reserve = 500
        available_for_messages = target_tokens - estimate_tokens(system_messages) - summary_reserve
        
        messages_to_keep = []
        kept_tokens = 0
        for msg in reversed(conversation):
            msg_tokens = (len(str(msg.get('content', ''))) + 50) // 4
            if kept_tokens + msg_tokens <= available_for_messages or len(messages_to_keep) < min_messages_to_keep:
                messages_to_keep.insert(0, msg)
                kept_tokens += msg_tokens
            else:
                break
        
        # Ensure minimum
        if len(messages_to_keep) < min_messages_to_keep:
            messages_to_keep = conversation[-min_messages_to_keep:]
        
        # Fix compaction boundary
        messages_to_keep = self._fix_compaction_boundary(conversation, messages_to_keep)
        
        messages_to_compact = conversation[:-len(messages_to_keep)] if len(messages_to_keep) < len(conversation) else []
        
        if not messages_to_compact:
            return context
        
        print(f"[ThinkLauncher] Keeping {len(messages_to_keep)} recent messages, compacting {len(messages_to_compact)} older messages")
        
        # Use LLM to generate summary via Gateway API
        try:
            result = await self.client.compact_context(agent_id, messages_to_compact)
            
            if result.get("success") and result.get("summary"):
                summary_content = f"""## 对话历史摘要

以下是之前 {len(messages_to_compact)} 条消息的 LLM 压缩摘要：

{result['summary']}

---
（以上为历史摘要，以下为最近的对话）"""
                print(f"[ThinkLauncher] LLM compaction successful: {len(messages_to_compact)} messages -> summary")
            else:
                # Fallback to simple truncation if LLM fails
                error = result.get("error", "Unknown error")
                print(f"[ThinkLauncher] LLM compaction failed ({error}), using fallback")
                summary_content = f"[Context compacted: {len(messages_to_compact)} earlier messages were compressed. Some context may be lost.]"
        except Exception as e:
            # Fallback to simple truncation on any error
            print(f"[ThinkLauncher] LLM compaction error: {e}, using fallback")
            summary_content = f"[Context compacted: {len(messages_to_compact)} earlier messages were compressed. Some context may be lost.]"
        
        summary_msg = {
            'role': 'system',
            'content': summary_content,
            'metadata': {'type': 'compaction_summary', 'compacted_count': len(messages_to_compact)},
        }
        
        new_context = system_messages + [summary_msg] + messages_to_keep
        new_tokens = estimate_tokens(new_context)
        
        print(f"[ThinkLauncher] Compacted: {len(messages_to_compact)} messages removed, ~{estimated_tokens} -> ~{new_tokens} tokens ({new_tokens/context_limit*100:.1f}%)")
        
        return new_context
    
    def _fix_compaction_boundary(
        self,
        all_messages: List[Dict[str, Any]],
        messages_to_keep: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Fix compaction boundary to ensure tool_calls/tool_result pairs are complete."""
        if not messages_to_keep:
            return messages_to_keep
        
        kept_tool_call_ids = set()
        for msg in messages_to_keep:
            if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                for tc in msg['tool_calls']:
                    tc_id = tc.get('id')
                    if tc_id:
                        kept_tool_call_ids.add(tc_id)
        
        result = []
        found_valid_start = False
        orphan_count = 0
        
        for msg in messages_to_keep:
            if not found_valid_start and msg.get('role') == 'tool_result':
                tc_id = msg.get('tool_call_id')
                if tc_id and tc_id not in kept_tool_call_ids:
                    orphan_count += 1
                    continue
            
            found_valid_start = True
            result.append(msg)
        
        if orphan_count > 0:
            print(f"[ThinkLauncher] Fixed compaction boundary: removed {orphan_count} orphan tool_result(s)")
        
        return result
    
    async def _get_subagent_type(self, agent_id: str, subagent_id: str) -> str:
        """Get subagent type."""
        try:
            subagent = await self.client.get_subagent(agent_id, subagent_id)
            
            if subagent:
                return subagent.get("type", "main")
        except:
            pass
        
        return "main"
