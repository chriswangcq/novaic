"""
Tests for context/checkpoint.py — context snapshot management.
"""
import pytest

from context_stack.context.checkpoint import CheckpointManager
from context_stack.context.types import Message, MessageRole, ScopeRecord, ScopeState
from tests.conftest import MockCounter, make_messages, make_scope


@pytest.fixture
def counter():
    return MockCounter()


@pytest.fixture
def mgr(counter):
    return CheckpointManager(counter)


class TestCheckpoint:
    def test_records_start_index(self, mgr):
        messages = make_messages(5)
        scope = make_scope()
        mgr.checkpoint(scope, messages)
        assert scope.message_start_idx == 5

    def test_records_tokens_before(self, mgr, counter):
        messages = make_messages(5)
        scope = make_scope()
        mgr.checkpoint(scope, messages)
        expected = counter.count_messages(messages)
        assert scope.tokens_before == expected

    def test_state_set_to_open(self, mgr):
        scope = make_scope()
        mgr.checkpoint(scope, [])
        assert scope.state == ScopeState.OPEN

    def test_empty_messages(self, mgr):
        scope = make_scope()
        mgr.checkpoint(scope, [])
        assert scope.message_start_idx == 0
        assert scope.tokens_before == 0


class TestReload:
    def test_replaces_scope_messages_with_summary(self, mgr):
        pre = make_messages(3)
        scope_msgs = make_messages(5)
        all_messages = pre + scope_msgs

        scope = make_scope()
        scope.message_start_idx = len(pre)

        summary_msg = Message(
            role=MessageRole.ASSISTANT,
            content="Summary of the scope work.",
            metadata={"compacted": True},
        )
        new_messages = mgr.reload(scope, all_messages, summary_msg)

        # Should have 3 pre + 1 summary
        assert len(new_messages) == len(pre) + 1
        assert new_messages[-1].content == "Summary of the scope work."

    def test_pre_messages_preserved(self, mgr):
        pre = [
            Message(role=MessageRole.SYSTEM, content="system"),
            Message(role=MessageRole.USER, content="user request"),
        ]
        scope_msgs = [
            Message(role=MessageRole.ASSISTANT, content="working..."),
            Message(role=MessageRole.TOOL, content="tool output", tool_name="foo"),
        ]
        all_messages = pre + scope_msgs

        scope = make_scope()
        scope.message_start_idx = len(pre)

        summary_msg = Message(role=MessageRole.ASSISTANT, content="done")
        new_messages = mgr.reload(scope, all_messages, summary_msg)

        # Pre-messages preserved exactly
        assert new_messages[0].content == "system"
        assert new_messages[1].content == "user request"

    def test_raw_messages_stored(self, mgr):
        pre = make_messages(2)
        scope_msgs = make_messages(4)
        all_messages = pre + scope_msgs

        scope = make_scope()
        scope.message_start_idx = len(pre)
        summary_msg = Message(role=MessageRole.ASSISTANT, content="summary")

        mgr.reload(scope, all_messages, summary_msg)

        assert scope.raw_messages == scope_msgs
        assert scope.message_count == len(scope_msgs)

    def test_state_set_to_compacted(self, mgr):
        messages = make_messages(3)
        scope = make_scope()
        scope.message_start_idx = 0
        summary_msg = Message(role=MessageRole.ASSISTANT, content="summary")
        mgr.reload(scope, messages, summary_msg)
        assert scope.state == ScopeState.COMPACTED

    def test_tokens_saved_computed(self, mgr, counter):
        pre = make_messages(2)
        scope_msgs = [
            Message(role=MessageRole.TOOL, content="x" * 2000, tool_name="read_file"),
            Message(role=MessageRole.ASSISTANT, content="done"),
        ]
        all_messages = pre + scope_msgs

        scope = make_scope()
        scope.message_start_idx = len(pre)
        scope.tokens_before = counter.count_messages(pre)

        summary_msg = Message(role=MessageRole.ASSISTANT, content="short summary")
        mgr.reload(scope, all_messages, summary_msg)

        assert scope.tokens_saved > 0

    def test_reload_with_no_scope_messages(self, mgr):
        messages = make_messages(3)
        scope = make_scope()
        scope.message_start_idx = len(messages)  # scope has no messages
        summary_msg = Message(role=MessageRole.ASSISTANT, content="empty scope done")
        new_messages = mgr.reload(scope, messages, summary_msg)
        assert len(new_messages) == len(messages) + 1
        assert scope.raw_messages == []
