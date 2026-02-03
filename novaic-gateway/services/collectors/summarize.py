"""
SummarizeCollector

Processes summary result and sets SubAgent status.

Post-logic:
- Save summary to runtime
- Check if should merge old summaries
- Set SubAgent status: 
  - main SubAgent -> sleeping
  - sub SubAgent (async spawn) -> completed
"""

import json
from typing import Dict, Any, List, TYPE_CHECKING

from ..collector_worker import BaseCollector, CollectorWorker

if TYPE_CHECKING:
    from ..gateway_client import GatewayClient


MAX_UNMERGED_RUNTIMES = 30
RUNTIMES_TO_KEEP = 10


@CollectorWorker.register("summarize_collector")
class SummarizeCollector(BaseCollector):
    """
    Collector that finalizes runtime and sets SubAgent status.
    
    For main SubAgents: sets to sleeping (can be woken by new messages)
    For sub SubAgents (async spawn): sets to completed (one-shot)
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
        Finalize runtime and set SubAgent status.
        """
        # Get runtime_id from args (REQUIRED)
        actual_runtime_id = args.get("runtime_id")
        if not actual_runtime_id:
            raise ValueError(f"runtime_id not found in args: {args}")
        
        subagent_id = args.get("subagent_id")
        simple_summary = args.get("simple_summary")
        is_failure = args.get("is_failure", False)
        
        # Get actual agent_id from Runtime (REQUIRED)
        runtime = await self.client.get_runtime(actual_runtime_id)
        if not runtime:
            raise ValueError(f"Runtime not found: {actual_runtime_id}")
        
        actual_agent_id = runtime.get("agent_id")
        if not actual_agent_id:
            raise ValueError(f"agent_id not found in Runtime {actual_runtime_id}")
        
        # Get LLM summary if async task was created
        llm_summary = None
        summarize_error = None
        for r in async_results:
            if r.get("task_subtype") == "summarize":
                if r.get("result"):
                    llm_summary = r["result"].get("summary")
                if r.get("error"):
                    summarize_error = r["error"]
                break
        
        # Check if summarize task failed
        if summarize_error and not llm_summary and not simple_summary:
            print(f"[SummarizeCollector] Summarize failed for {actual_runtime_id}: {summarize_error}")
            
            # Mark runtime as failed (if not already)
            if not is_failure:
                await self.client.update_runtime(
                    actual_runtime_id,
                    status="failed",
                    error=summarize_error,
                )
            
            # Set SubAgent to sleeping so it can be woken again
            if subagent_id:
                await self.client.set_subagent_sleeping(actual_agent_id, subagent_id)
                print(f"[SummarizeCollector] SubAgent {subagent_id} set to sleeping after summarize failure")
            
            # v18: Pipeline ends here. Monitor service will wake SubAgent when new messages arrive.
            return {
                "should_continue": False,
            }
        
        # Use LLM summary if available, otherwise simple summary
        final_summary = llm_summary or simple_summary
        
        if final_summary:
            await self.client.update_runtime(actual_runtime_id, summary=final_summary)
        
        # Handle failure case: runtime already marked as failed, just save summary
        if is_failure:
            print(f"[SummarizeCollector] Runtime {actual_runtime_id} failed, summary saved")
            
            # Set SubAgent to sleeping so it can be woken again
            if subagent_id:
                await self.client.set_subagent_sleeping(actual_agent_id, subagent_id)
                print(f"[SummarizeCollector] SubAgent {subagent_id} set to sleeping after failure summary")
            
            # v18: Pipeline ends here. Monitor service will wake SubAgent when new messages arrive.
            return {
                "should_continue": False,
            }
        
        # Mark runtime as completed via Gateway API
        await self.client.update_runtime(
            actual_runtime_id,
            status="completed",
            phase="completed",
        )
        
        # Set SubAgent status based on type
        if subagent_id:
            await self._check_and_merge(actual_agent_id, subagent_id)
            
            # Get SubAgent to check its type
            subagent = await self.client.get_subagent(actual_agent_id, subagent_id)
            
            if subagent and subagent.get("type") == "sub":
                # Sub SubAgent (async spawn) -> completed with result
                result_text = final_summary or "Task completed"
                await self.client.set_subagent_completed(actual_agent_id, subagent_id, result=result_text)
                print(f"[SummarizeCollector] Runtime {actual_runtime_id} completed, sub SubAgent {subagent_id} completed")
            else:
                # Main SubAgent -> sleeping (can be woken by new messages)
                await self.client.set_subagent_sleeping(actual_agent_id, subagent_id)
                print(f"[SummarizeCollector] Runtime {actual_runtime_id} completed, main SubAgent sleeping")
        else:
            print(f"[SummarizeCollector] Runtime {actual_runtime_id} completed")
        
        # v18: Pipeline ends here. Monitor service will wake SubAgent when new messages arrive.
        return {
            "should_continue": False,
        }
    
    async def _check_and_merge(self, agent_id: str, subagent_id: str):
        """Check if need to merge old runtime summaries."""
        # Get latest unmerged runtimes via Gateway API
        latest_runtimes = await self.client.get_latest_runtimes(
            agent_id, subagent_id, limit=50
        )
        
        # Filter unmerged
        unmerged = [r for r in latest_runtimes if not r.get("is_merged")]
        
        if len(unmerged) < MAX_UNMERGED_RUNTIMES:
            return
        
        print(f"[SummarizeCollector] Merging old runtimes: {len(unmerged)} > {MAX_UNMERGED_RUNTIMES}")
        
        # Split into old (to merge) and new (to keep)
        old_runtimes = unmerged[:-RUNTIMES_TO_KEEP]
        
        # Collect summaries
        summaries = [r.get("summary") for r in old_runtimes if r.get("summary")]
        
        if not summaries:
            # Just mark as merged
            for r in old_runtimes:
                rid = r.get("runtime_id")
                if rid:
                    await self.client.update_runtime(rid, is_merged=True)
            return
        
        # Get current historical summary via Gateway API
        subagent = await self.client.get_subagent(agent_id, subagent_id)
        current_historical = subagent.get("historical_summary", "") if subagent else ""
        
        # Use LLM to combine and compress summaries
        combined = await self._combine_summaries(agent_id, current_historical, summaries)
        
        if combined:
            # Update historical summary via Gateway API
            await self.client.update_subagent(
                agent_id, subagent_id,
                historical_summary=combined,
            )
        
        # Mark old runtimes as merged
        for r in old_runtimes:
            rid = r.get("runtime_id")
            if rid:
                await self.client.update_runtime(rid, is_merged=True)
        
        print(f"[SummarizeCollector] Merged {len(old_runtimes)} old runtimes")
    
    async def _combine_summaries(
        self,
        agent_id: str,
        historical: str,
        new_summaries: List[str],
    ) -> str:
        """
        Combine historical summary with new summaries using LLM.
        
        Keeps total length under MAX_HISTORICAL_LENGTH to prevent unbounded growth.
        """
        MAX_HISTORICAL_LENGTH = 8000
        
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
        
        # Use LLM to combine and compress via Gateway API
        messages = [{
            'role': 'user',
            'content': f"Combine the following session summaries into a concise historical summary. Keep important context, task progress, and key decisions. Output should be under 2000 words.\n\n{combined_text}"
        }]
        
        try:
            result = await self.client.compact_context(agent_id, messages)
            
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
            print(f"[SummarizeCollector] Failed to combine summaries: {e}")
            return combined_text[:MAX_HISTORICAL_LENGTH]
