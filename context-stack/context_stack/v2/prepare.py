"""
Context Stack v2 — prepare_messages_for_llm

The single entry point for pre-LLM message processing.
Internally split into two INDEPENDENT phases (§4.4.1):

  Phase A: _ensure_stack_ready  → only handles stack state (auto_meta)
  Phase B: _budget_compact      → only does pure token budget compression

Each phase has independent spans, error paths, and can be tested in isolation.
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, List, Optional

from .types import Message, MessageRole, CompactAction, CompactResult
from .config import CompactConfig

if TYPE_CHECKING:
    from .engine import ContextEngine

logger = logging.getLogger("context_stack.v2.prepare")


def prepare_messages_for_llm(
    engine: "ContextEngine",
    messages: List[Message],
) -> List[Message]:
    """
    The unified entry point called before every LLM invocation.

    Phase A: ensure stack is ready (auto_meta if empty)
    Phase B: budget compaction (micro → auto → emergency)

    Returns:
        Processed message list ready for LLM
    """
    # ─── Phase A: Stack Ready ───
    # span: context_stack.prepare.stack_ready
    try:
        messages = _ensure_stack_ready(engine, messages)
    except Exception as e:
        logger.error(
            "Phase A (_ensure_stack_ready) failed: %s. "
            "Continuing with original messages for Phase B.",
            e,
        )
        # Phase A failure should NOT prevent Phase B from running,
        # but we log it clearly so it's not masked as "no compaction needed"

    # ─── Phase B: Budget Compact ───
    # span: context_stack.prepare.budget_compact
    try:
        messages = _budget_compact(engine, messages)
    except Exception as e:
        logger.error(
            "Phase B (_budget_compact) failed: %s. "
            "Returning messages without compaction.",
            e,
        )

    return messages


# ─────────────────────────────────────────────
# Phase A: Stack State Management
# ─────────────────────────────────────────────

def _ensure_stack_ready(
    engine: "ContextEngine",
    messages: List[Message],
) -> List[Message]:
    """
    Phase A: Ensure the skill stack is in a valid state.

    If config.auto_meta_when_stack_empty and stack is empty,
    automatically open a MetaSkill scope so every message belongs
    to some scope.

    Returns:
        messages (possibly with auto_meta system message appended)
    """
    config = engine._config
    stack = engine._stack

    if not config.auto_meta_when_stack_empty:
        return messages

    if not stack.is_empty:
        return messages

    # Stack is empty → auto-open MetaSkill
    logger.info("Phase A: stack empty, auto-opening MetaSkill")
    messages = engine._begin_scope(
        skill_name="meta",
        skill_type="meta",
        messages=messages,
        auto_meta=True,
    )
    return messages


# ─────────────────────────────────────────────
# Phase B: Token Budget Compaction
# ─────────────────────────────────────────────

def _budget_compact(
    engine: "ContextEngine",
    messages: List[Message],
) -> List[Message]:
    """
    Phase B: Apply token budget compaction.

    Order:
      1. Count tokens, compute usage_ratio
      2. If >= emergency_threshold → emergency compact
      3. Elif >= compact_threshold → mild compact (micro + auto)
      4. Else → micro-only (if applicable)

    Respects scope boundaries: when stack is non-empty, only
    compacts in ways that don't break scope checkpoints.
    """
    config = engine._config
    counter = engine._counter

    total_tokens = counter.count_messages(messages)
    budget = config.context_window
    usage_ratio = total_tokens / budget if budget > 0 else 0.0

    # Debounce: skip if we already compacted recently on same message count
    msg_count = len(messages)
    if hasattr(engine, '_last_compact_msg_count'):
        if engine._last_compact_msg_count == msg_count:
            return messages

    if usage_ratio >= config.emergency_threshold:
        # ─── Emergency path ───
        logger.warning(
            "Phase B: EMERGENCY compact (usage=%.1f%%, threshold=%.0f%%)",
            usage_ratio * 100, config.emergency_threshold * 100,
        )
        result = _emergency_compact(engine, messages)
        engine._last_compact_msg_count = len(result)
        return result

    if usage_ratio >= config.compact_threshold:
        # ─── Mild path (micro + auto) ───
        logger.info(
            "Phase B: mild compact (usage=%.1f%%, threshold=%.0f%%)",
            usage_ratio * 100, config.compact_threshold * 100,
        )
        result = _mild_compact(engine, messages)
        engine._last_compact_msg_count = len(result)
        return result

    # ─── Below threshold: micro-only ───
    result = _micro_compact(messages, config)
    return result


# ─────────────────────────────────────────────
# Internal compact implementations
# ─────────────────────────────────────────────

def _micro_compact(messages: List[Message], config: CompactConfig) -> List[Message]:
    """
    Zero-cost tool output truncation. No LLM needed.
    Reuses v1 logic.
    """
    tool_indices = [
        i for i, m in enumerate(messages)
        if m.role == MessageRole.TOOL
    ]

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
                content=(
                    msg.content[:max_chars] +
                    f"\n\n... (truncated, was {len(msg.content)} chars)"
                ),
                tool_name=msg.tool_name,
                tool_input=msg.tool_input,
                tool_call_id=msg.tool_call_id,
                timestamp=msg.timestamp,
                metadata={**msg.metadata, "micro_compacted": True},
            )
            result.append(new_msg)
            count += 1
        else:
            result.append(msg)

    if count:
        logger.debug("Micro compact: truncated %d tool outputs", count)
    return result


def _mild_compact(engine: "ContextEngine", messages: List[Message]) -> List[Message]:
    """
    Micro + auto compaction. Uses Summarizer for the auto phase.
    Respects scope boundaries when stack is non-empty.
    """
    config = engine._config
    counter = engine._counter
    summarizer = engine._summarizer

    # Step 1: Micro compact
    messages = _micro_compact(messages, config)

    # Step 2: Auto compact (only if stack has no active non-meta scope)
    stack = engine._stack
    if not stack.is_empty and not stack.has_only_auto_meta():
        # Non-meta scopes active — don't do LLM-based compaction
        # as it would break scope boundaries
        logger.debug("Mild compact: skipping auto (active non-meta scope)")
        return messages

    # Auto compact: summarize old messages
    system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
    non_system = [m for m in messages if m.role != MessageRole.SYSTEM]

    if len(non_system) < 4:
        return messages

    keep_count = max(2, len(non_system) // 4)
    to_summarize = non_system[:-keep_count]
    to_keep = non_system[-keep_count:]

    try:
        summary_text = summarizer.summarize(
            to_summarize,
            max_tokens=config.auto_summary_max_tokens,
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
            metadata={
                "auto_compacted": True,
                "summarized_messages": len(to_summarize),
            },
        )
        summary_msg.token_count = counter.count(summary_msg.content)
        return system_msgs + [summary_msg] + to_keep

    except Exception as e:
        logger.warning("Auto compact failed: %s", e)
        return messages


def _emergency_compact(
    engine: "ContextEngine",
    messages: List[Message],
) -> List[Message]:
    """
    Emergency compaction: drop most messages, keep only recent.
    No LLM — pure truncation for prompt_too_long recovery.
    """
    system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
    non_system = [m for m in messages if m.role != MessageRole.SYSTEM]

    keep_count = max(2, len(non_system) // 10)
    kept = non_system[-keep_count:]
    dropped = len(non_system) - keep_count

    emergency_msg = Message(
        role=MessageRole.ASSISTANT,
        content=(
            f"## ⚠️ Emergency Compaction\n\n"
            f"{dropped} messages dropped.\n"
            f"Remaining: {len(kept)} recent + {len(system_msgs)} system."
        ),
        metadata={"emergency_compacted": True, "messages_dropped": dropped},
    )
    return system_msgs + [emergency_msg] + kept
