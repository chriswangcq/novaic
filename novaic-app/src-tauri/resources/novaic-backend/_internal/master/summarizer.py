"""
Summarizer Component (v14)

Handles runtime summary generation and sliding window management.
When a runtime completes:
1. Generate summary if context > 1000 tokens
2. Check if need to merge old summaries (>30 unmerged runtimes)
3. Update SubAgent historical_summary
4. Set SubAgent status to sleeping

v14: New component for SubAgent state refactor.
"""

import asyncio
from typing import TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from .master import Master


# Threshold for generating summary (in estimated tokens)
SUMMARY_THRESHOLD_TOKENS = 1000

# Sliding window parameters
MAX_UNMERGED_RUNTIMES = 30
RUNTIMES_TO_KEEP = 10


class Summarizer:
    """Generates runtime summaries and manages sliding window."""
    
    def __init__(self, master: 'Master'):
        self.master = master
    
    async def process_completed_runtime(
        self, 
        runtime_id: str, 
        subagent_id: str, 
        agent_id: str
    ):
        """Process a completed runtime, generate summary if needed.
        
        Args:
            runtime_id: The completed runtime ID
            subagent_id: The SubAgent ID (e.g., "main")
            agent_id: The VM Agent ID
        """
        gateway = self.master.gateway
        
        # Get runtime details
        runtime = await gateway.get_runtime(runtime_id)
        if not runtime:
            print(f"[Summarizer] Runtime {runtime_id} not found")
            await gateway.set_subagent_sleeping(agent_id, subagent_id)
            return
        
        context = runtime.get("context", [])
        
        # Always generate summary for completed runtimes
        if context:
            try:
                if self._needs_llm_summary(context):
                    # Long context: use LLM to compress
                    await gateway.set_subagent_summarizing(agent_id, subagent_id)
                    summary = await self._generate_summary(agent_id, context)
                    if summary:
                        await gateway.update_runtime(runtime_id, summary=summary)
                        print(f"[Summarizer] Generated LLM summary for runtime {runtime_id}")
                else:
                    # Short context: just concatenate messages directly
                    summary = self._simple_summary(context)
                    if summary:
                        await gateway.update_runtime(runtime_id, summary=summary)
                        print(f"[Summarizer] Generated simple summary for runtime {runtime_id}")
            except Exception as e:
                print(f"[Summarizer] Failed to generate summary: {e}")
        
        # Check if need to merge old runtimes
        try:
            await self._check_and_merge_if_needed(agent_id, subagent_id)
        except Exception as e:
            print(f"[Summarizer] Failed to merge old runtimes: {e}")
        
        # Set SubAgent to sleeping
        await gateway.set_subagent_sleeping(agent_id, subagent_id)
        print(f"[Summarizer] SubAgent {subagent_id} set to sleeping")
    
    def _needs_llm_summary(self, context: List[Dict[str, Any]]) -> bool:
        """Check if context exceeds threshold and needs LLM compression.
        
        Only counts new messages in this runtime, not injected history.
        """
        if not context:
            return False
        
        # Filter out injected history (only count new messages)
        new_messages = [
            msg for msg in context
            if not msg.get('metadata', {}).get('type') in ('historical_summary', 'runtime_summary', 'compaction_summary')
        ]
        
        if not new_messages:
            return False
        
        # Estimate tokens (rough: 4 chars per token)
        total_chars = sum(
            len(str(msg.get('content', ''))) + 50 
            for msg in new_messages
        )
        estimated_tokens = total_chars // 4
        
        return estimated_tokens > SUMMARY_THRESHOLD_TOKENS
    
    def _simple_summary(self, context: List[Dict[str, Any]]) -> str:
        """Create a simple summary by concatenating key messages.
        
        For short conversations, just extract user messages and assistant actions.
        """
        parts = []
        
        for msg in context:
            role = msg.get('role', '')
            content = msg.get('content', '')
            metadata = msg.get('metadata', {})
            
            # Skip system messages (existing summaries, etc.)
            if metadata.get('type') in ('historical_summary', 'runtime_summary', 'compaction_summary'):
                continue
            
            if role == 'user':
                # User message
                if isinstance(content, str) and content.strip():
                    parts.append(f"User: {content.strip()}")
            
            elif role == 'assistant':
                # Extract tool calls from assistant message
                tool_calls = msg.get('tool_calls', [])
                for tc in tool_calls:
                    func = tc.get('function', {})
                    name = func.get('name', '')
                    args = func.get('arguments', {})
                    
                    if name == 'chat_reply':
                        # Extract the reply content
                        if isinstance(args, str):
                            import json
                            try:
                                args = json.loads(args)
                            except:
                                pass
                        reply = args.get('message', '') if isinstance(args, dict) else ''
                        if reply:
                            # Truncate long replies
                            if len(reply) > 200:
                                reply = reply[:200] + '...'
                            parts.append(f"Agent: {reply}")
                    elif name not in ('runtime_rest', 'runtime_complete'):
                        # Record other tool calls (but not rest/complete)
                        parts.append(f"Agent called: {name}")
            
            elif role == 'tool_result':
                # Skip tool results in simple summary
                pass
        
        if not parts:
            return ""
        
        return " | ".join(parts)
    
    async def _generate_summary(
        self, 
        agent_id: str, 
        context: List[Dict[str, Any]]
    ) -> str:
        """Generate a summary of the runtime context using LLM."""
        gateway = self.master.gateway
        
        # Filter out system messages with existing summaries
        messages_to_summarize = [
            m for m in context
            if not (m.get('metadata', {}).get('type') in ('historical_summary', 'runtime_summary', 'compaction_summary'))
        ]
        
        if not messages_to_summarize:
            return ""
        
        try:
            result = await gateway.compact_context(agent_id, messages_to_summarize)
            
            if result.get("success") and result.get("summary"):
                return result["summary"]
            else:
                print(f"[Summarizer] LLM summary failed: {result.get('error', 'Unknown')}")
                return ""
        except Exception as e:
            print(f"[Summarizer] LLM summary error: {e}")
            return ""
    
    async def _check_and_merge_if_needed(self, agent_id: str, subagent_id: str):
        """Check if we need to merge old runtime summaries."""
        gateway = self.master.gateway
        
        # Get latest unmerged runtimes
        latest_runtimes = await gateway.get_latest_runtimes(agent_id, subagent_id, limit=50)
        
        if len(latest_runtimes) < MAX_UNMERGED_RUNTIMES:
            return  # Not enough to trigger merge
        
        print(f"[Summarizer] Merging old runtimes: {len(latest_runtimes)} > {MAX_UNMERGED_RUNTIMES}")
        
        # Split into old (to merge) and new (to keep)
        old_runtimes = latest_runtimes[:-RUNTIMES_TO_KEEP]  # All but the newest
        
        # Collect summaries to merge
        summaries_to_merge = [
            r.get("summary") 
            for r in old_runtimes 
            if r.get("summary")
        ]
        
        if not summaries_to_merge:
            # No summaries, just mark as merged
            runtime_ids = [r.get("runtime_id") for r in old_runtimes if r.get("runtime_id")]
            if runtime_ids:
                await self._mark_runtimes_merged(runtime_ids)
            return
        
        # Get current historical summary
        subagent = await gateway.get_subagent(agent_id, subagent_id)
        current_historical = subagent.get("historical_summary", "") if subagent else ""
        
        # Combine summaries
        combined_summary = await self._combine_summaries(
            agent_id, 
            current_historical, 
            summaries_to_merge
        )
        
        if combined_summary:
            # Update SubAgent historical summary
            await gateway.update_subagent(
                agent_id, 
                subagent_id, 
                historical_summary=combined_summary
            )
            print(f"[Summarizer] Updated historical summary for SubAgent {subagent_id}")
        
        # Mark old runtimes as merged
        runtime_ids = [r.get("runtime_id") for r in old_runtimes if r.get("runtime_id")]
        if runtime_ids:
            await self._mark_runtimes_merged(runtime_ids)
            print(f"[Summarizer] Marked {len(runtime_ids)} runtimes as merged")
    
    async def _combine_summaries(
        self, 
        agent_id: str,
        historical: str, 
        new_summaries: List[str]
    ) -> str:
        """Combine historical summary with new summaries using LLM.
        
        Keeps total length under MAX_HISTORICAL_LENGTH to prevent unbounded growth.
        """
        MAX_HISTORICAL_LENGTH = 8000  # Max chars for historical_summary
        
        gateway = self.master.gateway
        
        # Build context for combination
        all_content = []
        if historical:
            # If historical is already too long, truncate it
            if len(historical) > MAX_HISTORICAL_LENGTH // 2:
                historical = historical[:MAX_HISTORICAL_LENGTH // 2] + "\n...[truncated]"
            all_content.append(f"Previous Historical Summary:\n{historical}")
        
        for i, summary in enumerate(new_summaries):
            all_content.append(f"Session {i+1} Summary:\n{summary}")
        
        combined_text = "\n\n---\n\n".join(all_content)
        
        # Use LLM to combine and compress
        messages = [{
            'role': 'user',
            'content': f"Combine the following session summaries into a concise historical summary. Keep important context, task progress, and key decisions. Output should be under 2000 words.\n\n{combined_text}"
        }]
        
        try:
            result = await gateway.compact_context(agent_id, messages)
            
            if result.get("success") and result.get("summary"):
                summary = result["summary"]
                # Enforce max length
                if len(summary) > MAX_HISTORICAL_LENGTH:
                    summary = summary[:MAX_HISTORICAL_LENGTH] + "\n...[truncated]"
                return summary
            else:
                # Fallback: simple concatenation with truncation
                return combined_text[:MAX_HISTORICAL_LENGTH]
        except Exception as e:
            print(f"[Summarizer] Failed to combine summaries: {e}")
            return combined_text[:MAX_HISTORICAL_LENGTH]
    
    async def _mark_runtimes_merged(self, runtime_ids: List[str]):
        """Mark multiple runtimes as merged."""
        gateway = self.master.gateway
        
        for runtime_id in runtime_ids:
            try:
                await gateway.update_runtime(runtime_id, is_merged=True)
            except Exception as e:
                print(f"[Summarizer] Failed to mark runtime {runtime_id} as merged: {e}")
