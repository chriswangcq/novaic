"""
Context Stack v2 — Core Types

All data structures used across the v2 engine.
Changes from v1:
  - Added ScopePhase (scope state machine)
  - Added StackFrame (skill stack bookkeeping)
  - Added TurnContext / TurnPayload (passive pull/push)
  - CompactConfig moved to config.py
  - StackStatus reflects skill stack
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


# ─────────────────────────────────────────────
# Message
# ─────────────────────────────────────────────

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: MessageRole
    content: str
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_call_id: Optional[str] = None
    token_count: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────
# Scope Phase (state machine for _ScopeSession)
# ─────────────────────────────────────────────

class ScopePhase(Enum):
    """State machine for a single scope session."""
    INIT = "init"                # Created, not yet started
    PRE = "pre"                  # ① CHECKPOINT + ② PRE-HOOKS done
    EXECUTING = "executing"      # ③ Host is running LLM loop
    POST = "post"                # ④ POST-HOOKS
    SUMMARIZE = "summarize"      # ⑤ SUMMARIZE
    RELOAD = "reload"            # ⑥ RELOAD
    CLOSED = "closed"            # Finalized successfully
    ABORTED = "aborted"          # Aborted due to error

    @property
    def is_terminal(self) -> bool:
        return self in (ScopePhase.CLOSED, ScopePhase.ABORTED)

    def can_transition_to(self, target: "ScopePhase") -> bool:
        """Check if transition from self → target is valid."""
        return target in _PHASE_TRANSITIONS.get(self, set())


# Legal phase transitions
_PHASE_TRANSITIONS: Dict[ScopePhase, set] = {
    ScopePhase.INIT: {ScopePhase.PRE, ScopePhase.ABORTED},
    ScopePhase.PRE: {ScopePhase.EXECUTING, ScopePhase.ABORTED},
    ScopePhase.EXECUTING: {ScopePhase.POST, ScopePhase.ABORTED},
    ScopePhase.POST: {ScopePhase.SUMMARIZE, ScopePhase.ABORTED},
    ScopePhase.SUMMARIZE: {ScopePhase.RELOAD, ScopePhase.ABORTED},
    ScopePhase.RELOAD: {ScopePhase.CLOSED, ScopePhase.ABORTED},
    ScopePhase.CLOSED: set(),
    ScopePhase.ABORTED: set(),
}


# ─────────────────────────────────────────────
# Scope Record
# ─────────────────────────────────────────────

class ScopeState(Enum):
    OPEN = "open"
    COMPACTED = "compacted"
    RECALLED = "recalled"
    FUSED = "fused"           # merged into a higher-level scope


@dataclass
class ScopeRecord:
    """A bounded unit of agent work, with full metadata."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    skill_name: str = ""
    state: ScopeState = ScopeState.OPEN

    # Timing
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None

    # Structured metadata (post-execution)
    summary: str = ""
    decisions: List[str] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    tools_used: Dict[str, int] = field(default_factory=dict)

    # Message bookkeeping
    message_start_idx: int = 0
    message_end_idx: int = 0       # exclusive end index → [start, end) range ref
    message_count: int = 0
    tokens_before: int = 0
    tokens_after: int = 0
    tokens_saved: int = 0

    # Raw messages — lazily populated for recall/persistence only.
    # The authoritative reference is (message_start_idx, message_end_idx)
    # pointing into the host's message list. raw_messages is a materialized
    # snapshot taken at compaction time.
    raw_messages: List[Message] = field(default_factory=list)

    # Gem Fusion hierarchy (消消乐 / 5-ary carry)
    level: int = 0                                     # L0=raw, L1=5×L0, L2=5×L1...
    parent_id: Optional[str] = None                    # fused-into scope ID
    children_ids: List[str] = field(default_factory=list)  # source scope IDs

    @property
    def duration_seconds(self) -> float:
        if self.ended_at:
            return self.ended_at - self.started_at
        return time.time() - self.started_at


# ─────────────────────────────────────────────
# StackFrame (skill stack bookkeeping)
# ─────────────────────────────────────────────

@dataclass
class StackFrame:
    """
    One frame in the skill stack.
    Each active skill_begin creates one frame.
    """
    scope_id: str
    skill_name: str
    skill_type: str                    # "normal", "meta", "recall"
    auto_meta: bool = False            # True if auto-opened by engine
    message_start_idx: int = 0
    prefix_hash: str = ""              # SHA-256 of messages[:message_start_idx]
    depth: int = 0                     # 0 = bottom of stack
    started_at: float = field(default_factory=time.time)

    # Nested fold stash (§4.6.8)
    stash_segment: Optional[List[Message]] = None
    stash_ref: Optional[str] = None    # External storage reference
    stash_hash: Optional[str] = None   # SHA-256 of stashed segment
    folded_until_child: bool = False


# ─────────────────────────────────────────────
# TurnContext / TurnPayload (passive pull/push)
# ─────────────────────────────────────────────

@dataclass
class TurnContext:
    """Snapshot returned by pull_turn_context."""
    messages: List[Message]
    skill_stack: List[StackFrame]
    scope_id: str = ""
    message_start_idx: int = 0
    phase: ScopePhase = ScopePhase.INIT
    extra_tools: Optional[List[Dict[str, Any]]] = None
    skill_prompt: Optional[str] = None


@dataclass
class TurnPayload:
    """Submitted by host via push_turn."""
    messages: List[Message]
    mode: Literal["full", "replace_from_checkpoint"] = "full"
    done: bool = False
    error: Optional[str] = None
    idempotency_key: Optional[str] = None


# ─────────────────────────────────────────────
# Compact
# ─────────────────────────────────────────────

class CompactAction(Enum):
    SKIP = "skip"
    MICRO = "micro"
    AUTO = "auto"
    SCOPE = "scope"
    EMERGENCY = "emergency"


@dataclass
class CompactResult:
    action: CompactAction
    messages: List[Message]
    tokens_before: int = 0
    tokens_after: int = 0
    tokens_saved: int = 0
    scope_id: Optional[str] = None
    summary: str = ""

    @property
    def compression_ratio(self) -> float:
        if self.tokens_before == 0:
            return 0.0
        return 1.0 - (self.tokens_after / self.tokens_before)


# ─────────────────────────────────────────────
# Stack Status
# ─────────────────────────────────────────────

@dataclass
class StackStatus:
    used_tokens: int = 0
    budget_tokens: int = 200_000
    usage_ratio: float = 0.0
    skill_stack: List[StackFrame] = field(default_factory=list)
    active_scope: Optional[str] = None
    total_scopes: int = 0
    compacted_scopes: int = 0
    recall_available: List[str] = field(default_factory=list)
    total_tokens_saved: int = 0
    total_compactions: int = 0


# ─────────────────────────────────────────────
# Lifecycle Result
# ─────────────────────────────────────────────

@dataclass
class LifecycleResult:
    """Result of a scope finalization (skill_end or push_turn(done=True))."""
    messages: List[Message]
    scope: ScopeRecord
    compact: CompactResult
    skill_name: str = ""
    success: bool = True
    error: Optional[str] = None


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def compute_prefix_hash(messages: List[Message]) -> str:
    """
    Compute SHA-256 hash of a message prefix for fast validation.
    Used by StackFrame.prefix_hash to avoid O(n) deep comparison.
    """
    hasher = hashlib.sha256()
    for msg in messages:
        hasher.update(msg.role.value.encode())
        hasher.update(msg.content.encode())
        if msg.tool_name:
            hasher.update(msg.tool_name.encode())
        if msg.tool_call_id:
            hasher.update(msg.tool_call_id.encode())
    return hasher.hexdigest()
