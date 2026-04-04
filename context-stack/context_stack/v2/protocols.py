"""
Context Stack v2 — Protocols

Protocol-driven interfaces for zero-coupling integration.
Host implements these to plug in.

Changes from v1:
  - REMOVED AgentExecutor — engine is passive, host drives LLM loop
  - SkillEndReportValidator added (optional hook)
  - MemoryBackend.fetch_stash / save_stash for nested fold
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from .types import Message, ScopeRecord


@runtime_checkable
class Summarizer(Protocol):
    """LLM-based summarization. Host provides its own LLM client."""
    def summarize(
        self,
        messages: List[Message],
        max_tokens: int = 2000,
        instructions: str = "",
    ) -> str: ...


@runtime_checkable
class TokenCounter(Protocol):
    """Token counting."""
    def count(self, text: str) -> int: ...
    def count_messages(self, messages: List[Message]) -> int: ...


@runtime_checkable
class MemoryBackend(Protocol):
    """
    Persistent storage for scope records. Enables cross-session Recall.
    Without this, recall is limited to in-memory (current session).
    """
    def save(self, record: ScopeRecord) -> None: ...
    def load(self, scope_id: str) -> Optional[ScopeRecord]: ...
    def search(self, query: str, limit: int = 5) -> List[ScopeRecord]: ...
    def list_all(self, limit: int = 50) -> List[ScopeRecord]: ...


@runtime_checkable
class SkillEndReportValidator(Protocol):
    """
    Optional hook to validate skill_end report quality.
    Returns None if passed; returns rejection reason string if rejected.
    Rejected reports cause the engine to return a TOOL error
    asking the model to resubmit a better report.
    """
    def validate(self, report: str, scope: ScopeRecord) -> Optional[str]: ...
