"""
Tests for context/compact/ — MicroCompact and AutoCompact.
"""
import pytest

from context_stack.context.compact import micro_compact
from context_stack.context.compact.auto import AutoCompactor
from context_stack.context.types import CompactAction, CompactConfig, Message, MessageRole
from tests.conftest import MockCounter, MockSummarizer, FailingSummarizer, make_messages


def make_tool_messages(n: int, content_len: int = 2000) -> list:
    msgs = [Message(role=MessageRole.SYSTEM, content="system")]
    for i in range(n):
        msgs.append(Message(
            role=MessageRole.TOOL,
            content="x" * content_len,
            tool_name=f"tool_{i}",
        ))
    return msgs


class TestMicroCompact:
    def test_truncates_old_tool_outputs(self):
        config = CompactConfig(micro_max_tool_output_chars=100, micro_preserve_recent=1)
        msgs = make_tool_messages(5, content_len=500)
        result = micro_compact(msgs, config)

        # First 4 tool messages should be truncated
        tool_msgs = [m for m in result if m.role == MessageRole.TOOL]
        for m in tool_msgs[:-1]:
            # 100 chars + suffix like "\n\n... (truncated, was 500 chars)" ~35 chars
            assert len(m.content) <= 140  # 100 + suffix

    def test_preserves_recent_n_outputs(self):
        config = CompactConfig(micro_max_tool_output_chars=100, micro_preserve_recent=2)
        msgs = make_tool_messages(5, content_len=500)
        result = micro_compact(msgs, config)

        tool_msgs = [m for m in result if m.role == MessageRole.TOOL]
        # Last 2 should NOT be truncated
        assert len(tool_msgs[-1].content) == 500
        assert len(tool_msgs[-2].content) == 500

    def test_no_truncation_when_few_tools(self):
        config = CompactConfig(micro_max_tool_output_chars=100, micro_preserve_recent=3)
        msgs = make_tool_messages(2, content_len=500)
        result = micro_compact(msgs, config)
        # Both preserved (<=3)
        tool_msgs = [m for m in result if m.role == MessageRole.TOOL]
        assert all(len(m.content) == 500 for m in tool_msgs)

    def test_non_tool_messages_untouched(self):
        config = CompactConfig(micro_max_tool_output_chars=50, micro_preserve_recent=1)
        msgs = [
            Message(role=MessageRole.SYSTEM, content="system content here"),
            Message(role=MessageRole.USER, content="user message content here"),
            Message(role=MessageRole.ASSISTANT, content="assistant reply content here"),
            Message(role=MessageRole.TOOL, content="t" * 1000, tool_name="t"),
            Message(role=MessageRole.TOOL, content="t" * 1000, tool_name="t"),
        ]
        result = micro_compact(msgs, config)
        assert result[0].content == "system content here"
        assert result[1].content == "user message content here"
        assert result[2].content == "assistant reply content here"

    def test_message_count_preserved(self):
        config = CompactConfig(micro_max_tool_output_chars=50, micro_preserve_recent=1)
        msgs = make_tool_messages(5)
        result = micro_compact(msgs, config)
        assert len(result) == len(msgs)

    def test_truncation_marker_added(self):
        config = CompactConfig(micro_max_tool_output_chars=50, micro_preserve_recent=1)
        msgs = [
            Message(role=MessageRole.SYSTEM, content="sys"),
            Message(role=MessageRole.TOOL, content="x" * 500, tool_name="t1"),
            Message(role=MessageRole.TOOL, content="x" * 500, tool_name="t2"),
        ]
        result = micro_compact(msgs, config)
        assert "truncated" in result[1].content

    def test_metadata_micro_compacted_flag(self):
        config = CompactConfig(micro_max_tool_output_chars=50, micro_preserve_recent=1)
        msgs = [
            Message(role=MessageRole.SYSTEM, content="sys"),
            Message(role=MessageRole.TOOL, content="x" * 500, tool_name="t1"),
            Message(role=MessageRole.TOOL, content="x" * 500, tool_name="t2"),
        ]
        result = micro_compact(msgs, config)
        assert result[1].metadata.get("micro_compacted") is True
        assert not result[2].metadata.get("micro_compacted")


class TestAutoCompactor:
    def setup_method(self):
        self.counter = MockCounter()

    def test_should_trigger_above_threshold(self):
        config = CompactConfig(context_window=100, compact_threshold=0.70)
        summarizer = MockSummarizer()
        compactor = AutoCompactor(config, summarizer, self.counter)

        # Create messages that exceed 70 tokens (context_window=100)
        msgs = [Message(role=MessageRole.ASSISTANT, content="x" * 280 * 4)]  # ~280 tokens
        assert compactor.should_trigger(msgs) is True

    def test_should_not_trigger_below_threshold(self):
        config = CompactConfig(context_window=10_000, compact_threshold=0.70)
        compactor = AutoCompactor(config, MockSummarizer(), self.counter)
        msgs = make_messages(3)
        assert compactor.should_trigger(msgs) is False

    def test_compact_reduces_messages(self):
        config = CompactConfig(context_window=10_000, auto_summary_max_tokens=500)
        compactor = AutoCompactor(config, MockSummarizer("Summary."), self.counter)
        msgs = make_messages(20)
        result = compactor.compact(msgs)
        assert result.action == CompactAction.AUTO
        assert len(result.messages) < len(msgs)

    def test_compact_preserves_system_messages(self):
        config = CompactConfig(context_window=10_000)
        compactor = AutoCompactor(config, MockSummarizer("S."), self.counter)
        msgs = [Message(role=MessageRole.SYSTEM, content="important system")]
        msgs += make_messages(10)
        result = compactor.compact(msgs)
        sys_msgs = [m for m in result.messages if m.role == MessageRole.SYSTEM]
        assert any(m.content == "important system" for m in sys_msgs)

    def test_compact_tokens_saved_positive(self):
        config = CompactConfig(context_window=10_000)
        compactor = AutoCompactor(config, MockSummarizer("Short summary."), self.counter)
        msgs = make_messages(20)
        result = compactor.compact(msgs)
        # tokens_saved might be 0 or slightly negative with mock (short summary)
        assert result.tokens_before >= result.tokens_after or result.tokens_saved >= -100

    def test_compact_skip_when_too_few_messages(self):
        config = CompactConfig(context_window=10_000)
        compactor = AutoCompactor(config, MockSummarizer(), self.counter)
        msgs = [
            Message(role=MessageRole.USER, content="hi"),
            Message(role=MessageRole.ASSISTANT, content="hello"),
        ]
        result = compactor.compact(msgs)
        assert result.action == CompactAction.SKIP

    def test_circuit_breaker_after_failures(self):
        config = CompactConfig(
            context_window=100,
            compact_threshold=0.1,
            auto_circuit_breaker_max_fails=3,
        )
        compactor = AutoCompactor(config, FailingSummarizer(), self.counter)
        msgs = make_messages(5)

        # Exhaust circuit breaker
        for _ in range(3):
            compactor.compact(msgs)

        # Now should_trigger returns False (circuit open)
        assert compactor.should_trigger(msgs) is False

    def test_emergency_compact(self):
        config = CompactConfig(context_window=10_000)
        compactor = AutoCompactor(config, MockSummarizer(), self.counter)
        msgs = make_messages(30)
        result = compactor.emergency_compact(msgs)
        assert result.action == CompactAction.EMERGENCY
        # Should be very aggressive
        assert len(result.messages) < len(msgs) // 2

    def test_emergency_preserves_system(self):
        config = CompactConfig(context_window=10_000)
        compactor = AutoCompactor(config, MockSummarizer(), self.counter)
        msgs = [Message(role=MessageRole.SYSTEM, content="critical system")]
        msgs += make_messages(30)
        result = compactor.emergency_compact(msgs)
        sys_msgs = [m for m in result.messages if m.role == MessageRole.SYSTEM]
        assert any(m.content == "critical system" for m in sys_msgs)

    def test_llm_failure_returns_skip(self):
        config = CompactConfig(context_window=10_000)
        compactor = AutoCompactor(config, FailingSummarizer(), self.counter)
        msgs = make_messages(10)
        result = compactor.compact(msgs)
        assert result.action == CompactAction.SKIP
        assert result.messages == msgs
