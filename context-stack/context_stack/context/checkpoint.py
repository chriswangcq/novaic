"""
Context Stack — Checkpoint Manager

Saves and restores context snapshots at scope boundaries.
Phase ① of the lifecycle.

Fixes applied:
  #1: Filters out skill_prompt messages from raw_messages
  #4: Respects scope_store_raw config flag
  #6: Enforces raw_max_chars_per_scope memory budget
"""
from __future__ import annotations

import logging
from typing import List

from .types import CompactConfig, Message, ScopeRecord, ScopeState

logger = logging.getLogger("context_stack.checkpoint")


class CheckpointManager:
    """
    Manages context checkpoints for scope transactions.
    
    checkpoint() = save state
    reload()     = restore with summary replacing raw messages
    """

    def __init__(self, counter, config: CompactConfig | None = None):
        self._counter = counter
        self._config = config or CompactConfig()

    def checkpoint(
        self,
        scope: ScopeRecord,
        messages: List[Message],
    ) -> None:
        """
        Save a checkpoint at scope open.
        Records: where we are in the message list, current token count.
        """
        scope.message_start_idx = len(messages)
        scope.tokens_before = self._counter.count_messages(messages)
        scope.state = ScopeState.OPEN
        
        logger.debug(
            "Checkpoint: scope=%s messages=%d tokens=%d",
            scope.id, len(messages), scope.tokens_before,
        )

    def reload(
        self,
        scope: ScopeRecord,
        messages: List[Message],
        summary_msg: Message,
    ) -> List[Message]:
        """
        Reload context: replace scope messages with summary.
        
        Before: [pre-scope msgs] + [scope msgs (many)]
        After:  [pre-scope msgs] + [summary (one)]
        
        Fix #1: Filters skill_prompt messages from raw_messages
        Fix #4: Only stores raw if scope_store_raw is True
        Fix #6: Truncates raw_messages to raw_max_chars_per_scope
        """
        start_idx = scope.message_start_idx
        pre_messages = messages[:start_idx]
        scope_messages = messages[start_idx:]
        
        # Store raw messages for recall (with fixes)
        scope.message_count = len(scope_messages)
        if self._config.scope_store_raw:
            # Fix #1: filter out injected skill prompts — they're
            # engine internals, not useful for recall
            work_messages = [
                m for m in scope_messages
                if not m.metadata.get("skill_prompt")
            ]
            # Fix #6: enforce memory budget
            scope.raw_messages = self._budget_truncate(work_messages)
        else:
            scope.raw_messages = []
        
        # Replace with summary
        new_messages = pre_messages + [summary_msg]
        
        scope.tokens_after = self._counter.count_messages(new_messages)
        scope.tokens_saved = (
            scope.tokens_before
            + self._counter.count_messages(scope_messages)
            - scope.tokens_after
        )
        scope.state = ScopeState.COMPACTED
        
        logger.info(
            "Reload: scope=%s messages=%d→1 tokens_saved=%d raw_stored=%d",
            scope.id, len(scope_messages), scope.tokens_saved,
            len(scope.raw_messages),
        )
        
        return new_messages

    def _budget_truncate(self, messages: List[Message]) -> List[Message]:
        """
        Fix #6: Enforce raw_max_chars_per_scope.
        Keep messages from the end (most recent = most valuable)
        until we hit the budget.
        """
        budget = self._config.raw_max_chars_per_scope
        if budget <= 0:
            return messages
        
        total_chars = sum(len(m.content) for m in messages)
        if total_chars <= budget:
            return messages
        
        # Walk backwards, keep most recent messages first
        kept = []
        used = 0
        for msg in reversed(messages):
            msg_chars = len(msg.content)
            if used + msg_chars > budget:
                break
            kept.append(msg)
            used += msg_chars
        
        kept.reverse()
        
        logger.debug(
            "Budget truncate: %d→%d messages, %d→%d chars",
            len(messages), len(kept), total_chars, used,
        )
        return kept
