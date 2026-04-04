"""
Context Stack v2 — ContextEngine

The unified passive facade. No AgentExecutor — host drives the LLM loop.

Public API:
    prepare_messages_for_llm(messages)  → pre-LLM processing
    match(task)                          → skill matching
    status(messages)                     → inspect state
    close()                              → release resources
    __enter__ / __exit__                 → context manager
    router                               → SkillToolRouter for tool dispatch
    hooks                                → HookRegistry for pre/post hooks
    recall                               → RecallSkill for memory exploration

Internal (tool-driven):
    _begin_scope(...)                    → open a new scope (skill_begin)
    _end_scope(...)                      → close the top scope (skill_end)

Optional passive stepping:
    pull_turn_context()                  → snapshot for host
    push_turn(payload)                   → host submits turn
"""
from __future__ import annotations

import logging
import threading
import uuid
from typing import Any, Dict, List, Optional

from .types import (
    CompactAction,
    CompactResult,
    LifecycleResult,
    Message,
    MessageRole,
    ScopePhase,
    StackFrame,
    StackStatus,
    TurnContext,
    TurnPayload,
)
from .config import CompactConfig
from .protocols import Summarizer, TokenCounter, MemoryBackend, SkillEndReportValidator
from .stack import SkillStack
from .checkpoint import CheckpointManager
from .scope_session import ScopeSession
from .defaults import StubSummarizer, CharTokenCounter, InMemoryScopeStore
from .prepare import prepare_messages_for_llm as _prepare

logger = logging.getLogger("context_stack.v2.engine")


class ContextEngine:
    """
    The unified passive Context + Memory + Skill engine.

    Host provides (all optional, defaults available):
        config:     behavior tuning (CompactConfig)
        store:      where to persist scopes (MemoryBackend protocol)
        summarizer: how to call LLM for summarization (Summarizer protocol)
        counter:    how to count tokens (TokenCounter protocol)

    Engine provides:
        prepare_messages_for_llm():  pre-LLM budget management
        match():                      find the right skill for a task
        status():                     context budget + scope history
        close():                      release resources
    """

    def __init__(
        self,
        *,
        config: Optional[CompactConfig] = None,
        store: Optional[Any] = None,           # MemoryBackend protocol
        summarizer: Optional[Any] = None,      # Summarizer protocol
        counter: Optional[Any] = None,         # TokenCounter protocol
        report_validator: Optional[Any] = None, # SkillEndReportValidator protocol
        registry: Optional[Any] = None,        # SkillRegistry (optional)
    ):
        self._config = config or CompactConfig()
        self._store = store or InMemoryScopeStore()
        self._summarizer = summarizer or StubSummarizer()
        self._counter = counter or CharTokenCounter()
        self._report_validator = report_validator
        self._registry = registry

        # Core components
        self._stack = SkillStack(self._config)
        self._checkpoint = CheckpointManager(self._counter, self._config)

        # Recall skill (memory exploration)
        from .recall import RecallSkill
        self._recall = RecallSkill(self._store, self._counter)

        # Hook registry
        from .hooks import HookRegistry
        self._hooks = HookRegistry()

        # Tool router (bridges LLM tool_calls → engine internals)
        from .tool_router import SkillToolRouter
        self._router = SkillToolRouter(self)

        # Active scope sessions (keyed by scope_id)
        self._sessions: Dict[str, ScopeSession] = {}

        # Gem Fusion (宝石合成)
        self._fuser = None
        if self._config.gem_fusion_enabled:
            from .fuser import ScopeFuser
            self._fuser = ScopeFuser(
                store=self._store,
                merge_factor=self._config.gem_fusion_merge_factor,
                max_level=self._config.gem_fusion_max_level,
            )

        # Stats (thread-safe)
        self._stats_lock = threading.Lock()
        self._total_tokens_saved = 0
        self._total_lifecycles = 0

        # Lifecycle state
        self._closed = False

        # Debounce state for prepare
        self._last_compact_msg_count: Optional[int] = None

    # ═════════════════════════════════════════
    # Lifecycle Management
    # ═════════════════════════════════════════

    def close(self) -> None:
        """
        Release all resources held by the engine.
        After close(), any method call raises RuntimeError.
        Idempotent — multiple calls are safe.
        """
        if self._closed:
            return

        self._closed = True

        # Clear stack
        self._stack.clear()
        self._sessions.clear()

        # Close store if it supports it
        if hasattr(self._store, 'close'):
            try:
                self._store.close()
            except Exception as e:
                logger.warning("Store close failed: %s", e)

        logger.info("ContextEngine closed.")

    def __enter__(self) -> "ContextEngine":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _check_closed(self) -> None:
        if self._closed:
            raise RuntimeError(
                "ContextEngine has been closed. "
                "Cannot perform operations on a closed engine."
            )

    # ═════════════════════════════════════════
    # Core API 1: prepare_messages_for_llm
    # ═════════════════════════════════════════

    def prepare_messages_for_llm(
        self,
        messages: List[Message],
    ) -> List[Message]:
        """
        The single entry point called before every LLM invocation.

        Phase A: ensure stack is ready (auto_meta if empty)
        Phase B: budget compaction (micro → auto → emergency)

        Returns:
            Processed message list ready for LLM
        """
        self._check_closed()
        return _prepare(self, messages)

    # ═════════════════════════════════════════
    # Core API 2: match
    # ═════════════════════════════════════════

    def match(
        self,
        task: str,
        agent_id: str = "",
        file_paths: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Match a task to the best skill.
        Returns None if no match (caller should use auto_meta).

        Note: Skill registry is pluggable. This is a pass-through
        to whatever registry the host has set up.
        """
        self._check_closed()
        # TODO: integrate with SkillRegistry when available
        return None

    # ═════════════════════════════════════════
    # Core API 3: status
    # ═════════════════════════════════════════

    def status(self, messages: Optional[List[Message]] = None) -> StackStatus:
        """Get current engine status."""
        self._check_closed()

        used = self._counter.count_messages(messages) if messages else 0
        budget = self._config.context_window

        recallable = (
            self._store.get_recallable_names()
            if hasattr(self._store, 'get_recallable_names')
            else []
        )

        top_frame = self._stack.peek()

        return StackStatus(
            used_tokens=used,
            budget_tokens=budget,
            usage_ratio=used / budget if budget > 0 else 0,
            skill_stack=self._stack.frames,
            active_scope=top_frame.scope_id if top_frame else None,
            total_scopes=(
                self._store.count
                if hasattr(self._store, 'count') else 0
            ),
            compacted_scopes=(
                self._store.compacted_count
                if hasattr(self._store, 'compacted_count') else 0
            ),
            recall_available=recallable,
            total_tokens_saved=self._total_tokens_saved,
            total_compactions=self._total_lifecycles,
        )

    # ═════════════════════════════════════════
    # Internal: Scope Management (tool-driven)
    # ═════════════════════════════════════════

    def _begin_scope(
        self,
        skill_name: str,
        skill_type: str,
        messages: List[Message],
        auto_meta: bool = False,
        skill_prompt: Optional[str] = None,
    ) -> List[Message]:
        """
        Open a new scope. Called by:
          - skill_begin tool (via SkillToolRouter)
          - auto_meta (via prepare Phase A)

        Returns:
            messages with skill prompt and stack snapshot injected
        """
        self._check_closed()

        scope_id = uuid.uuid4().hex[:12]

        # Push onto stack (validates depth limit)
        frame = self._stack.push(
            scope_id=scope_id,
            skill_name=skill_name,
            skill_type=skill_type,
            messages=messages,
            auto_meta=auto_meta,
        )

        # Create scope session
        session = ScopeSession(
            frame=frame,
            config=self._config,
            checkpoint_mgr=self._checkpoint,
            counter=self._counter,
            store=self._store,
        )
        self._sessions[scope_id] = session

        # Execute ① CHECKPOINT + ② PRE-HOOKS
        messages = session.begin(messages, skill_prompt=skill_prompt)

        # Inject stack snapshot as system message (§4.6.3, role=system)
        snapshot_msg = Message(
            role=MessageRole.SYSTEM,
            content=self._stack.snapshot_text(),
            metadata={
                "skill_stack_snapshot": True,
                "scope_id": scope_id,
                "after": "begin",
            },
        )
        messages = messages + [snapshot_msg]

        logger.info(
            "Scope opened: scope=%s skill=%s depth=%d auto_meta=%s",
            scope_id, skill_name, frame.depth, auto_meta,
        )
        return messages

    def _end_scope(
        self,
        scope_id: Optional[str],
        messages: List[Message],
        report: Optional[str] = None,
    ) -> LifecycleResult:
        """
        Close the topmost scope. Called by skill_end tool.

        If scope_id is provided, validates it matches the top of stack.
        If report is provided, uses it as the summary (skips Summarizer LLM).

        Returns:
            LifecycleResult with compacted messages
        """
        self._check_closed()

        # Validate
        if scope_id:
            self._stack.validate_top_scope(scope_id)

        top = self._stack.peek()
        if not top:
            raise RuntimeError("Cannot end scope: stack is empty.")

        actual_scope_id = top.scope_id
        session = self._sessions.get(actual_scope_id)
        if not session:
            raise RuntimeError(
                f"No active session for scope '{actual_scope_id}'."
            )

        # Optional: validate report quality (§4.6.2)
        if report and self._report_validator:
            rejection = self._report_validator.validate(report, session.scope)
            if rejection:
                logger.warning(
                    "skill_end report rejected: %s (scope=%s)",
                    rejection, actual_scope_id,
                )
                # Return error so model can retry
                return LifecycleResult(
                    messages=messages,
                    scope=session.scope,
                    compact=CompactResult(
                        action=CompactAction.SKIP, messages=messages,
                    ),
                    skill_name=top.skill_name,
                    success=False,
                    error=f"Report rejected: {rejection}. Please resubmit skill_end with a more detailed report.",
                )

        # Finalize the session (④ POST → ⑤ SUMMARIZE → ⑥ RELOAD)
        result = session.finalize(messages, report=report)

        if result.success:
            # Pop the stack
            self._stack.pop()

            # Remove session
            del self._sessions[actual_scope_id]

            # Update stats
            with self._stats_lock:
                self._total_tokens_saved += result.compact.tokens_saved
                self._total_lifecycles += 1

            # Inject stack snapshot after end (§4.6.3 symmetry)
            if result.messages:
                snapshot_msg = Message(
                    role=MessageRole.SYSTEM,
                    content=self._stack.snapshot_text(),
                    metadata={
                        "skill_stack_snapshot": True,
                        "scope_id": actual_scope_id,
                        "after": "end",
                    },
                )
                result.messages = result.messages + [snapshot_msg]

            # Auto gem fusion
            if self._fuser:
                self._fuser.maybe_fuse(result.scope)

        return result

    # ═════════════════════════════════════════
    # Optional: Passive Stepping (pull/push)
    # ═════════════════════════════════════════

    def pull_turn_context(self) -> TurnContext:
        """
        Get a snapshot of the current state for the host.
        The host reads this to understand what's active.
        """
        self._check_closed()

        top = self._stack.peek()
        session = self._sessions.get(top.scope_id) if top else None

        return TurnContext(
            messages=[],  # Host provides messages from its own store
            skill_stack=self._stack.frames,
            scope_id=top.scope_id if top else "",
            message_start_idx=top.message_start_idx if top else 0,
            phase=session.phase if session else ScopePhase.INIT,
        )

    def push_turn(self, payload: TurnPayload) -> Optional[LifecycleResult]:
        """
        Host submits a turn. Delegates to the topmost session.
        Returns LifecycleResult if the scope is finalized.
        """
        self._check_closed()

        top = self._stack.peek()
        if not top:
            logger.debug("push_turn: no active scope, ignoring")
            return None

        session = self._sessions.get(top.scope_id)
        if not session:
            raise RuntimeError(
                f"No active session for scope '{top.scope_id}'."
            )

        result = session.push_turn(payload, payload.messages)

        if result and result.success:
            # Scope was finalized via done=True
            self._stack.pop()
            del self._sessions[top.scope_id]
            with self._stats_lock:
                self._total_tokens_saved += result.compact.tokens_saved
                self._total_lifecycles += 1
            # Auto gem fusion
            if self._fuser:
                self._fuser.maybe_fuse(result.scope)

        return result

    # ═════════════════════════════════════════
    # Checkpoint & Restore (M3)
    # ═════════════════════════════════════════

    def checkpoint_blob(
        self,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a checkpoint blob of the current engine state (§8.1).

        The blob can be serialized (JSON/msgpack) and used to
        restore the engine state in a new process.

        Note: Messages are NOT included in the blob. The host
        provides them on restore.

        Args:
            meta: optional metadata (task_id, correlation_id, etc.)

        Returns:
            Serializable dict
        """
        self._check_closed()
        from .blob import create_checkpoint_blob
        return create_checkpoint_blob(self, meta=meta)

    def restore_from_blob(
        self,
        blob: Dict[str, Any],
        messages: List[Message],
    ) -> None:
        """
        Restore engine state from a checkpoint blob (§8.1).

        Validates blob version and config hash before restoring.
        Only sessions in EXECUTING phase can be resumed.

        Args:
            blob: the checkpoint blob dict
            messages: current conversation messages from host

        Raises:
            BlobVersionError, BlobConfigHashError, BlobCorruptedError
            RuntimeError: if engine already has active scopes
        """
        self._check_closed()
        from .blob import restore_from_blob
        restore_from_blob(self, blob, messages)

    @property
    def config_hash(self) -> str:
        """SHA-256 hash of the current engine config (§8.1)."""
        from .blob import compute_config_hash
        return compute_config_hash(self._config)

    # ═════════════════════════════════════════
    # Accessors
    # ═════════════════════════════════════════

    @property
    def stack(self) -> SkillStack:
        """Read-only access to the skill stack."""
        return self._stack

    @property
    def router(self):
        """SkillToolRouter for dispatching engine tool calls."""
        return self._router

    @property
    def hooks(self):
        """HookRegistry for pre/post lifecycle hooks."""
        return self._hooks

    @property
    def recall(self):
        """RecallSkill for memory exploration."""
        return self._recall

    @property
    def fuser(self):
        """ScopeFuser for gem-synthesis progressive summarization. None if disabled."""
        return self._fuser

    @property
    def is_closed(self) -> bool:
        return self._closed

