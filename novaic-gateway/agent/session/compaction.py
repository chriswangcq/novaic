"""
Session Compaction - Context window management

Automatically compacts old messages into summaries to manage context window limits.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class Compactor:
    """
    Compacts session history to manage context window limits.
    
    When the session history exceeds a threshold, older messages are
    summarized by the LLM and replaced with a compact summary.
    
    This allows for effectively unlimited conversation length while
    staying within model context limits.
    """
    
    # Approximate tokens per character (conservative estimate)
    CHARS_PER_TOKEN = 4
    
    # Summary prompt template
    SUMMARY_PROMPT = """Summarize the following conversation history concisely, preserving:
1. Key decisions and conclusions made
2. Important facts and context established
3. Any pending tasks or commitments
4. The general flow and topic of discussion

Be concise but capture all critical information that would be needed to continue the conversation.

Conversation to summarize:
{messages}

Summary:"""
    
    def __init__(
        self,
        max_context_ratio: float = 0.8,
        compaction_ratio: float = 0.6,
        min_messages_to_keep: int = 4,
    ):
        """
        Initialize the compactor.
        
        Args:
            max_context_ratio: Trigger compaction when context exceeds this ratio of max
            compaction_ratio: Compact this ratio of messages (keep the rest)
            min_messages_to_keep: Always keep at least this many recent messages
        """
        self.max_context_ratio = max_context_ratio
        self.compaction_ratio = compaction_ratio
        self.min_messages_to_keep = min_messages_to_keep
    
    def estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Estimate token count for a list of messages.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Estimated token count
        """
        total_chars = 0
        
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                # Handle multi-part content (text + images)
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total_chars += len(part.get("text", ""))
            
            # Add overhead for role, metadata, etc.
            total_chars += 20
        
        return total_chars // self.CHARS_PER_TOKEN
    
    def should_compact(
        self,
        messages: List[Dict[str, Any]],
        model_context_size: int,
    ) -> bool:
        """
        Check if compaction is needed.
        
        Args:
            messages: Current message history
            model_context_size: Model's context window size in tokens
        
        Returns:
            True if compaction should be triggered
        """
        if len(messages) <= self.min_messages_to_keep:
            return False
        
        current_tokens = self.estimate_tokens(messages)
        threshold = int(model_context_size * self.max_context_ratio)
        
        should = current_tokens > threshold
        
        if should:
            logger.info(f"[Compactor] Compaction needed: {current_tokens} tokens > {threshold} threshold")
        
        return should
    
    def split_for_compaction(
        self,
        messages: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Split messages into parts to compact and parts to keep.
        
        Args:
            messages: All messages
        
        Returns:
            Tuple of (messages_to_compact, messages_to_keep)
        """
        total = len(messages)
        keep_count = max(
            self.min_messages_to_keep,
            int(total * (1 - self.compaction_ratio))
        )
        
        compact_count = total - keep_count
        
        return messages[:compact_count], messages[compact_count:]
    
    def format_messages_for_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages for the summary prompt."""
        lines = []
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                # Extract text parts only
                text_parts = [
                    p.get("text", "")
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                text = "\n".join(text_parts)
            else:
                text = str(content)
            
            # Truncate very long messages for summary
            if len(text) > 1000:
                text = text[:1000] + "... [truncated]"
            
            lines.append(f"{role.upper()}: {text}")
        
        return "\n\n".join(lines)
    
    async def compact(
        self,
        messages: List[Dict[str, Any]],
        llm_client,  # LLM client for generating summary
        model: str,
    ) -> Dict[str, Any]:
        """
        Perform compaction on the message history.
        
        Args:
            messages: Current message history
            llm_client: LLM client for generating summary
            model: Model to use for summary generation
        
        Returns:
            Dictionary with:
            - new_messages: The compacted message list
            - summary: The generated summary
            - stats: Compaction statistics
        """
        # Split messages
        to_compact, to_keep = self.split_for_compaction(messages)
        
        if not to_compact:
            return {
                "new_messages": messages,
                "summary": None,
                "stats": {"compacted": False, "reason": "No messages to compact"}
            }
        
        # Estimate tokens before
        original_tokens = self.estimate_tokens(messages)
        
        # Generate summary
        formatted = self.format_messages_for_summary(to_compact)
        prompt = self.SUMMARY_PROMPT.format(messages=formatted)
        
        try:
            response = await llm_client.chat(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise conversation summaries."},
                    {"role": "user", "content": prompt}
                ],
                model=model,
                max_tokens=1000,  # Limit summary length
            )
            
            summary = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except Exception as e:
            logger.error(f"[Compactor] Failed to generate summary: {e}")
            return {
                "new_messages": messages,
                "summary": None,
                "stats": {"compacted": False, "reason": f"Summary generation failed: {e}"}
            }
        
        # Create summary message
        summary_message = {
            "role": "system",
            "content": f"[Previous conversation summary]\n\n{summary}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "type": "compaction_summary",
                "compacted_count": len(to_compact),
            }
        }
        
        # Build new message list
        new_messages = [summary_message] + to_keep
        
        # Calculate stats
        new_tokens = self.estimate_tokens(new_messages)
        
        stats = {
            "compacted": True,
            "messages_compacted": len(to_compact),
            "messages_kept": len(to_keep),
            "original_tokens": original_tokens,
            "new_tokens": new_tokens,
            "tokens_saved": original_tokens - new_tokens,
            "compression_ratio": round(new_tokens / original_tokens, 2) if original_tokens > 0 else 1.0,
        }
        
        logger.info(f"[Compactor] Compacted {len(to_compact)} messages, "
                   f"saved {stats['tokens_saved']} tokens "
                   f"({stats['compression_ratio']:.0%} of original)")
        
        return {
            "new_messages": new_messages,
            "summary": summary,
            "stats": stats,
        }
    
    async def auto_compact_if_needed(
        self,
        messages: List[Dict[str, Any]],
        model_context_size: int,
        llm_client,
        model: str,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Automatically compact if needed.
        
        Args:
            messages: Current message history
            model_context_size: Model context window size
            llm_client: LLM client
            model: Model name
        
        Returns:
            Tuple of (messages, compaction_result or None)
        """
        if not self.should_compact(messages, model_context_size):
            return messages, None
        
        result = await self.compact(messages, llm_client, model)
        return result["new_messages"], result
