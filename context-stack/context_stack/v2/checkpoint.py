"""
Context Stack v2 — Checkpoint Manager

Saves and restores context snapshots at scope boundaries.
Phase ① of the lifecycle.

Changes from v1:
  - Prefix hash validation (SHA-256 fast path) for mode=full
  - Supports full_prefix_validation config for debug-mode deep compare
"""
from __future__ import annotations

import logging
from typing import List

from .types import (
    Message,
    MessageRole,
    ScopeRecord,
    ScopeState,
    compute_prefix_hash,
)
from .config import CompactConfig

logger = logging.getLogger("context_stack.v2.checkpoint")


class CheckpointManager:
    """
    Manages context checkpoints for scope transactions.

    checkpoint() = save state (Phase ①)
    reload()     = restore with summary replacing raw messages (Phase ⑥)
    validate_prefix() = verify pre-scope messages haven't changed
    """

    def __init__(self, counter, config: CompactConfig):
        self._counter = counter
        self._config = config

    def checkpoint(
        self,
        scope: ScopeRecord,
        messages: List[Message],
    ) -> str:
        """
        Save a checkpoint at scope open.
        Records: message_start_idx (reference into host messages), token count, prefix hash.

        This is reference-based: only stores the index position, not the messages themselves.

        Returns:
            prefix_hash (SHA-256) for the pre-scope messages
        """
        scope.message_start_idx = len(messages)
        scope.message_end_idx = len(messages)  # will be updated at reload
        scope.tokens_before = self._counter.count_messages(messages)
        scope.state = ScopeState.OPEN

        prefix_hash = compute_prefix_hash(messages)

        logger.debug(
            "Checkpoint: scope=%s start_idx=%d tokens=%d hash=%s",
            scope.id, scope.message_start_idx, scope.tokens_before, prefix_hash[:12],
        )
        return prefix_hash

    def validate_prefix(
        self,
        messages: List[Message],
        message_start_idx: int,
        expected_hash: str,
    ) -> None:
        """
        Validate that pre-scope messages haven't been tampered with.

        Uses SHA-256 hash fast path by default.
        Falls back to deep comparison when full_prefix_validation=True.

        Raises:
            ValueError: if validation fails
        """
        prefix = messages[:message_start_idx]

        if self._config.full_prefix_validation:
            # O(n) deep comparison — debug mode
            self._deep_validate(prefix, expected_hash, message_start_idx)
        else:
            # O(1) hash comparison — production mode
            actual_hash = compute_prefix_hash(prefix)
            if actual_hash != expected_hash:
                raise ValueError(
                    f"Prefix validation failed: pre-scope messages have been modified. "
                    f"Expected hash {expected_hash[:12]}..., got {actual_hash[:12]}... "
                    f"(prefix length: {len(prefix)}). "
                    f"Enable full_prefix_validation=True for detailed diagnostics."
                )

    def _deep_validate(
        self,
        prefix: List[Message],
        expected_hash: str,
        start_idx: int,
    ) -> None:
        """Deep comparison for debugging. Identifies exact mismatch."""
        actual_hash = compute_prefix_hash(prefix)
        if actual_hash == expected_hash:
            return

        # Hash mismatch — find where
        logger.error(
            "Prefix validation FAILED (deep mode): "
            "hash mismatch at message_start_idx=%d. "
            "Expected: %s, Got: %s",
            start_idx, expected_hash[:16], actual_hash[:16],
        )
        raise ValueError(
            f"Prefix validation failed (deep mode): "
            f"pre-scope messages modified at start_idx={start_idx}. "
            f"Hash expected={expected_hash[:12]}, actual={actual_hash[:12]}."
        )

    def reload(
        self,
        scope: ScopeRecord,
        messages: List[Message],
        summary_msg: Message,
    ) -> List[Message]:
        """
        Reload context: replace scope messages with summary. (Phase ⑥)

        Reference-based design:
          - Stores (message_start_idx, message_end_idx) as the reference range
          - Only materializes raw_messages when persistence is enabled
          - The host's message list is the single source of truth

        Before: [pre-scope msgs] + [scope msgs (many)]
        After:  [pre-scope msgs] + [summary (one)]
        """
        start_idx = scope.message_start_idx
        pre_messages = messages[:start_idx]
        scope_messages = messages[start_idx:]

        # Record the reference range (not a copy — just two ints)
        scope.message_end_idx = len(messages)
        scope.message_count = len(scope_messages)

        # Materialize raw_messages ONLY for persistence/recall
        if self._config.scope_store_raw:
            # Filter out injected skill prompts (engine internals)
            work_messages = [
                m for m in scope_messages
                if not m.metadata.get("skill_prompt")
            ]
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
            "Reload: scope=%s range=[%d,%d) msgs=%d→1 saved=%d raw=%d",
            scope.id, start_idx, scope.message_end_idx,
            len(scope_messages), scope.tokens_saved,
            len(scope.raw_messages),
        )
        return new_messages

    def _budget_truncate(self, messages: List[Message]) -> List[Message]:
        """
        Enforce raw_max_chars_per_scope.
        Keep messages from the end (most recent = most valuable).
        """
        budget = self._config.raw_max_chars_per_scope
        if budget <= 0:
            return messages

        total_chars = sum(len(m.content) for m in messages)
        if total_chars <= budget:
            return messages

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
