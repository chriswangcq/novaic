"""
Tests for context/types.py — core data structures.
"""
import time

import pytest

from context_stack.context.types import (
    CompactAction,
    CompactConfig,
    CompactResult,
    LifecycleResult,
    Message,
    MessageRole,
    ScopeRecord,
    ScopeState,
    StackStatus,
)


class TestMessage:
    def test_default_fields(self):
        m = Message(role=MessageRole.USER, content="hello")
        assert m.role == MessageRole.USER
        assert m.content == "hello"
        assert m.tool_name is None
        assert m.token_count is None
        assert m.metadata == {}
        assert isinstance(m.timestamp, float)

    def test_all_roles(self):
        for role in MessageRole:
            m = Message(role=role, content="x")
            assert m.role == role

    def test_tool_message_fields(self):
        m = Message(
            role=MessageRole.TOOL,
            content='{"result": "ok"}',
            tool_name="write_file",
            tool_input='{"path": "foo.py"}',
        )
        assert m.tool_name == "write_file"
        assert m.tool_input == '{"path": "foo.py"}'

    def test_metadata(self):
        m = Message(role=MessageRole.ASSISTANT, content="x", metadata={"key": "val"})
        assert m.metadata["key"] == "val"


class TestScopeRecord:
    def test_default_state(self):
        s = ScopeRecord()
        assert s.state == ScopeState.OPEN
        assert s.summary == ""
        assert s.raw_messages == []
        assert s.tools_used == {}
        assert s.files_changed == []
        assert s.errors == []

    def test_unique_ids(self):
        ids = {ScopeRecord().id for _ in range(100)}
        assert len(ids) == 100

    def test_duration_open(self):
        s = ScopeRecord()
        time.sleep(0.01)
        assert s.duration_seconds >= 0.01

    def test_duration_closed(self):
        s = ScopeRecord()
        s.ended_at = s.started_at + 5.0
        assert abs(s.duration_seconds - 5.0) < 0.01

    def test_scope_state_transitions(self):
        s = ScopeRecord()
        assert s.state == ScopeState.OPEN
        s.state = ScopeState.COMPACTED
        assert s.state == ScopeState.COMPACTED
        s.state = ScopeState.RECALLED
        assert s.state == ScopeState.RECALLED


class TestCompactConfig:
    def test_defaults(self):
        c = CompactConfig()
        assert c.context_window == 200_000
        assert c.compact_threshold == 0.70
        assert c.emergency_threshold == 0.95
        assert c.scope_store_raw is True

    def test_custom(self):
        c = CompactConfig(context_window=50_000, compact_threshold=0.80)
        assert c.context_window == 50_000
        assert c.compact_threshold == 0.80


class TestCompactResult:
    def test_compression_ratio_zero_before(self):
        r = CompactResult(
            action=CompactAction.SKIP,
            messages=[],
            tokens_before=0,
        )
        assert r.compression_ratio == 0.0

    def test_compression_ratio_calculated(self):
        r = CompactResult(
            action=CompactAction.SCOPE,
            messages=[],
            tokens_before=1000,
            tokens_after=200,
        )
        assert abs(r.compression_ratio - 0.8) < 0.001

    def test_tokens_saved(self):
        r = CompactResult(
            action=CompactAction.AUTO,
            messages=[],
            tokens_before=500,
            tokens_after=100,
            tokens_saved=400,
        )
        assert r.tokens_saved == 400


class TestLifecycleResult:
    def test_success_result(self):
        scope = ScopeRecord(name="test")
        compact = CompactResult(action=CompactAction.SCOPE, messages=[])
        result = LifecycleResult(
            messages=[],
            scope=scope,
            compact=compact,
            skill_name="my-skill",
            success=True,
        )
        assert result.success is True
        assert result.error is None
        assert result.skill_name == "my-skill"

    def test_failure_result(self):
        scope = ScopeRecord()
        compact = CompactResult(action=CompactAction.SKIP, messages=[])
        result = LifecycleResult(
            messages=[],
            scope=scope,
            compact=compact,
            success=False,
            error="something failed",
        )
        assert result.success is False
        assert "failed" in result.error
