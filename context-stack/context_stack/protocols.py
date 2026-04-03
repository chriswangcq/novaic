"""
Context Stack — Integration Protocols

Protocol-driven interfaces for zero-coupling integration.
Host (NovAIC / OpenCode / etc.) implements these to plug in.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from .context.types import Message, ScopeRecord


@runtime_checkable
class AgentExecutor(Protocol):
    """
    How the host runs its agent loop.
    The engine calls this during the EXECUTE phase.
    
    The host controls:
    - Which LLM to call
    - How many rounds to run
    - What tools are available
    
    The engine provides:
    - messages (with skill prompt injected)
    - extra_tools (temporary tools like memory_expand/memory_search)
    """
    def execute(
        self,
        messages: List[Message],
        extra_tools: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Message]:
        """
        Run the agent loop. Return ALL messages (input + new ones).
        
        Args:
            messages: conversation so far (skill prompt already injected)
            extra_tools: temporary tool definitions to add for this execution
                         (e.g., memory_expand, memory_search for Recall Skill)
        
        Returns:
            Full message list after agent finishes (original + new messages)
        """
        ...


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
