"""
Context Stack — AutoCompact

LLM-based conversation summarization with circuit breaker + emergency fallback.
"""
from __future__ import annotations

import logging
import time
from typing import List

from ..types import CompactAction, CompactConfig, CompactResult, Message, MessageRole

logger = logging.getLogger("context_stack.compact.auto")


class AutoCompactor:
    def __init__(self, config: CompactConfig, summarizer, counter):
        self._config = config
        self._summarizer = summarizer
        self._counter = counter
        self._consecutive_failures = 0
        self._last_failure_time: float = 0
        self._cooldown = 60.0

    def should_trigger(self, messages: List[Message]) -> bool:
        if self._is_circuit_open():
            return False
        total = self._counter.count_messages(messages)
        threshold = int(self._config.context_window * self._config.compact_threshold)
        return total > threshold

    def compact(self, messages: List[Message]) -> CompactResult:
        tokens_before = self._counter.count_messages(messages)
        try:
            system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
            non_system = [m for m in messages if m.role != MessageRole.SYSTEM]

            if len(non_system) < 4:
                return CompactResult(action=CompactAction.SKIP, messages=messages,
                                     tokens_before=tokens_before, tokens_after=tokens_before)

            keep_count = max(2, len(non_system) // 4)
            to_summarize = non_system[:-keep_count]
            to_keep = non_system[-keep_count:]

            summary_text = self._summarizer.summarize(
                to_summarize, max_tokens=self._config.auto_summary_max_tokens,
                instructions=(
                    "Summarize this conversation segment. Preserve:\n"
                    "1. All decisions and rationale\n"
                    "2. Files created/modified\n"
                    "3. Errors and resolutions\n"
                    "4. Current state and pending tasks"
                ),
            )
            summary_msg = Message(
                role=MessageRole.ASSISTANT,
                content=f"## 📋 Auto-Compact Summary\n\n{summary_text}",
                metadata={"auto_compacted": True, "summarized_messages": len(to_summarize)},
            )
            summary_msg.token_count = self._counter.count(summary_msg.content)

            new_messages = system_msgs + [summary_msg] + to_keep
            tokens_after = self._counter.count_messages(new_messages)
            self._consecutive_failures = 0

            return CompactResult(
                action=CompactAction.AUTO, messages=new_messages,
                tokens_before=tokens_before, tokens_after=tokens_after,
                tokens_saved=tokens_before - tokens_after, summary=summary_text,
            )
        except Exception as e:
            self._consecutive_failures += 1
            self._last_failure_time = time.time()
            logger.error("AutoCompact failed (attempt %d): %s", self._consecutive_failures, e)
            return CompactResult(action=CompactAction.SKIP, messages=messages,
                                 tokens_before=tokens_before, tokens_after=tokens_before)

    def emergency_compact(self, messages: List[Message]) -> CompactResult:
        tokens_before = self._counter.count_messages(messages)
        system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
        non_system = [m for m in messages if m.role != MessageRole.SYSTEM]
        keep_count = max(2, len(non_system) // 10)
        kept = non_system[-keep_count:]
        dropped = len(non_system) - keep_count
        emergency_msg = Message(
            role=MessageRole.ASSISTANT,
            content=f"## ⚠️ Emergency Compaction\n\n{dropped} messages dropped.\nRemaining: {len(kept)} recent + system.",
            metadata={"emergency_compacted": True, "messages_dropped": dropped},
        )
        new_messages = system_msgs + [emergency_msg] + kept
        tokens_after = self._counter.count_messages(new_messages)
        return CompactResult(
            action=CompactAction.EMERGENCY, messages=new_messages,
            tokens_before=tokens_before, tokens_after=tokens_after,
            tokens_saved=tokens_before - tokens_after,
        )

    def _is_circuit_open(self) -> bool:
        if self._consecutive_failures < self._config.auto_circuit_breaker_max_fails:
            return False
        if time.time() - self._last_failure_time > self._cooldown:
            self._consecutive_failures = 0
            return False
        return True
