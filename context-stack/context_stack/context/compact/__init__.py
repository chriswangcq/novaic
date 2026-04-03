"""
Context Stack — MicroCompact

Zero-cost tool output truncation. No LLM needed.
"""
from __future__ import annotations

import logging
from typing import List

from ..types import CompactConfig, Message, MessageRole

logger = logging.getLogger("context_stack.compact.micro")


def micro_compact(messages: List[Message], config: CompactConfig) -> List[Message]:
    """Truncate old tool outputs, preserving the N most recent."""
    tool_indices = [i for i, m in enumerate(messages) if m.role == MessageRole.TOOL]

    if len(tool_indices) <= config.micro_preserve_recent:
        return messages

    truncate_set = set(tool_indices[:-config.micro_preserve_recent])
    max_chars = config.micro_max_tool_output_chars
    result = []
    count = 0

    for i, msg in enumerate(messages):
        if i in truncate_set and len(msg.content) > max_chars:
            new_msg = Message(
                role=msg.role,
                content=msg.content[:max_chars] + f"\n\n... (truncated, was {len(msg.content)} chars)",
                tool_name=msg.tool_name,
                tool_input=msg.tool_input,
                timestamp=msg.timestamp,
                metadata={**msg.metadata, "micro_compacted": True},
            )
            result.append(new_msg)
            count += 1
        else:
            result.append(msg)

    if count:
        logger.debug("MicroCompact: truncated %d tool outputs", count)
    return result
