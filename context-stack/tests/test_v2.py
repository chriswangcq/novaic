"""
Context Stack v2 — Test Suite

Covers:
  - types.py:         ScopePhase transitions, compute_prefix_hash
  - stack.py:         push/pop/depth enforcement, snapshot
  - checkpoint.py:    prefix hash validation (fast + deep)
  - scope_session.py: phase state machine, finalize, abort
  - prepare.py:       Phase A/B isolation
  - engine.py:        full lifecycle, close(), context manager
  - config.py:        default values
  - defaults.py:      stub implementations
"""
from __future__ import annotations

import pytest
from typing import List

from context_stack.v2.types import (
    Message,
    MessageRole,
    ScopePhase,
    StackFrame,
    TurnPayload,
    CompactAction,
    compute_prefix_hash,
)
from context_stack.v2.config import CompactConfig
from context_stack.v2.defaults import StubSummarizer, CharTokenCounter, InMemoryScopeStore
from context_stack.v2.stack import SkillStack
from context_stack.v2.checkpoint import CheckpointManager
from context_stack.v2.scope_session import ScopeSession
from context_stack.v2.engine import ContextEngine


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_messages(n: int = 5) -> List[Message]:
    msgs = [Message(role=MessageRole.SYSTEM, content="You are a coding assistant.")]
    for i in range(n - 1):
        role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
        msgs.append(Message(role=role, content=f"Message {i} content here."))
    return msgs


def make_config(**kwargs) -> CompactConfig:
    defaults = dict(
        context_window=10_000,
        compact_threshold=0.70,
        emergency_threshold=0.95,
        scope_store_raw=True,
        max_skill_depth=4,
    )
    defaults.update(kwargs)
    return CompactConfig(**defaults)


def make_engine(**kwargs) -> ContextEngine:
    return ContextEngine(config=make_config(), **kwargs)


# ═════════════════════════════════════════════
# Test: types.py
# ═════════════════════════════════════════════

class TestScopePhase:
    def test_terminal_states(self):
        assert ScopePhase.CLOSED.is_terminal
        assert ScopePhase.ABORTED.is_terminal
        assert not ScopePhase.EXECUTING.is_terminal
        assert not ScopePhase.INIT.is_terminal

    def test_valid_transitions(self):
        assert ScopePhase.INIT.can_transition_to(ScopePhase.PRE)
        assert ScopePhase.PRE.can_transition_to(ScopePhase.EXECUTING)
        assert ScopePhase.EXECUTING.can_transition_to(ScopePhase.POST)
        assert ScopePhase.POST.can_transition_to(ScopePhase.SUMMARIZE)
        assert ScopePhase.SUMMARIZE.can_transition_to(ScopePhase.RELOAD)
        assert ScopePhase.RELOAD.can_transition_to(ScopePhase.CLOSED)

    def test_invalid_transitions(self):
        assert not ScopePhase.INIT.can_transition_to(ScopePhase.EXECUTING)
        assert not ScopePhase.EXECUTING.can_transition_to(ScopePhase.RELOAD)
        assert not ScopePhase.CLOSED.can_transition_to(ScopePhase.INIT)

    def test_abort_from_any_non_terminal(self):
        for phase in ScopePhase:
            if not phase.is_terminal:
                assert phase.can_transition_to(ScopePhase.ABORTED)


class TestComputePrefixHash:
    def test_same_messages_same_hash(self):
        msgs = make_messages(3)
        h1 = compute_prefix_hash(msgs)
        h2 = compute_prefix_hash(msgs)
        assert h1 == h2

    def test_different_messages_different_hash(self):
        msgs1 = make_messages(3)
        msgs2 = make_messages(4)
        assert compute_prefix_hash(msgs1) != compute_prefix_hash(msgs2)

    def test_empty_messages(self):
        h = compute_prefix_hash([])
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex


# ═════════════════════════════════════════════
# Test: stack.py
# ═════════════════════════════════════════════

class TestSkillStack:
    def test_push_and_pop(self):
        stack = SkillStack(make_config())
        msgs = make_messages(3)
        frame = stack.push("s1", "code-review", "normal", msgs)
        assert frame.scope_id == "s1"
        assert frame.depth == 0
        assert stack.depth == 1

        popped = stack.pop()
        assert popped.scope_id == "s1"
        assert stack.is_empty

    def test_depth_enforcement(self):
        config = make_config(max_skill_depth=2)
        stack = SkillStack(config)
        msgs = make_messages(3)
        stack.push("s1", "a", "normal", msgs)
        stack.push("s2", "b", "normal", msgs)
        with pytest.raises(RuntimeError, match="depth limit"):
            stack.push("s3", "c", "normal", msgs)

    def test_pop_empty_raises(self):
        stack = SkillStack(make_config())
        with pytest.raises(RuntimeError, match="empty"):
            stack.pop()

    def test_peek(self):
        stack = SkillStack(make_config())
        assert stack.peek() is None
        msgs = make_messages(3)
        stack.push("s1", "a", "normal", msgs)
        assert stack.peek().scope_id == "s1"

    def test_has_only_auto_meta(self):
        stack = SkillStack(make_config())
        msgs = make_messages(3)
        stack.push("s1", "meta", "meta", msgs, auto_meta=True)
        assert stack.has_only_auto_meta()
        stack.push("s2", "code", "normal", msgs)
        assert not stack.has_only_auto_meta()

    def test_validate_top_scope(self):
        stack = SkillStack(make_config())
        msgs = make_messages(3)
        stack.push("s1", "a", "normal", msgs)
        stack.validate_top_scope("s1")  # no error
        with pytest.raises(RuntimeError, match="LIFO"):
            stack.validate_top_scope("wrong-id")

    def test_snapshot_text(self):
        stack = SkillStack(make_config())
        assert "empty" in stack.snapshot_text()

        msgs = make_messages(3)
        stack.push("s1", "meta", "meta", msgs, auto_meta=True)
        stack.push("s2", "code-review", "normal", msgs)
        text = stack.snapshot_text()
        assert "code-review" in text
        assert "meta" in text
        assert "(auto_meta)" in text

    def test_prefix_hash_stored(self):
        stack = SkillStack(make_config())
        msgs = make_messages(5)
        frame = stack.push("s1", "a", "normal", msgs)
        assert len(frame.prefix_hash) == 64  # SHA-256

    def test_clear(self):
        stack = SkillStack(make_config())
        msgs = make_messages(3)
        stack.push("s1", "a", "normal", msgs)
        stack.push("s2", "b", "normal", msgs)
        stack.clear()
        assert stack.is_empty


# ═════════════════════════════════════════════
# Test: checkpoint.py
# ═════════════════════════════════════════════

class TestCheckpointManager:
    def setup_method(self):
        self.counter = CharTokenCounter()
        self.config = make_config()
        self.mgr = CheckpointManager(self.counter, self.config)

    def test_checkpoint_records_state(self):
        from context_stack.v2.types import ScopeRecord
        scope = ScopeRecord(name="test")
        msgs = make_messages(5)
        prefix_hash = self.mgr.checkpoint(scope, msgs)

        assert scope.message_start_idx == 5
        assert scope.tokens_before > 0
        assert len(prefix_hash) == 64

    def test_prefix_validation_passes(self):
        msgs = make_messages(5)
        expected = compute_prefix_hash(msgs[:3])
        self.mgr.validate_prefix(msgs, 3, expected)  # should not raise

    def test_prefix_validation_fails(self):
        msgs = make_messages(5)
        with pytest.raises(ValueError, match="Prefix validation failed"):
            self.mgr.validate_prefix(msgs, 3, "wrong_hash")

    def test_deep_validation_mode(self):
        config = make_config(full_prefix_validation=True)
        mgr = CheckpointManager(self.counter, config)
        msgs = make_messages(5)
        with pytest.raises(ValueError, match="deep mode"):
            mgr.validate_prefix(msgs, 3, "wrong_hash")

    def test_reload(self):
        from context_stack.v2.types import ScopeRecord
        scope = ScopeRecord(name="test")
        msgs = make_messages(5)
        self.mgr.checkpoint(scope, msgs)

        # Add scope messages
        scope_msgs = [
            Message(role=MessageRole.ASSISTANT, content="I did the work."),
            Message(role=MessageRole.TOOL, content="result " * 50, tool_name="run"),
        ]
        all_msgs = msgs + scope_msgs

        summary = Message(
            role=MessageRole.ASSISTANT,
            content="Summary of work.",
            metadata={"compacted": True},
        )
        result = self.mgr.reload(scope, all_msgs, summary)

        assert len(result) == 6  # 5 pre + 1 summary
        assert result[-1].content == "Summary of work."
        assert scope.tokens_saved > 0


# ═════════════════════════════════════════════
# Test: scope_session.py
# ═════════════════════════════════════════════

class TestScopeSession:
    def _make_session(self) -> tuple:
        config = make_config()
        counter = CharTokenCounter()
        store = InMemoryScopeStore()
        msgs = make_messages(5)
        frame = StackFrame(
            scope_id="test-scope",
            skill_name="code-review",
            skill_type="normal",
            message_start_idx=len(msgs),
        )
        checkpoint_mgr = CheckpointManager(counter, config)
        session = ScopeSession(frame, config, checkpoint_mgr, counter, store)
        return session, msgs, store

    def test_begin_transitions_to_executing(self):
        session, msgs, _ = self._make_session()
        assert session.phase == ScopePhase.INIT
        result = session.begin(msgs, skill_prompt="You are a code reviewer.")
        assert session.phase == ScopePhase.EXECUTING
        # Skill prompt should be injected
        assert any(m.metadata.get("skill_prompt") for m in result)

    def test_finalize_without_report(self):
        session, msgs, store = self._make_session()
        session.begin(msgs)

        # Simulate work
        work_msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Review complete."),
        ]
        result = session.finalize(work_msgs)
        assert result.success
        assert session.phase == ScopePhase.CLOSED
        assert result.scope.summary  # should have a fallback summary
        assert store.count == 1

    def test_finalize_with_report(self):
        session, msgs, store = self._make_session()
        session.begin(msgs)

        work_msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Done."),
        ]
        result = session.finalize(work_msgs, report="Reviewed 3 files, no issues found.")
        assert result.success
        assert "Reviewed 3 files" in result.scope.summary

    def test_abort(self):
        session, msgs, _ = self._make_session()
        session.begin(msgs)
        result = session.abort("Connection lost")
        assert not result.success
        assert session.phase == ScopePhase.ABORTED
        assert "Connection lost" in result.error

    def test_push_turn_idempotency(self):
        session, msgs, _ = self._make_session()
        session.begin(msgs)

        payload = TurnPayload(
            messages=msgs,
            mode="full",
            idempotency_key="key-1",
        )
        # First push
        session.push_turn(payload, msgs)
        # Second push with same key — should be ignored
        result = session.push_turn(payload, msgs)
        assert result is None

    def test_push_turn_wrong_phase_raises(self):
        session, msgs, _ = self._make_session()
        # Still in INIT, not EXECUTING
        payload = TurnPayload(messages=msgs)
        with pytest.raises(RuntimeError, match="Cannot push_turn"):
            session.push_turn(payload, msgs)


# ═════════════════════════════════════════════
# Test: engine.py
# ═════════════════════════════════════════════

class TestContextEngine:
    def test_create_with_defaults(self):
        engine = ContextEngine()
        assert engine.stack.is_empty
        assert not engine.is_closed

    def test_close_and_reuse_raises(self):
        engine = ContextEngine()
        engine.close()
        assert engine.is_closed
        with pytest.raises(RuntimeError, match="closed"):
            engine.prepare_messages_for_llm([])

    def test_close_idempotent(self):
        engine = ContextEngine()
        engine.close()
        engine.close()  # should not raise

    def test_context_manager(self):
        with ContextEngine() as engine:
            assert not engine.is_closed
            msgs = make_messages(3)
            engine.prepare_messages_for_llm(msgs)
        assert engine.is_closed

    def test_context_manager_on_exception(self):
        try:
            with ContextEngine() as engine:
                raise ValueError("test")
        except ValueError:
            pass
        assert engine.is_closed

    def test_begin_and_end_scope(self):
        engine = ContextEngine(config=make_config(auto_meta_when_stack_empty=False))
        msgs = make_messages(5)

        # Begin scope
        msgs = engine._begin_scope(
            skill_name="code-review",
            skill_type="normal",
            messages=msgs,
            skill_prompt="Review the code.",
        )
        assert engine.stack.depth == 1
        assert engine.stack.peek().skill_name == "code-review"
        # Should have stack snapshot
        assert any(m.metadata.get("skill_stack_snapshot") for m in msgs)

        # Add work
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Code looks good."),
        ]

        # End scope
        result = engine._end_scope(
            scope_id=engine.stack.peek().scope_id,
            messages=msgs,
            report="Reviewed all files, no issues.",
        )
        assert result.success
        assert engine.stack.is_empty
        # Should have end snapshot
        assert any(
            m.metadata.get("skill_stack_snapshot") and m.metadata.get("after") == "end"
            for m in result.messages
        )

    def test_auto_meta_on_prepare(self):
        engine = ContextEngine(config=make_config(auto_meta_when_stack_empty=True))
        msgs = make_messages(3)
        result = engine.prepare_messages_for_llm(msgs)
        # Auto-meta should have opened
        assert engine.stack.depth == 1
        assert engine.stack.peek().auto_meta

    def test_no_auto_meta_when_disabled(self):
        engine = ContextEngine(config=make_config(auto_meta_when_stack_empty=False))
        msgs = make_messages(3)
        result = engine.prepare_messages_for_llm(msgs)
        assert engine.stack.is_empty

    def test_status(self):
        engine = ContextEngine(config=make_config(auto_meta_when_stack_empty=False))
        msgs = make_messages(5)
        status = engine.status(msgs)
        assert status.used_tokens > 0
        assert status.budget_tokens == 10_000
        assert status.skill_stack == []

    def test_nested_scopes(self):
        engine = ContextEngine(
            config=make_config(auto_meta_when_stack_empty=False, max_skill_depth=3),
        )
        msgs = make_messages(3)

        # Open two nested scopes
        msgs = engine._begin_scope("meta", "meta", msgs, auto_meta=True)
        msgs = engine._begin_scope("code-review", "normal", msgs)
        assert engine.stack.depth == 2

        # Add work for inner scope
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Inner work done."),
        ]

        # End inner scope (LIFO)
        result = engine._end_scope(
            scope_id=engine.stack.peek().scope_id,
            messages=msgs,
            report="Inner scope complete.",
        )
        assert result.success
        assert engine.stack.depth == 1
        assert engine.stack.peek().skill_name == "meta"


# ═════════════════════════════════════════════
# Test: prepare.py (Phase A/B isolation)
# ═════════════════════════════════════════════

class TestPrepare:
    def test_phase_a_only(self):
        """Phase A should auto-open MetaSkill when stack is empty."""
        engine = ContextEngine(config=make_config(auto_meta_when_stack_empty=True))
        msgs = make_messages(3)
        result = engine.prepare_messages_for_llm(msgs)
        assert engine.stack.depth == 1

    def test_phase_b_emergency(self):
        """Phase B should emergency-compact when over threshold."""
        # Create a config with very low context window
        config = make_config(
            context_window=100,
            emergency_threshold=0.50,
            auto_meta_when_stack_empty=False,
        )
        engine = ContextEngine(config=config)
        # Create messages that exceed the threshold
        msgs = [Message(role=MessageRole.USER, content="x" * 200)]
        result = engine.prepare_messages_for_llm(msgs)
        # Should have been compacted
        assert any(m.metadata.get("emergency_compacted") for m in result)

    def test_phase_b_micro_truncation(self):
        """Phase B should truncate old tool outputs."""
        config = make_config(
            auto_meta_when_stack_empty=False,
            micro_max_tool_output_chars=20,
            micro_preserve_recent=1,
        )
        engine = ContextEngine(config=config)
        msgs = [
            Message(role=MessageRole.SYSTEM, content="sys"),
            Message(role=MessageRole.TOOL, content="x" * 1000, tool_name="t1"),
            Message(role=MessageRole.TOOL, content="y" * 1000, tool_name="t2"),
            Message(role=MessageRole.TOOL, content="z" * 100, tool_name="t3"),
        ]
        result = engine.prepare_messages_for_llm(msgs)
        # First tool should be truncated, last preserved
        assert result[1].metadata.get("micro_compacted")
        assert not result[-1].metadata.get("micro_compacted")


# ═════════════════════════════════════════════
# Test: defaults.py
# ═════════════════════════════════════════════

class TestDefaults:
    def test_stub_summarizer(self):
        s = StubSummarizer()
        result = s.summarize(make_messages(3))
        assert "Stub Summary" in result

    def test_char_counter(self):
        c = CharTokenCounter()
        assert c.count("hello world") == 2  # 11 // 4 = 2
        assert c.is_estimate

    def test_in_memory_store(self):
        from context_stack.v2.types import ScopeRecord, ScopeState
        store = InMemoryScopeStore()
        rec = ScopeRecord(name="test", state=ScopeState.COMPACTED)
        store.save(rec)
        assert store.count == 1
        assert store.load(rec.id) == rec
        results = store.search("test")
        assert len(results) == 1


# ═════════════════════════════════════════════
# Test: Report Validator
# ═════════════════════════════════════════════

class TestReportValidator:
    def test_valid_report_passes(self):
        class PassValidator:
            def validate(self, report, scope):
                return None  # pass

        engine = ContextEngine(
            config=make_config(auto_meta_when_stack_empty=False),
            report_validator=PassValidator(),
        )
        msgs = make_messages(5)
        msgs = engine._begin_scope("test", "normal", msgs)
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Work done."),
        ]
        result = engine._end_scope(
            engine.stack.peek().scope_id,
            msgs,
            report="Detailed report of 3 files changed.",
        )
        assert result.success

    def test_rejected_report_returns_error(self):
        class RejectValidator:
            def validate(self, report, scope):
                return "Report too short"

        engine = ContextEngine(
            config=make_config(auto_meta_when_stack_empty=False),
            report_validator=RejectValidator(),
        )
        msgs = make_messages(5)
        msgs = engine._begin_scope("test", "normal", msgs)
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Work done."),
        ]
        result = engine._end_scope(
            engine.stack.peek().scope_id,
            msgs,
            report="OK",
        )
        assert not result.success
        assert "rejected" in result.error.lower()
        # Stack should NOT be popped (model needs to retry)
        assert engine.stack.depth == 1
