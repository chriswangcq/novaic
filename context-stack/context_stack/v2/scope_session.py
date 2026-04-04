"""
Context Stack v2 — Scope Session (Internal)

NOT a public API. This is the per-scope state machine that tracks
a single scope's progression through phases:

  INIT → PRE → EXECUTING → POST → SUMMARIZE → RELOAD → CLOSED

The engine creates a ScopeSession when a scope opens (skill_begin or auto_meta).
Host interacts indirectly via engine.push_turn / skill_end tool.
"""
from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from .types import (
    CompactAction,
    CompactResult,
    LifecycleResult,
    Message,
    MessageRole,
    ScopePhase,
    ScopeRecord,
    ScopeState,
    StackFrame,
    TurnContext,
    TurnPayload,
    compute_prefix_hash,
)
from .config import CompactConfig
from .checkpoint import CheckpointManager

logger = logging.getLogger("context_stack.v2.scope_session")


class ScopeSession:
    """
    Internal state machine for a single scope.

    Lifecycle:
      1. __init__     → creates scope record, phase=INIT
      2. begin()      → checkpoint + pre-hooks → phase=EXECUTING
      3. push_turn()  → host pushes turn results → stays EXECUTING
      4. finalize()   → post/summarize/reload → phase=CLOSED
      5. abort()      → error path → phase=ABORTED
    """

    def __init__(
        self,
        frame: StackFrame,
        config: CompactConfig,
        checkpoint_mgr: CheckpointManager,
        counter,
        store,
    ):
        self._frame = frame
        self._config = config
        self._checkpoint = checkpoint_mgr
        self._counter = counter
        self._store = store

        # Create scope record
        self._scope = ScopeRecord(
            id=frame.scope_id,
            name=frame.skill_name,
            skill_name=frame.skill_name,
        )
        self._phase = ScopePhase.INIT
        self._turn_count = 0
        self._idempotency_keys: set = set()

    # ─────────────────────────────────────────
    # Properties
    # ─────────────────────────────────────────

    @property
    def phase(self) -> ScopePhase:
        return self._phase

    @property
    def scope(self) -> ScopeRecord:
        return self._scope

    @property
    def frame(self) -> StackFrame:
        return self._frame

    @property
    def scope_id(self) -> str:
        return self._scope.id

    # ─────────────────────────────────────────
    # Phase transitions
    # ─────────────────────────────────────────

    def _transition(self, target: ScopePhase) -> None:
        """Transition to a new phase with validation."""
        if not self._phase.can_transition_to(target):
            raise RuntimeError(
                f"Invalid phase transition: {self._phase.value} → {target.value} "
                f"(scope={self._scope.id})"
            )
        logger.debug(
            "Phase transition: %s → %s (scope=%s)",
            self._phase.value, target.value, self._scope.id,
        )
        self._phase = target

    # ─────────────────────────────────────────
    # Step 1+2: begin (checkpoint + pre-hooks)
    # ─────────────────────────────────────────

    def begin(
        self,
        messages: List[Message],
        skill_prompt: Optional[str] = None,
    ) -> List[Message]:
        """
        Execute ① CHECKPOINT + ② PRE-HOOKS, transition to EXECUTING.

        Args:
            messages: current conversation
            skill_prompt: optional prompt to inject as system message

        Returns:
            messages with skill_prompt injected (if any)
        """
        # ① CHECKPOINT
        self._transition(ScopePhase.PRE)
        prefix_hash = self._checkpoint.checkpoint(self._scope, messages)
        self._frame.prefix_hash = prefix_hash
        self._frame.message_start_idx = self._scope.message_start_idx

        # ② PRE-HOOKS: inject skill prompt
        if skill_prompt:
            prompt_msg = Message(
                role=MessageRole.SYSTEM,
                content=skill_prompt,
                metadata={
                    "skill_prompt": True,
                    "skill_name": self._frame.skill_name,
                    "scope_id": self._scope.id,
                },
            )
            messages = messages + [prompt_msg]

        logger.info(
            "② PRE: scope=%s skill=%s prompt=%s",
            self._scope.id, self._frame.skill_name, bool(skill_prompt),
        )

        # Transition to EXECUTING
        self._transition(ScopePhase.EXECUTING)
        return messages

    # ─────────────────────────────────────────
    # Step 3: push_turn (host pushes turn)
    # ─────────────────────────────────────────

    def push_turn(
        self,
        payload: TurnPayload,
        messages: List[Message],
    ) -> Optional[LifecycleResult]:
        """
        Accept a turn from the host.

        Args:
            payload: the host's turn submission
            messages: current messages (used for full-mode validation)

        Returns:
            None if scope continues; LifecycleResult if done/error
        """
        if self._phase != ScopePhase.EXECUTING:
            raise RuntimeError(
                f"Cannot push_turn in phase {self._phase.value} "
                f"(scope={self._scope.id})"
            )

        # Idempotency check
        if payload.idempotency_key:
            if payload.idempotency_key in self._idempotency_keys:
                logger.warning(
                    "Duplicate idempotency_key: %s (scope=%s), skipping",
                    payload.idempotency_key, self._scope.id,
                )
                return None
            self._idempotency_keys.add(payload.idempotency_key)

        # Validate prefix (mode=full)
        if payload.mode == "full":
            self._checkpoint.validate_prefix(
                payload.messages,
                self._frame.message_start_idx,
                self._frame.prefix_hash,
            )

        self._turn_count += 1

        # Handle error
        if payload.error:
            return self.abort(payload.error)

        # Handle done (finalize)
        if payload.done:
            return self.finalize(payload.messages)

        return None

    # ─────────────────────────────────────────
    # Step 4-6: finalize (post → summarize → reload)
    # ─────────────────────────────────────────

    def finalize(
        self,
        messages: List[Message],
        report: Optional[str] = None,
    ) -> LifecycleResult:
        """
        Execute ④ POST → ⑤ SUMMARIZE → ⑥ RELOAD.

        Args:
            messages: final conversation messages
            report: optional model-provided summary (from skill_end)
                    If provided, skips Summarizer LLM call (§4.6.2)

        Returns:
            LifecycleResult with compacted messages
        """
        try:
            # ④ POST-HOOKS
            self._transition(ScopePhase.POST)
            scope_messages = messages[self._scope.message_start_idx:]
            self._extract_metadata(scope_messages)
            logger.info("④ POST: scope=%s", self._scope.id)

            # ⑤ SUMMARIZE
            self._transition(ScopePhase.SUMMARIZE)
            if report:
                # Path A: model-provided report (skill_end)
                summary_text = report
            else:
                # Path B/C/D: engine generates summary
                summary_text = self._generate_fallback_summary(scope_messages)

            self._scope.summary = summary_text
            self._scope.ended_at = time.time()
            logger.info("⑤ SUMMARIZE: scope=%s len=%d", self._scope.id, len(summary_text))

            # ⑥ RELOAD
            self._transition(ScopePhase.RELOAD)
            summary_msg = Message(
                role=MessageRole.ASSISTANT,
                content=summary_text,
                metadata={
                    "scope_id": self._scope.id,
                    "scope_name": self._scope.name,
                    "skill_name": self._frame.skill_name,
                    "compacted": True,
                },
            )
            summary_msg.token_count = self._counter.count(summary_text)

            new_messages = self._checkpoint.reload(
                self._scope, messages, summary_msg,
            )
            self._store.save(self._scope)

            logger.info(
                "⑥ RELOAD: scope=%s tokens_saved=%d",
                self._scope.id, self._scope.tokens_saved,
            )

            self._transition(ScopePhase.CLOSED)

            compact = CompactResult(
                action=CompactAction.SCOPE,
                messages=new_messages,
                tokens_before=self._scope.tokens_before,
                tokens_after=self._scope.tokens_after,
                tokens_saved=self._scope.tokens_saved,
                scope_id=self._scope.id,
                summary=summary_text,
            )

            return LifecycleResult(
                messages=new_messages,
                scope=self._scope,
                compact=compact,
                skill_name=self._frame.skill_name,
                success=True,
            )

        except Exception as e:
            logger.error(
                "Finalize failed for scope '%s': %s",
                self._scope.id, e,
            )
            return self.abort(str(e))

    # ─────────────────────────────────────────
    # Abort (error path)
    # ─────────────────────────────────────────

    def abort(self, error: str) -> LifecycleResult:
        """Abort the scope due to error."""
        self._scope.errors.append(error)
        self._scope.ended_at = time.time()
        self._phase = ScopePhase.ABORTED  # Direct set, skip validation

        logger.warning(
            "Scope aborted: scope=%s error=%s",
            self._scope.id, error[:100],
        )

        return LifecycleResult(
            messages=[],  # Caller should use the original messages
            scope=self._scope,
            compact=CompactResult(action=CompactAction.SKIP, messages=[]),
            skill_name=self._frame.skill_name,
            success=False,
            error=error,
        )

    # ─────────────────────────────────────────
    # Metadata extraction (rule-based, zero LLM)
    # ─────────────────────────────────────────

    def _extract_metadata(self, scope_messages: List[Message]) -> None:
        """④ POST sub-step: extract files, tools, errors from messages."""
        import re

        files_set = set()
        errors = []
        tools: Dict[str, int] = {}

        for msg in scope_messages:
            if msg.tool_name:
                tools[msg.tool_name] = tools.get(msg.tool_name, 0) + 1

            content = msg.content or ""

            # File paths
            file_patterns = re.findall(
                r'(?:creat|modif|updat|wrote|edit|delet)\w*\s+'
                r'(?:file\s+)?[`"\']?([^\s`"\']+\.\w{1,10})[`"\']?',
                content, re.IGNORECASE,
            )
            files_set.update(file_patterns)

            # Errors from tool outputs
            if msg.role == MessageRole.TOOL and any(
                kw in content.lower()
                for kw in ("error", "failed", "exception", "traceback")
            ):
                first_line = content.strip().split("\n")[0][:200]
                errors.append(first_line)

        self._scope.files_changed = sorted(files_set)
        self._scope.errors.extend(errors[:10])
        self._scope.tools_used = tools

    def _generate_fallback_summary(self, scope_messages: List[Message]) -> str:
        """Generate a stub summary when no LLM or model report is available."""
        scope = self._scope
        parts = [
            f"## ✅ Scope Complete: {scope.name}",
            f"**Duration**: {scope.duration_seconds:.1f}s | "
            f"**Messages**: {len(scope_messages)} | "
            f"**Tools**: {sum(scope.tools_used.values())} calls",
        ]

        if scope.tools_used:
            tool_str = ", ".join(
                f"{k}×{v}" for k, v in
                sorted(scope.tools_used.items(), key=lambda x: -x[1])[:8]
            )
            parts.append(f"**Tools used**: {tool_str}")

        if scope.files_changed:
            parts.append(
                "**Files**: " + ", ".join(scope.files_changed[:15])
            )

        if scope.errors:
            parts.append(
                "### Errors\n" +
                "\n".join(f"- {e}" for e in scope.errors[:5])
            )

        # Last assistant message as output
        assistant_msgs = [
            m for m in scope_messages
            if m.role == MessageRole.ASSISTANT
        ]
        if assistant_msgs:
            parts.append(
                f"\n### Final Output\n{assistant_msgs[-1].content[:500]}"
            )

        return "\n".join(parts)
