"""
LLM API
"""

from typing import Dict, Any, List
from .base import BaseAPI


class LlmAPI(BaseAPI):
    """
    LLM operations.
    
    Usage:
        result = await sdk.llm.compact_context(agent_id, messages)
        summary = result["summary"]
    """
    
    async def compact_context(
        self,
        agent_id: str,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compact conversation context using LLM summarization.
        
        Takes a list of messages and produces a shorter summary
        while preserving key information.
        
        Args:
            agent_id: Agent for context (used to get LLM config)
            messages: Messages to summarize
        
        Returns:
            {
                "success": bool,
                "summary": str,      # Summarized content
                "error": str,        # Error if failed
                "input_tokens": int,
                "output_tokens": int
            }
        """
        return await self._http.post(
            f"{self.gateway_url}/internal/llm/compact-context",
            json={
                "agent_id": agent_id,
                "messages": messages,
            },
            timeout=120.0,  # LLM calls can take longer
        )
