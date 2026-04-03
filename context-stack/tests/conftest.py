"""
Shared fixtures for Context Stack tests.
All tests import from here to avoid duplication.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from context_stack import (
    Message,
    MessageRole,
    CompactConfig,
)
from context_stack.context.types import ScopeRecord


# ─────────────────────────────────────────────
# Minimal mock implementations
# ─────────────────────────────────────────────

class MockCounter:
    """Simple char/4 token counter."""
    def count(self, text: str) -> int:
        return max(1, len(text) // 4)

    def count_messages(self, messages: List[Message]) -> int:
        return sum(self.count(m.content) for m in messages)


class MockSummarizer:
    """Deterministic summarizer — always returns the same string."""
    def __init__(self, text: str = "Summary of work done."):
        self._text = text
        self.call_count = 0

    def summarize(
        self,
        messages: List[Message],
        max_tokens: int = 2000,
        instructions: str = "",
    ) -> str:
        self.call_count += 1
        return self._text


class FailingSummarizer:
    """Always raises, used to test fallback paths."""
    def summarize(self, messages, max_tokens=2000, instructions=""):
        raise RuntimeError("LLM unavailable")


class MockExecutor:
    """
    Mock AgentExecutor.
    Appends a fixed set of messages and optionally handles recall tools.
    """
    def __init__(self, extra_messages: Optional[List[Message]] = None, engine=None):
        self._extra = extra_messages or _default_work_messages()
        self._engine = engine
        self.call_count = 0
        self.last_extra_tools: Optional[List[Dict]] = None

    def execute(
        self,
        messages: List[Message],
        extra_tools: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Message]:
        self.call_count += 1
        self.last_extra_tools = extra_tools

        if extra_tools and self._engine:
            # Simulate recall tool usage
            return self._recall_execute(messages)

        return messages + self._extra

    def _recall_execute(self, messages: List[Message]) -> List[Message]:
        new = list(messages)
        search_result = self._engine.handle_recall_tool(
            "memory_search", {"query": "test"}
        )
        new.append(Message(
            role=MessageRole.TOOL,
            content=search_result,
            tool_name="memory_search",
        ))
        expand_result = self._engine.handle_recall_tool(
            "memory_expand", {"level": 0}
        )
        new.append(Message(
            role=MessageRole.TOOL,
            content=expand_result,
            tool_name="memory_expand",
        ))
        new.append(Message(
            role=MessageRole.ASSISTANT,
            content="Based on past work: the answer is X.",
        ))
        return new


def _default_work_messages() -> List[Message]:
    return [
        Message(role=MessageRole.ASSISTANT, content="Looking at the project."),
        Message(role=MessageRole.TOOL, content="file contents here " * 20, tool_name="read_file"),
        Message(role=MessageRole.ASSISTANT, content="I'll create the needed files."),
        Message(role=MessageRole.TOOL, content="Created file src/foo.py", tool_name="write_file"),
        Message(role=MessageRole.TOOL, content="Error: something failed", tool_name="run_command"),
        Message(role=MessageRole.ASSISTANT, content="Fixed the error. Done."),
    ]


# ─────────────────────────────────────────────
# Common builders
# ─────────────────────────────────────────────

def make_messages(n: int = 5) -> List[Message]:
    """Build a generic message list."""
    msgs = [Message(role=MessageRole.SYSTEM, content="You are a coding assistant.")]
    for i in range(n - 1):
        role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
        msgs.append(Message(role=role, content=f"Message {i} content here."))
    return msgs


def make_scope(name: str = "test-scope", skill: str = "test-skill") -> ScopeRecord:
    return ScopeRecord(name=name, skill_name=skill)


def default_config(**kwargs) -> CompactConfig:
    base = dict(
        context_window=10_000,
        compact_threshold=0.70,
        emergency_threshold=0.95,
        scope_store_raw=True,
    )
    base.update(kwargs)
    return CompactConfig(**base)
