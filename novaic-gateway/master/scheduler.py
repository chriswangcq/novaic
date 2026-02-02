"""
Scheduler Component

Drives the ReACT loop for each active Runtime.
Handles:
- Phase 1: THINK - Prepare context, create think task
- Phase 2: SCHEDULE - Process actions, create action tasks
- Phase 3: EXECUTE - Broadcast tasks to Workers
- Phase 4: COLLECT - Wait for results, advance Round

v2.10: Uses Gateway HTTP API instead of direct DB access.
v14: SubAgent state refactor
- Uses runtime_id instead of subagent_id
- Checks inbox at round completion to decide continue/complete
- Context includes SubAgent historical_summary + latest runtime summaries
- Triggers Summarizer on runtime completion
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import multimodal

if TYPE_CHECKING:
    from .master import Master

# Model context window limits (tokens)
# Used for context compaction threshold (set to ~70% of limit)
MODEL_CONTEXT_LIMITS = {
    # Moonshot models
    "moonshot-v1-8k": 8192,
    "moonshot-v1-32k": 32768,
    "moonshot-v1-128k": 131072,
    # OpenAI models
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
    # Anthropic models
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-3.5-sonnet": 200000,
    # Kimi models
    "kimi-k2.5": 131072,
    # Default fallback
    "default": 8192,
}

def get_model_context_limit(model_name: str) -> int:
    """Get context limit for a model, with fuzzy matching."""
    if not model_name:
        return MODEL_CONTEXT_LIMITS["default"]
    
    model_lower = model_name.lower()
    
    # Exact match first
    if model_lower in MODEL_CONTEXT_LIMITS:
        return MODEL_CONTEXT_LIMITS[model_lower]
    
    # Partial match
    for key, limit in MODEL_CONTEXT_LIMITS.items():
        if key in model_lower or model_lower in key:
            return limit
    
    return MODEL_CONTEXT_LIMITS["default"]


class Scheduler:
    """Schedules and drives Runtime execution."""
    
    def __init__(self, master: 'Master'):
        self.master = master
        self.running = False
        self.loop_interval = 0.1  # seconds (fast polling)
        self._task = None
        
        # Track processed states to avoid double-scheduling
        # Key: (subagent_id, round_id, phase) - each state is processed only once
        self._processed_states: set = set()
        
        # Track currently executing tasks (for immediate lock)
        self._executing: set = set()
    
    async def start(self):
        """Start the scheduler loop."""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run())
        print("[Scheduler] Started")
    
    async def stop(self):
        """Stop the scheduler loop."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("[Scheduler] Stopped")
    
    async def _run(self):
        """Main scheduler loop."""
        while self.running:
            try:
                await self._schedule_runtimes()
            except Exception as e:
                print(f"[Scheduler] Error in schedule loop: {e}")
                import traceback
                traceback.print_exc()
            
            await asyncio.sleep(self.loop_interval)
    
    async def _schedule_runtimes(self):
        """Check all active runtimes and drive them."""
        gateway = self.master.gateway
        
        # Get all active runtimes (v14: includes status=active and status=resting)
        runtimes = await gateway.get_active_runtimes()
        
        for runtime in runtimes:
            # v14: Use runtime_id
            runtime_id = runtime.get("runtime_id") or runtime.get("subagent_id")
            round_id = runtime.get("current_round_id", "round-1")
            phase = runtime.get("phase", "")
            
            # Skip if currently executing (immediate lock)
            if runtime_id in self._executing:
                continue
            
            # For need_think phase: only process once per (round, phase)
            # For waiting_actions phases: always process (need to poll task status)
            if phase == 'need_think':
                state_key = (runtime_id, round_id, phase)
                if state_key in self._processed_states:
                    continue
                self._processed_states.add(state_key)
            
            # Mark as executing
            self._executing.add(runtime_id)
            
            # Drive this runtime based on its phase
            asyncio.create_task(self._drive_runtime(runtime))
    
    async def _drive_runtime(self, runtime: Dict[str, Any]):
        """Drive a single runtime through its current phase."""
        # v14: Use runtime_id
        runtime_id = runtime.get("runtime_id") or runtime.get("subagent_id")
        gateway = self.master.gateway
        
        try:
            # Re-read runtime to get latest state
            fresh_runtime = await gateway.get_runtime(runtime_id)
            if not fresh_runtime:
                return  # Runtime not found
            
            # v14: Active runtimes include status=active and status=resting
            status = fresh_runtime.get("status", "")
            if status not in ('active', 'resting'):
                return  # Runtime no longer active
            
            runtime = fresh_runtime
            phase = runtime.get("phase", "")
            
            if phase == 'need_think':
                await self._handle_need_think(runtime)
            elif phase in ('waiting_actions', 'waiting_actions_final'):
                await self._handle_waiting_actions(runtime)
            # 'completed' phase - no action needed
        except Exception as e:
            print(f"[Scheduler] Error driving runtime {runtime_id}: {e}")
            import traceback
            traceback.print_exc()
            # Mark runtime as failed
            await gateway.update_runtime(runtime_id, status="failed", error=str(e))
        finally:
            # Release executing lock (allow next state to be processed)
            self._executing.discard(runtime_id)
    
    async def _handle_need_think(self, runtime: Dict[str, Any]):
        """Phase 1: THINK - Create think task for Worker."""
        # v14: Use runtime_id
        runtime_id = runtime.get("runtime_id") or runtime.get("subagent_id")
        round_num = runtime.get("current_round_num", 1)
        
        # Wait for MCP URL to be set (MCP servers may still be initializing)
        mcp_url = runtime.get("mcp_url")
        if not mcp_url:
            # MCP servers not ready yet - remove from processed_states to retry
            state_key = (runtime_id, runtime.get("current_round_id", "round-1"), "need_think")
            self._processed_states.discard(state_key)
            return
        
        print(f"[Scheduler] Runtime {runtime_id} needs think (round {round_num})")
        
        # 1. Prepare context
        context = await self._prepare_context(runtime)
        
        # 2. Create think task (with database-level idempotency)
        task_id = await self._create_think_task(runtime, context)
        
        if task_id is None:
            # Another Master already created this think task - skip
            print(f"[Scheduler] Skipping: think task for {runtime_id} round {round_num} already exists")
            return
        
        # 3. Update runtime state
        await self.master.gateway.update_runtime(
            runtime_id,
            phase="waiting_actions",
            pending_actions=[task_id]
        )
        
        # 4. Broadcast SSE
        await self.master.broadcast_new_task(task_id, 'think', runtime["agent_id"])
        
        print(f"[Scheduler] Created think task {task_id} for runtime {runtime_id}")
    
    async def _prepare_context(self, runtime: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare context for thinking, including inbox messages.
        
        v14: Context structure:
        1. Historical summary from SubAgent (merged old runtime summaries)
        2. Summaries of latest completed runtimes (up to 30)
        3. Current runtime context
        4. Unread inbox messages
        """
        gateway = self.master.gateway
        agent_id = runtime["agent_id"]
        # v14: Use runtime_id and subagent_id separately
        runtime_id = runtime.get("runtime_id") or runtime.get("subagent_id")
        subagent_id = runtime.get("subagent_id", "main")
        
        # Start with existing context
        context = list(runtime.get("context", []))
        
        # v14: Add SubAgent historical summary and latest runtime summaries (only for first round)
        round_num = runtime.get("current_round_num", 1)
        if round_num == 1 and not context:
            try:
                # Get SubAgent for historical context
                subagent = await gateway.get_subagent(agent_id, subagent_id)
                if subagent:
                    # Add historical summary
                    historical_summary = subagent.get("historical_summary")
                    if historical_summary:
                        context.append({
                            'role': 'system',
                            'content': f"## Historical Context Summary\n\n{historical_summary}\n\n---",
                            'metadata': {'type': 'historical_summary'},
                        })
                    
                    # Add summaries from latest runtimes
                    latest_runtimes = await gateway.get_latest_runtimes(agent_id, subagent_id, limit=10)
                    for r in latest_runtimes:
                        summary = r.get("summary")
                        if summary and r.get("runtime_id") != runtime_id:
                            context.append({
                                'role': 'system',
                                'content': f"## Previous Session Summary\n\n{summary}\n\n---",
                                'metadata': {'type': 'runtime_summary', 'runtime_id': r.get('runtime_id')},
                            })
            except Exception as e:
                print(f"[Scheduler] Warning: Could not load historical context: {e}")
        
        # Get unread inbox messages
        messages = await gateway.get_unread_messages(agent_id)
        
        # Add inbox messages to context
        inbox_message_ids = []
        for msg in messages:
            inbox_message_ids.append(msg["id"])
            context.append({
                'role': 'user' if msg["type"] == 'USER_MESSAGE' else 'system',
                'content': msg["content"],
                'metadata': msg.get("metadata", {}),
                'timestamp': msg.get("timestamp"),
                'message_id': msg["id"],
            })
        
        # Mark messages as processed
        if inbox_message_ids:
            await gateway.mark_messages_processed(inbox_message_ids)
        
        # Get model context limit for compaction
        from config.settings import get_context_compaction_settings
        compaction_settings = get_context_compaction_settings()
        
        try:
            agent_config = await gateway.get_agent_config(agent_id)
            model_name = agent_config.get("default_model", "moonshot-v1-8k")
            context_limit = get_model_context_limit(model_name)
        except Exception:
            context_limit = 8000  # Safe default
        
        # Context compaction (using LLM for summarization)
        # Trigger at 80%, target 30%
        context = await self._compact_context_if_needed(
            agent_id, 
            context, 
            context_limit=context_limit,
            threshold_ratio=compaction_settings.compaction_threshold_ratio,
            target_ratio=compaction_settings.compaction_target_ratio,
            min_messages_to_keep=compaction_settings.min_messages_to_keep,
        )
        
        # Update runtime context (v14: use runtime_id)
        await gateway.update_runtime(runtime_id, context=context)
        
        return context
    
    async def _compact_context_if_needed(
        self, 
        agent_id: str,
        context: List[Dict[str, Any]],
        context_limit: int = 8000,
        threshold_ratio: float = 0.8,  # Trigger when > 80%
        target_ratio: float = 0.3,     # Compact to ~30%
        min_messages_to_keep: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Compact context using LLM if it exceeds token threshold.
        
        Uses LLM to generate a summary of older messages rather than
        simply truncating them, preserving important context.
        
        Args:
            context_limit: Model's context window in tokens
            threshold_ratio: Trigger compaction when context exceeds this ratio (0.8 = 80%)
            target_ratio: Target ratio after compaction (0.3 = 30%)
            min_messages_to_keep: Minimum recent messages to preserve
        """
        if len(context) <= min_messages_to_keep:
            return context
        
        # Calculate thresholds
        trigger_tokens = int(context_limit * threshold_ratio)
        target_tokens = int(context_limit * target_ratio)
        
        # Estimate current tokens
        def estimate_tokens(messages: List[Dict]) -> int:
            total_chars = sum(len(str(msg.get('content', ''))) + 50 for msg in messages)
            return total_chars // 4
        
        estimated_tokens = estimate_tokens(context)
        
        if estimated_tokens <= trigger_tokens:
            return context
        
        print(f"[Scheduler] Context compaction triggered: ~{estimated_tokens} tokens > {trigger_tokens} threshold ({threshold_ratio*100:.0f}%)")
        print(f"[Scheduler] Target: ~{target_tokens} tokens ({target_ratio*100:.0f}% of {context_limit})")
        
        # Separate system messages and conversation messages
        system_messages = [m for m in context if m.get('role') == 'system' and 'compaction_summary' not in str(m.get('metadata', {}))]
        conversation_messages = [m for m in context if m.get('role') != 'system' or 'compaction_summary' in str(m.get('metadata', {}))]
        
        # Calculate how many messages to keep to reach target
        # Reserve ~500 tokens for summary message
        summary_reserve = 500
        available_for_messages = target_tokens - estimate_tokens(system_messages) - summary_reserve
        
        # Calculate messages to keep (from end)
        messages_to_keep = []
        kept_tokens = 0
        for msg in reversed(conversation_messages):
            msg_tokens = (len(str(msg.get('content', ''))) + 50) // 4
            if kept_tokens + msg_tokens <= available_for_messages or len(messages_to_keep) < min_messages_to_keep:
                messages_to_keep.insert(0, msg)
                kept_tokens += msg_tokens
            else:
                break
        
        # Ensure minimum messages kept
        if len(messages_to_keep) < min_messages_to_keep:
            messages_to_keep = conversation_messages[-min_messages_to_keep:]
        
        # Fix compaction boundary to ensure tool_calls/tool_result pairs are complete
        # If the first kept message is a tool_result, we need to either:
        # 1. Include the corresponding assistant+tool_calls message, or
        # 2. Remove the orphan tool_result
        messages_to_keep = self._fix_compaction_boundary(conversation_messages, messages_to_keep)
        
        messages_to_compact = conversation_messages[:-len(messages_to_keep)] if len(messages_to_keep) < len(conversation_messages) else []
        
        if not messages_to_compact:
            return context
        
        print(f"[Scheduler] Keeping {len(messages_to_keep)} recent messages, compacting {len(messages_to_compact)} older messages")
        
        # Use LLM to generate summary
        gateway = self.master.gateway
        try:
            result = await gateway.compact_context(agent_id, messages_to_compact)
            
            if result.get("success") and result.get("summary"):
                summary_content = f"""## 对话历史摘要

以下是之前 {len(messages_to_compact)} 条消息的 LLM 压缩摘要：

{result['summary']}

---
（以上为历史摘要，以下为最近的对话）"""
                print(f"[Scheduler] LLM compaction successful: {len(messages_to_compact)} messages -> summary")
            else:
                # Fallback to simple truncation if LLM fails
                error = result.get("error", "Unknown error")
                print(f"[Scheduler] LLM compaction failed ({error}), using fallback")
                summary_content = f"[Context compacted: {len(messages_to_compact)} earlier messages were compressed. Some context may be lost.]"
        except Exception as e:
            # Fallback to simple truncation on any error
            print(f"[Scheduler] LLM compaction error: {e}, using fallback")
            summary_content = f"[Context compacted: {len(messages_to_compact)} earlier messages were compressed. Some context may be lost.]"
        
        summary_message = {
            'role': 'system',
            'content': summary_content,
            'metadata': {'type': 'compaction_summary', 'compacted_count': len(messages_to_compact)},
        }
        
        new_context = system_messages + [summary_message] + messages_to_keep
        
        new_tokens = estimate_tokens(new_context)
        
        print(f"[Scheduler] Compacted: {len(messages_to_compact)} messages removed, ~{estimated_tokens} -> ~{new_tokens} tokens ({new_tokens/context_limit*100:.1f}%)")
        
        return new_context
    
    def _fix_compaction_boundary(
        self, 
        all_messages: List[Dict[str, Any]], 
        messages_to_keep: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fix compaction boundary to ensure tool_calls/tool_result pairs are complete.
        
        Problem: If compaction boundary cuts between assistant+tool_calls and its tool_result,
        the tool_result becomes an orphan, causing LLM API errors.
        
        Solution: 
        1. Find all tool_call_ids defined in kept assistant messages
        2. Remove any leading tool_results whose tool_call_id is not in kept messages
        """
        if not messages_to_keep:
            return messages_to_keep
        
        # Build set of tool_call_ids from assistant messages in messages_to_keep
        kept_tool_call_ids = set()
        for msg in messages_to_keep:
            if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                for tc in msg['tool_calls']:
                    tc_id = tc.get('id')
                    if tc_id:
                        kept_tool_call_ids.add(tc_id)
        
        # Remove leading orphan tool_results
        result = []
        found_valid_start = False
        orphan_count = 0
        
        for msg in messages_to_keep:
            if not found_valid_start and msg.get('role') == 'tool_result':
                tc_id = msg.get('tool_call_id')
                if tc_id and tc_id not in kept_tool_call_ids:
                    # This is an orphan tool_result at the start - skip it
                    orphan_count += 1
                    print(f"[Scheduler] Removing orphan tool_result from compaction boundary: {tc_id}")
                    continue
            
            found_valid_start = True
            result.append(msg)
        
        if orphan_count > 0:
            print(f"[Scheduler] Fixed compaction boundary: removed {orphan_count} orphan tool_result(s)")
        
        return result
    
    async def _get_subagent_type(self, agent_id: str, subagent_id: str) -> str:
        """Get subagent type from SubAgent record.
        
        Returns 'main' or 'sub' based on the actual database record,
        not guessing from the subagent_id name.
        """
        try:
            gateway = self.master.gateway
            resp = await gateway.client.get(
                f"{gateway.gateway_url}/internal/subagents/{agent_id}/{subagent_id}"
            )
            if resp.status_code == 200:
                subagent = resp.json()
                return subagent.get("type", "main")
        except Exception as e:
            print(f"[Scheduler] Error getting subagent type: {e}")
        
        # Fallback to 'main' if query fails
        return "main"
    
    async def _create_think_task(self, runtime: Dict[str, Any], context: List[Dict[str, Any]]) -> str:
        """Create a think task."""
        gateway = self.master.gateway
        
        task_id = f"think-{uuid.uuid4().hex[:12]}"
        round_id = runtime.get("current_round_id", "round-1")
        
        # v14: Use runtime_id for idempotency key
        runtime_id = runtime.get("runtime_id") or runtime.get("subagent_id")
        
        # Database-level idempotency: prevents duplicate think tasks from multiple Masters
        idempotency_key = f"{runtime['agent_id']}-{runtime_id}-{round_id}-think"
        
        # v14: Get subagent_type from SubAgent record (not guessing from name)
        subagent_id = runtime.get("subagent_id", "main")
        agent_id = runtime["agent_id"]
        subagent_type = await self._get_subagent_type(agent_id, subagent_id)
        
        success = await gateway.create_task(
            id=task_id,
            agent_id=runtime["agent_id"],
            subagent_id=runtime_id,  # v14: This is runtime_id in action_tasks table
            round_id=round_id,
            mcpcall_id="think",
            idempotency_key=idempotency_key,
            type="think",
            args={
                'context': context,
                'mcp_url': runtime.get("mcp_url"),
                'subagent_type': subagent_type,  # v14: 'main' or 'sub'
            }
        )
        
        if not success:
            print(f"[Scheduler] Think task creation blocked by idempotency: {idempotency_key}")
            return None  # Another Master already created this think task
        
        return task_id
    
    async def _handle_waiting_actions(self, runtime: Dict[str, Any]):
        """Phase 3+4: Check if actions are done, collect results."""
        gateway = self.master.gateway
        # v14: Use runtime_id
        runtime_id = runtime.get("runtime_id") or runtime.get("subagent_id")
        
        pending_ids = runtime.get("pending_actions", [])
        if not pending_ids:
            await self._advance_or_complete(runtime, [])
            return
        
        # Get task statuses
        tasks = await gateway.get_tasks(ids=pending_ids)
        
        # Check if all done, re-broadcast unclaimed tasks
        all_done = True
        results = []
        for task in tasks:
            task_id = task["id"]
            status = task["status"]
            
            if status == 'pending':
                print(f"[Scheduler] Re-broadcasting unclaimed task {task_id}")
                await self.master.broadcast_new_task(task_id, task["type"], runtime["agent_id"])
                all_done = False
            elif status in ('executing', 'blocked'):
                all_done = False
            else:
                args = task.get("args", {})
                tool_call_id = args.get('tool_call_id', '')
                
                results.append({
                    'task_id': task_id,
                    'type': task["type"],
                    'status': status,
                    'result': task.get("result"),
                    'error': task.get("error"),
                    'tool_call_id': tool_call_id,
                    'action': task.get("action"),
                })
        
        if not all_done:
            return  # Still waiting
        
        # All tasks done - try to claim processing rights (CAS)
        # This prevents two Masters from processing the same results
        current_phase = runtime.get("phase", "")
        claimed = await gateway.try_claim_phase(
            runtime_id, 
            expected_phase=current_phase,
            new_phase="processing_results"
        )
        
        if not claimed:
            print(f"[Scheduler] Runtime {runtime_id} results already being processed (CAS conflict)")
            return
        
        print(f"[Scheduler] Runtime {runtime_id} round {runtime.get('current_round_num', 1)} complete")
        await self._advance_or_complete(runtime, results)
    
    async def _advance_or_complete(self, runtime: Dict[str, Any], results: List[Dict[str, Any]]):
        """Decide whether to advance round or complete runtime.
        
        v14 Logic:
        - At round completion, check for unread messages
        - If messages: set status to 'active' (even if was resting), continue
        - If no messages: complete runtime
        """
        gateway = self.master.gateway
        # v14: Use runtime_id
        runtime_id = runtime.get("runtime_id") or runtime.get("subagent_id")
        agent_id = runtime["agent_id"]
        
        # Check if we got a 'done' action from think result
        think_result = None
        for r in results:
            if r['type'] == 'think' and r['result']:
                think_result = r['result']
                break
        
        if think_result:
            if not think_result.get('success', True):
                error = think_result.get('error', 'Unknown thinking error')
                print(f"[Scheduler] Runtime {runtime_id} think failed: {error}")
                await gateway.update_runtime(runtime_id, status="failed", error=error)
                return
            
            actions = think_result.get('actions', [])
            has_done = any(a.get('type') == 'done' for a in actions)
            action_tasks = [a for a in actions if a.get('type') != 'done']
            
            if action_tasks:
                # Add assistant message with tool_calls to context
                tool_calls = []
                for a in action_tasks:
                    if a.get('tool_call_id'):
                        tool_calls.append({
                            "id": a.get('tool_call_id'),
                            "type": "function",
                            "function": {
                                "name": a.get('tool'),
                                "arguments": json.dumps(a.get('args', {})),
                            }
                        })
                
                if tool_calls:
                    fresh_runtime = await gateway.get_runtime(runtime_id)
                    context = list(fresh_runtime.get("context", []) if fresh_runtime else runtime.get("context", []))
                    
                    # v15: 清理已被 LLM 处理过的图片数据
                    # Think 完成意味着 LLM 已经看到了 context 中的所有图片
                    # 现在可以安全地用 placeholder 替换，避免数据库膨胀
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
                    
                    assistant_msg = {
                        'role': 'assistant',
                        'content': think_result.get('reasoning', ''),
                        'tool_calls': tool_calls,
                    }
                    # For kimi-k2.5: include reasoning_content
                    reasoning = think_result.get('reasoning', '')
                    if reasoning:
                        assistant_msg['reasoning_content'] = reasoning
                    context.append(assistant_msg)
                    await gateway.update_runtime(runtime_id, context=context)
                
                # Create action tasks (pass mcp_session_id for tool calls)
                mcp_session_id = think_result.get('mcp_session_id')
                task_ids = await self._create_action_tasks(runtime, action_tasks, mcp_session_id)
                
                phase = 'waiting_actions_final' if has_done else 'waiting_actions'
                await gateway.update_runtime(runtime_id, phase=phase, pending_actions=task_ids)
                
                # Broadcast new tasks
                for i, task_id in enumerate(task_ids):
                    task_type = action_tasks[i].get('type', 'tool_call')
                    await self.master.broadcast_new_task(task_id, task_type, runtime["agent_id"])
                
                return  # Wait for action tasks
            
            if has_done:
                await self._complete_runtime(runtime)
                return
            
            print(f"[Scheduler] Runtime {runtime_id} returned no actions, completing")
            await self._complete_runtime(runtime)
            return
        
        # Add results to context (for non-think tasks)
        has_tool_results = False
        if results:
            fresh_runtime = await gateway.get_runtime(runtime_id)
            context = list(fresh_runtime.get("context", []) if fresh_runtime else runtime.get("context", []))
            for r in results:
                if r['result']:
                    has_tool_results = True
                    tool_call_id = r.get('tool_call_id') or ''
                    result_data = r['result']
                    
                    # v15: 保留完整结果（包括图片 base64）供 LLM Caller 提取
                    # 图片数据会在 LLM Caller 的 add_tool_result 中被提取并传给 LLM
                    # 然后存入 context 时会被 LLM Caller 处理（替换为 placeholder）
                    # 这样图片既能被 LLM 看到，又不会永久占用 context 空间
                    content = json.dumps(result_data) if isinstance(result_data, dict) else str(result_data)
                    
                    context.append({
                        'role': 'tool_result' if r['type'] != 'think' else 'assistant',
                        'content': content,
                        'tool_call_id': tool_call_id,
                        'tool_name': r.get('action', 'tool'),
                    })
            await gateway.update_runtime(runtime_id, context=context)
        
        # v14: Check if runtime entered resting state (via runtime_rest tool)
        # Re-fetch runtime to get latest status
        fresh_runtime = await gateway.get_runtime(runtime_id)
        current_status = fresh_runtime.get("status", "active") if fresh_runtime else "active"
        
        # ReACT loop: If we just executed tool calls, continue to next think round
        # to let LLM see the results and decide next action (reflection)
        if has_tool_results and current_status != "resting":
            # Tool results received - advance to next round for reflection
            current_round_num = runtime.get("current_round_num", 1)
            new_round_id = await gateway.advance_round(runtime_id, expected_round_num=current_round_num)
            
            if new_round_id:
                print(f"[Scheduler] Runtime {runtime_id} tool results received, advancing to {new_round_id} for reflection")
            else:
                print(f"[Scheduler] Runtime {runtime_id} advance failed (CAS conflict)")
            return
        
        # v14: At round completion, check for unread messages
        has_unread = await gateway.has_unread_messages(agent_id)
        
        if has_unread:
            # Has new messages - continue even if was resting
            if current_status == "resting":
                print(f"[Scheduler] Runtime {runtime_id} has new messages, canceling rest and continuing")
                await gateway.update_runtime(runtime_id, status="active")
            
            # Advance to next round (atomic CAS)
            current_round_num = runtime.get("current_round_num", 1)
            new_round_id = await gateway.advance_round(runtime_id, expected_round_num=current_round_num)
            
            if new_round_id:
                print(f"[Scheduler] Runtime {runtime_id} advanced to {new_round_id}")
            else:
                print(f"[Scheduler] Runtime {runtime_id} advance failed (CAS conflict)")
            return
        
        # No new messages - complete runtime
        if current_status == "resting":
            print(f"[Scheduler] Runtime {runtime_id} resting with no new messages, completing")
        elif runtime.get("phase") == 'waiting_actions_final':
            print(f"[Scheduler] Runtime {runtime_id} actions done, completing (final)")
        else:
            print(f"[Scheduler] Runtime {runtime_id} no new messages, completing")
        
        await self._complete_runtime(fresh_runtime or runtime)
    
    async def _create_action_tasks(
        self, 
        runtime: Dict[str, Any], 
        actions: List[Dict[str, Any]],
        mcp_session_id: Optional[str] = None
    ) -> List[str]:
        """Create action tasks from LLM actions."""
        gateway = self.master.gateway
        task_ids = []
        
        # v14: Use runtime_id
        runtime_id = runtime.get("runtime_id") or runtime.get("subagent_id")
        
        for i, action in enumerate(actions):
            task_id = f"action-{uuid.uuid4().hex[:12]}"
            mcpcall_id = f"mc-{i+1}"
            idempotency_key = f"{runtime['agent_id']}-{runtime_id}-{runtime.get('current_round_id', 'round-1')}-{mcpcall_id}"
            
            action_type = action.get('type', 'tool_call')
            tool_name = action.get('tool') or action.get('name')
            tool_args = action.get('args', {})
            tool_call_id = action.get('tool_call_id', '')
            
            task_args = {
                'tool_args': tool_args,
                'mcp_url': runtime.get("mcp_url"),
                'tool_call_id': tool_call_id,
                'mcp_session_id': mcp_session_id,  # Session ID for MCP calls
            }
            
            success = await gateway.create_task(
                id=task_id,
                agent_id=runtime["agent_id"],
                subagent_id=runtime_id,  # v14: This is runtime_id in action_tasks table
                round_id=runtime.get("current_round_id", "round-1"),
                mcpcall_id=mcpcall_id,
                idempotency_key=idempotency_key,
                type=action_type,
                action=tool_name,
                args=task_args,
            )
            
            if success:
                task_ids.append(task_id)
            else:
                print(f"[Scheduler] Task creation failed (idempotency): {idempotency_key}")
        
        return task_ids
    
    async def _complete_runtime(self, runtime: Dict[str, Any]):
        """Complete a runtime and trigger Summarizer.
        
        v14: 
        - Mark runtime as completed
        - Trigger Summarizer to generate summary
        - Update SubAgent status to sleeping/summarizing
        """
        gateway = self.master.gateway
        # v14: Use runtime_id
        runtime_id = runtime.get("runtime_id") or runtime.get("subagent_id")
        subagent_id = runtime.get("subagent_id", "main")
        agent_id = runtime["agent_id"]
        
        current_status = runtime.get("status", "active")
        print(f"[Scheduler] Completing runtime {runtime_id} (status: {current_status})")
        
        # Clean up processed states for this runtime (prevent memory leak)
        self._processed_states = {
            s for s in self._processed_states 
            if s[0] != runtime_id
        }
        
        # Mark runtime as completed
        await gateway.update_runtime(runtime_id, status="completed", phase="completed")
        
        # v14: Trigger Summarizer to generate summary (async)
        # The Summarizer will set SubAgent status appropriately
        try:
            await self.master.process_completed_runtime(runtime_id, subagent_id, agent_id)
        except Exception as e:
            print(f"[Scheduler] Warning: Could not trigger summarizer: {e}")
            # Fall back to just setting SubAgent to sleeping
            try:
                await gateway.set_subagent_sleeping(agent_id, subagent_id)
            except Exception as e2:
                print(f"[Scheduler] Warning: Could not set subagent sleeping: {e2}")
