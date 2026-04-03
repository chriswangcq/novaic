"""
Context Stack — Core Types

All data structures used across the engine.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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
    token_count: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────
# Scope
# ─────────────────────────────────────────────

class ScopeState(Enum):
    OPEN = "open"
    COMPACTED = "compacted"
    RECALLED = "recalled"


@dataclass
class ScopeRecord:
    """A bounded unit of agent work, with full metadata."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    skill_name: str = ""           # which skill drove this scope
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
    message_count: int = 0
    tokens_before: int = 0
    tokens_after: int = 0
    tokens_saved: int = 0

    # Raw messages (stored for recall)
    raw_messages: List[Message] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        if self.ended_at:
            return self.ended_at - self.started_at
        return time.time() - self.started_at


# ─────────────────────────────────────────────
# Compact
# ─────────────────────────────────────────────

@dataclass
class CompactConfig:
    context_window: int = 200_000
    compact_threshold: float = 0.70
    emergency_threshold: float = 0.95
    # Micro
    micro_max_tool_output_chars: int = 500
    micro_preserve_recent: int = 3
    # Auto
    auto_summary_max_tokens: int = 20_000
    auto_circuit_breaker_max_fails: int = 3
    # Scope
    scope_store_raw: bool = True
    raw_max_chars_per_scope: int = 50_000  # max total chars stored per scope


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
    active_scope: Optional[str] = None
    total_scopes: int = 0
    compacted_scopes: int = 0
    recall_available: List[str] = field(default_factory=list)
    total_tokens_saved: int = 0
    total_compactions: int = 0


# ─────────────────────────────────────────────
# Lifecycle Result (returned by engine.run)
# ─────────────────────────────────────────────

@dataclass
class LifecycleResult:
    """Result of a complete skill execution lifecycle."""
    messages: List[Message]          # messages after reload
    scope: ScopeRecord               # the scope that was created
    compact: CompactResult           # compact details
    skill_name: str = ""
    success: bool = True
    error: Optional[str] = None
