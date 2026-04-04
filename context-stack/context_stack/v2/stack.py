"""
Context Stack v2 — SkillStack

Manages the skill stack: push/pop/peek with depth enforcement.
Each frame represents an active scope opened by skill_begin.

The stack is the single source of truth for:
  - What skills are currently active (and their nesting order)
  - Where each scope's messages start in the conversation
  - Prefix hashes for fast validation

Invariants (§2.2):
  1. Stack grows from bottom (outer) to top (inner)
  2. skill_end pops only the top frame (LIFO)
  3. message_start_idx is strictly non-decreasing up the stack
  4. max_skill_depth is enforced on push
"""
from __future__ import annotations

import logging
from typing import List, Optional

from .types import StackFrame, Message, compute_prefix_hash
from .config import CompactConfig

logger = logging.getLogger("context_stack.v2.stack")


class SkillStack:
    """
    The skill stack.

    Push = skill_begin (open a new scope)
    Pop  = skill_end (close the topmost scope)
    Peek = inspect the topmost frame without removing it
    """

    def __init__(self, config: CompactConfig):
        self._frames: List[StackFrame] = []
        self._config = config

    # ─────────────────────────────────────────
    # Core operations
    # ─────────────────────────────────────────

    def push(
        self,
        scope_id: str,
        skill_name: str,
        skill_type: str,
        messages: List[Message],
        auto_meta: bool = False,
    ) -> StackFrame:
        """
        Push a new frame onto the stack.

        Args:
            scope_id:   unique ID for this scope
            skill_name: name of the skill
            skill_type: "normal", "meta", "recall"
            messages:   current conversation (used to compute prefix hash and start idx)
            auto_meta:  True if this is an auto-opened MetaSkill

        Returns:
            The new StackFrame

        Raises:
            RuntimeError: if max depth would be exceeded
        """
        new_depth = len(self._frames)
        if new_depth >= self._config.max_skill_depth:
            raise RuntimeError(
                f"Skill stack depth limit reached ({self._config.max_skill_depth}). "
                f"Cannot push '{skill_name}'. Close an active skill first."
            )

        message_start_idx = len(messages)
        prefix_hash = compute_prefix_hash(messages[:message_start_idx])

        frame = StackFrame(
            scope_id=scope_id,
            skill_name=skill_name,
            skill_type=skill_type,
            auto_meta=auto_meta,
            message_start_idx=message_start_idx,
            prefix_hash=prefix_hash,
            depth=new_depth,
        )

        self._frames.append(frame)
        logger.info(
            "Stack push: skill=%s scope=%s depth=%d",
            skill_name, scope_id, new_depth,
        )
        return frame

    def pop(self) -> StackFrame:
        """
        Pop the topmost frame.

        Returns:
            The popped StackFrame

        Raises:
            RuntimeError: if stack is empty
        """
        if not self._frames:
            raise RuntimeError("Cannot pop from empty skill stack.")

        frame = self._frames.pop()
        logger.info(
            "Stack pop: skill=%s scope=%s depth_after=%d",
            frame.skill_name, frame.scope_id, len(self._frames),
        )
        return frame

    def peek(self) -> Optional[StackFrame]:
        """Return the topmost frame without removing it, or None if empty."""
        return self._frames[-1] if self._frames else None

    # ─────────────────────────────────────────
    # Queries
    # ─────────────────────────────────────────

    @property
    def depth(self) -> int:
        """Current stack depth (0 = empty)."""
        return len(self._frames)

    @property
    def is_empty(self) -> bool:
        return len(self._frames) == 0

    @property
    def frames(self) -> List[StackFrame]:
        """Read-only snapshot of the stack (bottom to top)."""
        return list(self._frames)

    def has_only_auto_meta(self) -> bool:
        """True if the stack contains exactly one auto-meta frame."""
        return (
            len(self._frames) == 1
            and self._frames[0].auto_meta
        )

    def top_is_auto_meta(self) -> bool:
        """True if the topmost frame is an auto-meta frame."""
        return (
            bool(self._frames)
            and self._frames[-1].auto_meta
        )

    # ─────────────────────────────────────────
    # Snapshot for context message injection
    # ─────────────────────────────────────────

    def snapshot_text(self) -> str:
        """
        Generate the skill stack snapshot text for context injection (§4.6.3).
        Top→bottom (inner→outer) ordering.
        """
        if not self._frames:
            return "## Skill stack\nempty"

        lines = ["## Skill stack", "Top→bottom (inner→outer):"]
        for i, frame in enumerate(reversed(self._frames), 1):
            auto_tag = " (auto_meta)" if frame.auto_meta else ""
            lines.append(
                f"{i}. {frame.skill_name} scope={frame.scope_id}{auto_tag}"
            )
        return "\n".join(lines)

    # ─────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────

    def validate_top_scope(self, expected_scope_id: str) -> None:
        """
        Ensure the top of the stack matches an expected scope ID.
        Used by skill_end to prevent closing the wrong scope.

        Raises:
            RuntimeError: if mismatch or stack empty
        """
        if not self._frames:
            raise RuntimeError(
                f"Cannot close scope '{expected_scope_id}': stack is empty."
            )
        top = self._frames[-1]
        if top.scope_id != expected_scope_id:
            raise RuntimeError(
                f"Cannot close scope '{expected_scope_id}': "
                f"top of stack is '{top.scope_id}' ({top.skill_name}). "
                f"Close inner scopes first (LIFO)."
            )

    def clear(self) -> None:
        """Clear all frames. Used during engine close/reset."""
        self._frames.clear()
