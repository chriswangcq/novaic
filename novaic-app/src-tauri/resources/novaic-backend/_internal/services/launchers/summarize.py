"""
SummarizeLauncher

Creates a summarize async task for completed runtime.

Pre-logic:
- Check if runtime needs summary (context length)
- Prepare context for summarization

Creates one async task: summarize (or none if simple summary suffices)
"""

import json
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from ..launcher_worker import BaseLauncher, LauncherWorker

if TYPE_CHECKING:
    from ..gateway_client import GatewayClient


SUMMARY_THRESHOLD_TOKENS = 1000


@LauncherWorker.register("summarize_launcher")
class SummarizeLauncher(BaseLauncher):
    """
    Launcher that creates summarize task or does simple summary.
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
        Check if LLM summary needed, create task if so.
        """
        # Get runtime_id from args (REQUIRED)
        actual_runtime_id = args.get("runtime_id")
        if not actual_runtime_id:
            raise ValueError(f"runtime_id not found in args: {args}")
        
        # Get Runtime via Gateway API
        runtime = await self.client.get_runtime(actual_runtime_id)
        
        if not runtime:
            raise ValueError(f"Runtime not found: {actual_runtime_id}")
        
        subagent_id = runtime.get("subagent_id")
        actual_agent_id = runtime.get("agent_id")
        if not actual_agent_id:
            raise ValueError(f"agent_id not found in Runtime {actual_runtime_id}")
        
        # Get context
        context = runtime.get("context", [])
        if isinstance(context, str):
            try:
                context = json.loads(context)
            except:
                context = []
        
        # Check if needs LLM summary
        needs_llm = self._needs_llm_summary(context)
        
        async_task_ids = []
        simple_summary = None
        
        if needs_llm:
            # Create summarize async task
            task_id = await self.create_async_task(
                task_subtype="summarize",
                runtime_id=actual_runtime_id,
                stage_id=stage_id,
                agent_id=actual_agent_id,  # Use actual_agent_id from Runtime
                args={
                    "context": context,
                },
                idempotency_key=f"{actual_runtime_id}-summarize",
            )
            if not task_id:
                raise ValueError(f"Failed to create summarize task for runtime {actual_runtime_id}")
            async_task_ids.append(task_id)
        else:
            # Generate simple summary now
            simple_summary = self._simple_summary(context)
            
            # Save summary immediately via Gateway API
            if simple_summary:
                await self.client.update_runtime(actual_runtime_id, summary=simple_summary)
        
        # Mark runtime as completing via Gateway API
        await self.client.update_runtime(
            actual_runtime_id,
            phase="completing",
            status="completed",
        )
        
        return {
            "async_task_ids": async_task_ids,
            "collector_args": {
                "agent_id": actual_agent_id,  # REQUIRED for cleanup operations
                "runtime_id": actual_runtime_id,
                "subagent_id": subagent_id,
                "simple_summary": simple_summary,
            },
            "next_stage_type": None,  # End of pipeline
        }
    
    def _needs_llm_summary(self, context: List[Dict[str, Any]]) -> bool:
        """Check if context needs LLM compression."""
        if not context:
            return False
        
        # Filter out injected history
        new_messages = [
            msg for msg in context
            if not msg.get('metadata', {}).get('type') in 
               ('historical_summary', 'runtime_summary', 'compaction_summary')
        ]
        
        if not new_messages:
            return False
        
        # Estimate tokens
        total_chars = sum(len(str(msg.get('content', ''))) + 50 for msg in new_messages)
        estimated_tokens = total_chars // 4
        
        return estimated_tokens > SUMMARY_THRESHOLD_TOKENS
    
    def _simple_summary(self, context: List[Dict[str, Any]]) -> str:
        """Create simple summary from context."""
        parts = []
        
        for msg in context:
            role = msg.get('role', '')
            content = msg.get('content', '')
            metadata = msg.get('metadata', {})
            
            if metadata.get('type') in ('historical_summary', 'runtime_summary', 'compaction_summary'):
                continue
            
            if role == 'user':
                if isinstance(content, str) and content.strip():
                    text = content.strip()
                    if len(text) > 100:
                        text = text[:100] + '...'
                    parts.append(f"User: {text}")
            
            elif role == 'assistant':
                tool_calls = msg.get('tool_calls', [])
                for tc in tool_calls:
                    func = tc.get('function', {})
                    name = func.get('name', '')
                    
                    if name == 'chat_reply':
                        args = func.get('arguments', {})
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except:
                                pass
                        reply = args.get('message', '') if isinstance(args, dict) else ''
                        if reply:
                            if len(reply) > 100:
                                reply = reply[:100] + '...'
                            parts.append(f"Agent: {reply}")
                    elif name not in ('runtime_rest', 'runtime_complete'):
                        parts.append(f"Agent called: {name}")
        
        if not parts:
            return ""
        
        return " | ".join(parts)
