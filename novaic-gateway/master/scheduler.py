"""
Scheduler Component

Drives the ReACT loop for each active Runtime.
Handles:
- Phase 1: THINK - Prepare context, create think task
- Phase 2: SCHEDULE - Process actions, create action tasks
- Phase 3: EXECUTE - Broadcast tasks to Workers
- Phase 4: COLLECT - Wait for results, advance Round
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from .master import Master

from db.repositories import AgentRuntime


class Scheduler:
    """Schedules and drives Runtime execution."""
    
    def __init__(self, master: 'Master'):
        self.master = master
        self.running = False
        self.loop_interval = 0.1  # seconds (fast polling)
        self._task = None
        
        # Track Runtimes being processed to avoid double-scheduling
        self._processing: set = set()
    
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
        runtime_repo = self.master.runtime_repo
        
        # Get all active runtimes
        runtimes = await runtime_repo.get_all_active_runtimes()
        
        for runtime in runtimes:
            # Skip if already being processed
            if runtime.subagent_id in self._processing:
                continue
            
            # v2.9: Add to processing BEFORE creating task to prevent race condition
            # asyncio.create_task is async, so without this, the same runtime
            # could be scheduled multiple times before _drive_runtime starts
            self._processing.add(runtime.subagent_id)
            
            # Drive this runtime based on its phase
            asyncio.create_task(self._drive_runtime(runtime))
    
    async def _drive_runtime(self, runtime: AgentRuntime):
        """Drive a single runtime through its current phase."""
        # v2.9: _processing.add is now done in _schedule_runtimes before create_task
        # to prevent race condition
        
        try:
            # v2.9: Re-read runtime from DB to get latest state
            # This prevents acting on stale data when Scheduler loop runs fast
            fresh_runtime = await self.master.runtime_repo.get_by_id(runtime.subagent_id)
            if not fresh_runtime or fresh_runtime.status != 'active':
                return  # Runtime no longer active
            
            runtime = fresh_runtime
            
            if runtime.phase == 'need_think':
                await self._handle_need_think(runtime)
            elif runtime.phase in ('waiting_actions', 'waiting_actions_final'):
                # v14: waiting_actions_final 表示 actions 完成后应该结束 runtime
                await self._handle_waiting_actions(runtime)
            # 'completed' phase - no action needed
        except Exception as e:
            print(f"[Scheduler] Error driving runtime {runtime.subagent_id}: {e}")
            import traceback
            traceback.print_exc()
            # Mark runtime as failed
            await self.master.runtime_repo.mark_failed(runtime.subagent_id, str(e))
        finally:
            self._processing.discard(runtime.subagent_id)
    
    async def _handle_need_think(self, runtime: AgentRuntime):
        """Phase 1: THINK - Create think task for Worker."""
        print(f"[Scheduler] Runtime {runtime.subagent_id} needs think (round {runtime.current_round_num})")
        
        # 1. Prepare context
        context = await self._prepare_context(runtime)
        
        # 2. Create think task
        task_id = await self._create_think_task(runtime, context)
        
        # 3. Update runtime state
        await self.master.runtime_repo.set_pending_actions(runtime.subagent_id, [task_id])
        
        # 4. Broadcast SSE
        await self.master.broadcast_new_task(task_id, 'think', runtime.agent_id)
        
        print(f"[Scheduler] Created think task {task_id} for runtime {runtime.subagent_id}")
    
    async def _prepare_context(self, runtime: AgentRuntime) -> List[Dict[str, Any]]:
        """Prepare context for thinking, including inbox messages.
        
        Context management:
        1. Start with existing context (preserved across wake/sleep cycles)
        2. Add unread inbox messages
        3. Compact if context exceeds threshold (keep recent 10 rounds)
        """
        db = self.master.db
        
        # Start with existing context (preserved across wake/sleep)
        context = list(runtime.context)
        
        # Get unread inbox messages
        async with db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT id, type, content, metadata, timestamp 
                FROM chat_messages 
                WHERE agent_id = ? AND read = 0 AND processed = 0
                ORDER BY timestamp ASC
            """, (runtime.agent_id,))
            messages = await cursor.fetchall()
            
            # Mark messages as read
            if messages:
                msg_ids = [m[0] for m in messages]
                placeholders = ','.join(['?'] * len(msg_ids))
                await conn.execute(f"""
                    UPDATE chat_messages SET read = 1 WHERE id IN ({placeholders})
                """, msg_ids)
                await conn.commit()
        
        # Add inbox messages to context
        inbox_message_ids = []
        for msg in messages:
            msg_id, msg_type, content, metadata, timestamp = msg
            inbox_message_ids.append(msg_id)
            context.append({
                'role': 'user' if msg_type == 'USER_MESSAGE' else 'system',
                'content': content,
                'metadata': json.loads(metadata) if metadata else {},
                'timestamp': timestamp,
                'message_id': msg_id,
            })
        
        # v2.9: Also mark messages as processed to prevent Monitor from re-waking
        if inbox_message_ids:
            async with db.get_connection() as conn:
                placeholders = ','.join(['?'] * len(inbox_message_ids))
                await conn.execute(f"""
                    UPDATE chat_messages SET processed = 1 WHERE id IN ({placeholders})
                """, inbox_message_ids)
                await conn.commit()
        
        # Context compaction: keep recent messages if context is too large
        context = self._compact_context_if_needed(context)
        
        # Update runtime context (persisted for next round and wake/sleep)
        await self.master.runtime_repo.update_context(runtime.subagent_id, context)
        
        return context
    
    def _compact_context_if_needed(
        self, 
        context: List[Dict[str, Any]],
        max_tokens: int = 100000,  # ~70% of 128k context
        min_messages_to_keep: int = 20,  # ~10 rounds (user + assistant pairs)
    ) -> List[Dict[str, Any]]:
        """Compact context if it exceeds token threshold.
        
        Simple compaction strategy:
        1. Estimate token count
        2. If over threshold, keep system messages + recent messages
        3. Add a summary marker for truncated history
        
        Args:
            context: Current context messages
            max_tokens: Max token threshold to trigger compaction
            min_messages_to_keep: Minimum number of recent messages to keep
        
        Returns:
            Compacted context
        """
        if len(context) <= min_messages_to_keep:
            return context
        
        # Estimate tokens (rough: ~4 chars per token)
        total_chars = sum(
            len(str(msg.get('content', ''))) + 50  # +50 for role/metadata overhead
            for msg in context
        )
        estimated_tokens = total_chars // 4
        
        if estimated_tokens <= max_tokens:
            return context
        
        print(f"[Scheduler] Context compaction triggered: ~{estimated_tokens} tokens > {max_tokens} threshold")
        
        # Separate system messages (keep all) and conversation messages
        system_messages = [m for m in context if m.get('role') == 'system' and 'compaction_summary' not in str(m.get('metadata', {}))]
        conversation_messages = [m for m in context if m.get('role') != 'system' or 'compaction_summary' in str(m.get('metadata', {}))]
        
        # Keep recent conversation messages
        messages_to_keep = conversation_messages[-min_messages_to_keep:]
        messages_to_compact = conversation_messages[:-min_messages_to_keep] if len(conversation_messages) > min_messages_to_keep else []
        
        if not messages_to_compact:
            return context
        
        # Create a simple summary marker (LLM-based summary can be added later)
        summary_message = {
            'role': 'system',
            'content': f"[Context compacted: {len(messages_to_compact)} earlier messages were truncated to stay within context limits. The conversation continues from the recent messages below.]",
            'metadata': {'type': 'compaction_summary', 'compacted_count': len(messages_to_compact)},
        }
        
        # Build new context: system messages + summary + recent messages
        new_context = system_messages + [summary_message] + messages_to_keep
        
        new_chars = sum(len(str(m.get('content', ''))) + 50 for m in new_context)
        new_tokens = new_chars // 4
        
        print(f"[Scheduler] Compacted: {len(messages_to_compact)} messages removed, ~{estimated_tokens - new_tokens} tokens saved")
        
        return new_context
    
    async def _create_think_task(self, runtime: AgentRuntime, context: List[Dict[str, Any]]) -> str:
        """Create a think task in action_tasks table."""
        db = self.master.db
        
        task_id = f"think-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        async with db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO action_tasks (
                    id, agent_id, subagent_id, round_id, mcpcall_id,
                    type, args, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                runtime.agent_id,
                runtime.subagent_id,
                runtime.current_round_id,
                'think',  # mcpcall_id for think task
                'think',  # type
                json.dumps({
                    'context': context,
                    'mcp_url': runtime.mcp_url,  # Runtime MCP URL from runtime record
                }),
                'pending',
                now,
            ))
            await conn.commit()
        
        return task_id
    
    async def _handle_waiting_actions(self, runtime: AgentRuntime):
        """Phase 3+4: Check if actions are done, collect results."""
        db = self.master.db
        
        # Check if all pending actions are complete
        pending_ids = runtime.pending_actions
        if not pending_ids:
            # No pending actions, advance round
            await self._advance_or_complete(runtime, [])
            return
        
        # Get task statuses
        placeholders = ','.join(['?'] * len(pending_ids))
        async with db.get_connection() as conn:
            cursor = await conn.execute(f"""
                SELECT id, status, result, error, type, args, action 
                FROM action_tasks 
                WHERE id IN ({placeholders})
            """, pending_ids)
            tasks = await cursor.fetchall()
        
        # Check if all done, re-broadcast unclaimed tasks
        all_done = True
        results = []
        for task in tasks:
            task_id, status, result, error, task_type, args_json, action = task
            if status == 'pending':
                # Task not claimed yet, re-broadcast
                print(f"[Scheduler] Re-broadcasting unclaimed task {task_id}")
                await self.master.broadcast_new_task(task_id, task_type, runtime.agent_id)
                all_done = False
            elif status in ('executing', 'blocked'):
                all_done = False
            else:
                # v12: 解析 args 获取 tool_call_id
                args = json.loads(args_json) if args_json else {}
                tool_call_id = args.get('tool_call_id', '')
                
                results.append({
                    'task_id': task_id,
                    'type': task_type,
                    'status': status,
                    'result': json.loads(result) if result else None,
                    'error': error,
                    'tool_call_id': tool_call_id,  # v12: 传递 tool_call_id
                    'action': action,  # v12: 工具名
                })
        
        if not all_done:
            return  # Still waiting
        
        # All actions done, process results
        print(f"[Scheduler] Runtime {runtime.subagent_id} round {runtime.current_round_num} complete")
        await self._advance_or_complete(runtime, results)
    
    async def _advance_or_complete(self, runtime: AgentRuntime, results: List[Dict[str, Any]]):
        """Decide whether to advance round or complete runtime."""
        # Check if we got a 'done' action from think result
        think_result = None
        for r in results:
            if r['type'] == 'think' and r['result']:
                think_result = r['result']
                break
        
        if think_result:
            # Check if thinking was successful
            if not think_result.get('success', True):
                # Thinking failed, mark runtime as failed
                error = think_result.get('error', 'Unknown thinking error')
                print(f"[Scheduler] Runtime {runtime.subagent_id} think failed: {error}")
                await self.master.runtime_repo.mark_failed(runtime.subagent_id, error)
                return
            
            actions = think_result.get('actions', [])
            
            # Check for 'done' action (is_final 会自动插入 done，所以只检查 has_done 即可)
            has_done = any(a.get('type') == 'done' for a in actions)
            
            # Filter out 'done' and create tasks for other actions
            action_tasks = [a for a in actions if a.get('type') != 'done']
            
            if action_tasks:
                # v12: 先添加 assistant 消息（包含 tool_calls）到 context
                # OpenAI/Kimi 要求 tool_result 消息之前必须有对应的 assistant 消息
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
                    # v13: 重新读取 runtime 以获取最新 context（包含 inbox messages）
                    # context(n+1) = input(n) + assistant + tool_results
                    fresh_runtime = await self.master.runtime_repo.get_by_id(runtime.subagent_id)
                    context = list(fresh_runtime.context) if fresh_runtime else list(runtime.context)
                    context.append({
                        'role': 'assistant',
                        'content': think_result.get('reasoning', ''),
                        'tool_calls': tool_calls,
                    })
                    await self.master.runtime_repo.update_context(runtime.subagent_id, context)
                
                # Create action tasks and wait for them
                task_ids = await self._create_action_tasks(runtime, action_tasks)
                
                # v14: 如果 has_done，使用 waiting_actions_final phase，否则用 waiting_actions
                # 这样 action tasks 完成后知道是否应该完成 runtime
                phase = 'waiting_actions_final' if has_done else 'waiting_actions'
                await self.master.runtime_repo.set_pending_actions(runtime.subagent_id, task_ids, phase)
                
                # Broadcast new tasks with correct type
                for i, task_id in enumerate(task_ids):
                    task_type = action_tasks[i].get('type', 'tool_call')
                    await self.master.broadcast_new_task(task_id, task_type, runtime.agent_id)
                
                return  # Wait for action tasks
            
            # No action tasks - check if we should complete
            if has_done:
                # Agent is done
                await self._complete_runtime(runtime)
                return
            
            # No actions and no done flag - this shouldn't happen normally
            # Complete the runtime to avoid infinite loop
            print(f"[Scheduler] Runtime {runtime.subagent_id} returned no actions, completing")
            await self._complete_runtime(runtime)
            return
        
        # Add results to context (for non-think tasks like tool_call results)
        if results:
            # v13: 重新读取 runtime 以获取最新 context（包含 assistant 消息）
            # context(n+1) = input(n) + assistant + tool_results
            fresh_runtime = await self.master.runtime_repo.get_by_id(runtime.subagent_id)
            context = list(fresh_runtime.context) if fresh_runtime else list(runtime.context)
            for r in results:
                if r['result']:
                    # v12: 使用 tool_call_id，不要 fallback 到 task_id
                    # LLM 需要 tool_call_id 来匹配 tool 返回结果
                    # task_id 是内部 ID，LLM 不认识，会报错 "tool_call_id is not found"
                    tool_call_id = r.get('tool_call_id') or ''
                    context.append({
                        'role': 'tool_result' if r['type'] != 'think' else 'assistant',
                        'content': json.dumps(r['result']) if isinstance(r['result'], dict) else str(r['result']),
                        'tool_call_id': tool_call_id,  # v12: 使用正确的 tool_call_id
                        'tool_name': r.get('action', 'tool'),  # v12: 工具名
                    })
            await self.master.runtime_repo.update_context(runtime.subagent_id, context)
        
        # v14: 检查 phase 是否是 waiting_actions_final，如果是则完成 runtime
        # 这处理了 LLM 返回 final_answer 时的 chat_reply 场景
        if runtime.phase == 'waiting_actions_final':
            print(f"[Scheduler] Runtime {runtime.subagent_id} actions done, completing (final)")
            await self._complete_runtime(runtime)
            return
        
        # Check if max rounds reached
        max_rounds = 50  # Configurable
        if runtime.current_round_num >= max_rounds:
            print(f"[Scheduler] Runtime {runtime.subagent_id} reached max rounds")
            await self._complete_runtime(runtime)
            return
        
        # Advance to next round
        new_round_id = await self.master.runtime_repo.advance_round(runtime.subagent_id)
        print(f"[Scheduler] Runtime {runtime.subagent_id} advanced to {new_round_id}")
    
    async def _create_action_tasks(self, runtime: AgentRuntime, actions: List[Dict[str, Any]]) -> List[str]:
        """Create action tasks from LLM actions."""
        db = self.master.db
        task_ids = []
        now = datetime.utcnow().isoformat()
        
        async with db.get_connection() as conn:
            for i, action in enumerate(actions):
                task_id = f"action-{uuid.uuid4().hex[:12]}"
                mcpcall_id = f"mc-{i+1}"
                idempotency_key = f"{runtime.agent_id}-{runtime.subagent_id}-{runtime.current_round_id}-{mcpcall_id}"
                
                action_type = action.get('type', 'tool_call')
                tool_name = action.get('tool') or action.get('name')
                tool_args = action.get('args', {})
                tool_call_id = action.get('tool_call_id', '')  # v12: 保存 LLM 返回的 tool_call_id
                
                # Include MCP URL and tool_call_id in task args
                task_args = {
                    'tool_args': tool_args,
                    'mcp_url': runtime.mcp_url,  # Runtime MCP URL from runtime record
                    'tool_call_id': tool_call_id,  # v12: 用于返回结果时匹配
                }
                
                await conn.execute("""
                    INSERT INTO action_tasks (
                        id, agent_id, subagent_id, round_id, mcpcall_id,
                        idempotency_key, type, action, args, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    runtime.agent_id,
                    runtime.subagent_id,
                    runtime.current_round_id,
                    mcpcall_id,
                    idempotency_key,
                    action_type,
                    tool_name,
                    json.dumps(task_args),
                    'pending',
                    now,
                ))
                task_ids.append(task_id)
            
            await conn.commit()
        
        return task_ids
    
    async def _complete_runtime(self, runtime: AgentRuntime):
        """Complete a runtime and check if agent should sleep."""
        print(f"[Scheduler] Completing runtime {runtime.subagent_id}")
        
        # Mark runtime as completed
        await self.master.runtime_repo.mark_completed(runtime.subagent_id)
        
        # If this was a SubAgent, notify parent
        if runtime.parent_subagent_id:
            # TODO: Update parent's pending subagent task with result
            pass
        
        # Check if agent should sleep
        if runtime.type == 'main':
            # Check for other active runtimes
            active_runtimes = await self.master.runtime_repo.get_active_runtimes(runtime.agent_id)
            
            # Check inbox
            db = self.master.db
            async with db.get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT COUNT(*) FROM chat_messages 
                    WHERE agent_id = ? AND read = 0 AND processed = 0
                """, (runtime.agent_id,))
                (unread_count,) = await cursor.fetchone()
            
            if not active_runtimes and unread_count == 0:
                # No active runtimes and inbox empty, set to sleep
                print(f"[Scheduler] Agent {runtime.agent_id} going to sleep")
                await self.master.set_agent_sleep(runtime.agent_id)
