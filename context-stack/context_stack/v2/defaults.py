"""
Context Stack v2 — Built-in Default Implementations

Zero-dependency implementations for Summarizer, TokenCounter, MemoryBackend.
Ensures the engine can work out-of-the-box without any host-provided dependencies.
"""
from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional

from .types import Message, ScopeRecord, ScopeState

logger = logging.getLogger("context_stack.v2.defaults")


# ─────────────────────────────────────────────
# Stub Summarizer (no LLM)
# ─────────────────────────────────────────────

class StubSummarizer:
    """
    Returns a template-based summary without any LLM call.
    Suitable for testing and CI environments.
    """

    def summarize(
        self,
        messages: List[Message],
        max_tokens: int = 2000,
        instructions: str = "",
    ) -> str:
        msg_count = len(messages)
        roles = {}
        for m in messages:
            roles[m.role.value] = roles.get(m.role.value, 0) + 1

        role_summary = ", ".join(f"{k}: {v}" for k, v in sorted(roles.items()))
        return (
            f"[Stub Summary] {msg_count} messages ({role_summary}). "
            f"Use a real Summarizer for production summaries."
        )


# ─────────────────────────────────────────────
# Char-based Token Counter (no tiktoken)
# ─────────────────────────────────────────────

class CharTokenCounter:
    """
    Estimates tokens as len(text) // 4.
    Suitable for testing. Marks itself as an estimate.
    """

    is_estimate: bool = True

    def count(self, text: str) -> int:
        return max(1, len(text) // 4)

    def count_messages(self, messages: List[Message]) -> int:
        return sum(self.count(m.content) for m in messages)


class TiktokenCounter:
    """
    Accurate token counter using tiktoken (optional dependency).

    Falls back to CharTokenCounter if tiktoken is unavailable.

    Usage:
        counter = TiktokenCounter()           # defaults to cl100k_base
        counter = TiktokenCounter("o200k_base")  # GPT-4o encoding

        n = counter.count("Hello world")
        is_accurate = not counter.is_estimate
    """

    is_estimate: bool = False

    def __init__(self, encoding_name: str = "cl100k_base"):
        self._encoding = None
        self._fallback = CharTokenCounter()
        try:
            import tiktoken
            self._encoding = tiktoken.get_encoding(encoding_name)
            self.is_estimate = False
            logger.info(
                "TiktokenCounter initialized with encoding '%s'",
                encoding_name,
            )
        except ImportError:
            logger.warning(
                "tiktoken not installed, falling back to CharTokenCounter. "
                "Install with: pip install tiktoken"
            )
            self.is_estimate = True
        except Exception as e:
            logger.warning(
                "tiktoken init failed (%s), falling back to CharTokenCounter",
                e,
            )
            self.is_estimate = True

    @classmethod
    def for_model(cls, model: str) -> "TiktokenCounter":
        """
        Create a counter for a specific model name.

        Example:
            counter = TiktokenCounter.for_model("gpt-4o")
            counter = TiktokenCounter.for_model("claude-3-sonnet")
        """
        instance = cls.__new__(cls)
        instance._fallback = CharTokenCounter()
        instance._encoding = None
        instance.is_estimate = True

        try:
            import tiktoken
            instance._encoding = tiktoken.encoding_for_model(model)
            instance.is_estimate = False
            logger.info("TiktokenCounter initialized for model '%s'", model)
        except ImportError:
            logger.warning("tiktoken not installed, using CharTokenCounter")
        except KeyError:
            # Unknown model → try cl100k_base as sensible default
            try:
                import tiktoken
                instance._encoding = tiktoken.get_encoding("cl100k_base")
                instance.is_estimate = False
                logger.info(
                    "Model '%s' unknown, using cl100k_base encoding", model,
                )
            except Exception:
                pass
        except Exception as e:
            logger.warning("tiktoken init failed (%s), using fallback", e)

        return instance

    def count(self, text: str) -> int:
        """Count tokens in a text string."""
        if self._encoding is not None:
            try:
                return len(self._encoding.encode(text))
            except Exception:
                pass
        return self._fallback.count(text)

    def count_messages(self, messages: List[Message]) -> int:
        """
        Count tokens for a list of messages.

        Includes per-message overhead (~4 tokens) to match OpenAI's counting.
        """
        if self._encoding is not None:
            total = 0
            for msg in messages:
                total += 4  # per-message overhead (role, separators)
                total += self.count(msg.content)
                if msg.tool_name:
                    total += self.count(msg.tool_name)
            total += 2  # reply priming
            return total
        return self._fallback.count_messages(messages)


# ─────────────────────────────────────────────
# In-Memory Scope Store
# ─────────────────────────────────────────────

class InMemoryScopeStore:
    """
    Thread-safe in-memory store. Good for single-session.
    Implements MemoryBackend protocol.
    """

    def __init__(self, max_records: int = 200):
        self._records: Dict[str, ScopeRecord] = {}
        self._order: List[str] = []
        self._max_records = max_records
        self._lock = threading.Lock()

    def save(self, record: ScopeRecord) -> None:
        with self._lock:
            if record.id not in self._records:
                self._order.append(record.id)
            self._records[record.id] = record
            while len(self._order) > self._max_records:
                old_id = self._order.pop(0)
                self._records.pop(old_id, None)

    def load(self, scope_id: str) -> Optional[ScopeRecord]:
        with self._lock:
            return self._records.get(scope_id)

    def search(self, query: str, limit: int = 5) -> List[ScopeRecord]:
        """Basic keyword search across scope summaries and names."""
        with self._lock:
            compacted = [
                r for r in self._records.values()
                if r.state == ScopeState.COMPACTED
            ]

        if not query:
            return compacted[:limit]

        query_lower = query.lower()
        scored = []
        for r in compacted:
            text = f"{r.name} {r.summary} {' '.join(r.files_changed)}".lower()
            if query_lower in text:
                scored.append(r)

        return scored[:limit]

    def list_all(self, limit: int = 50) -> List[ScopeRecord]:
        with self._lock:
            compacted = [
                self._records[sid]
                for sid in reversed(self._order)
                if sid in self._records
                and self._records[sid].state == ScopeState.COMPACTED
            ]
            return compacted[:limit]

    def get_recallable_names(self) -> List[str]:
        return [r.name for r in self.list_all() if r.raw_messages]

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._records)

    @property
    def compacted_count(self) -> int:
        with self._lock:
            return sum(
                1 for r in self._records.values()
                if r.state == ScopeState.COMPACTED
            )

    def close(self) -> None:
        """Release resources. No-op for in-memory store."""
        pass
