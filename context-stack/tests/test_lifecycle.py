"""
Tests for hooks.py and lifecycle.py
"""
import pytest

from context_stack.context.types import Message, MessageRole, ScopeRecord, ScopeState
from context_stack.hooks import HookRegistry
from context_stack.lifecycle import LifecycleExecutor
from context_stack.context.checkpoint import CheckpointManager
from context_stack.context.summarizer import StructuredSummarizer
from context_stack.memory.store import MemoryScopeStore
from context_stack.skill.types import Skill, SkillType
from tests.conftest import MockCounter, MockSummarizer, FailingSummarizer, MockExecutor, make_messages


class TestHookRegistry:
    def setup_method(self):
        self.hooks = HookRegistry()

    def test_pre_hook_receives_and_returns_messages(self):
        sentinel = []

        def my_pre(scope, messages):
            sentinel.append(True)
            return messages

        self.hooks.register_pre("test", my_pre)
        scope = ScopeRecord()
        msgs = make_messages(3)
        result = self.hooks.run_pre_hooks(scope, msgs)
        assert sentinel == [True]
        assert result == msgs

    def test_pre_hook_can_modify_messages(self):
        extra = Message(role=MessageRole.SYSTEM, content="injected")

        def inject(scope, messages):
            return messages + [extra]

        self.hooks.register_pre("inject", inject)
        scope = ScopeRecord()
        result = self.hooks.run_pre_hooks(scope, make_messages(2))
        assert result[-1].content == "injected"

    def test_post_hook_is_observer(self):
        seen_scope = []

        def my_post(scope, messages):
            seen_scope.append(scope.name)

        self.hooks.register_post("test", my_post)
        scope = ScopeRecord(name="my-scope")
        self.hooks.run_post_hooks(scope, make_messages(2))
        assert "my-scope" in seen_scope

    def test_hooks_run_in_priority_order(self):
        order = []
        self.hooks.register_pre("last", lambda s, m: (order.append("last"), m)[1], priority=200)
        self.hooks.register_pre("first", lambda s, m: (order.append("first"), m)[1], priority=100)
        self.hooks.run_pre_hooks(ScopeRecord(), [])
        assert order == ["first", "last"]

    def test_failing_pre_hook_does_not_abort(self):
        def bad_hook(scope, messages):
            raise RuntimeError("boom")

        good_called = []

        def good_hook(scope, messages):
            good_called.append(True)
            return messages

        self.hooks.register_pre("bad", bad_hook, priority=100)
        self.hooks.register_pre("good", good_hook, priority=200)
        # Should not raise, good hook should still run
        self.hooks.run_pre_hooks(ScopeRecord(), [])
        assert good_called == [True]

    def test_failing_post_hook_does_not_abort(self):
        def bad_post(scope, messages):
            raise RuntimeError("boom")

        good_called = []

        def good_post(scope, messages):
            good_called.append(True)

        self.hooks.register_post("bad", bad_post, priority=100)
        self.hooks.register_post("good", good_post, priority=200)
        self.hooks.run_post_hooks(ScopeRecord(), [])
        assert good_called == [True]


class TestLifecycleExecutor:
    def setup_method(self):
        self.counter = MockCounter()
        self.summarizer = MockSummarizer("Completed task successfully.")
        self.store = MemoryScopeStore()
        self.hooks = HookRegistry()
        self.checkpoint = CheckpointManager(self.counter)
        self.structured_sum = StructuredSummarizer(self.summarizer, self.counter)

    def _make_lifecycle(self):
        return LifecycleExecutor(
            checkpoint_mgr=self.checkpoint,
            summarizer=self.structured_sum,
            counter=self.counter,
            store=self.store,
            hooks=self.hooks,
        )

    def _normal_skill(self):
        return Skill(
            name="test-skill",
            skill_type=SkillType.NORMAL,
            prompt="You are a test assistant.",
            workflow="Step 1. Test.",
        )

    def test_lifecycle_returns_success(self):
        executor = MockExecutor()
        lifecycle = self._make_lifecycle()
        msgs = make_messages(3)
        result = lifecycle.run(self._normal_skill(), msgs, executor)
        assert result.success is True
        assert result.error is None

    def test_lifecycle_scope_stored(self):
        executor = MockExecutor()
        lifecycle = self._make_lifecycle()
        lifecycle.run(self._normal_skill(), make_messages(3), executor)
        assert self.store.compacted_count == 1

    def test_lifecycle_reduces_messages(self):
        executor = MockExecutor()
        lifecycle = self._make_lifecycle()
        msgs = make_messages(3)
        result = lifecycle.run(self._normal_skill(), msgs, executor)
        # N original messages + executor adds 6 → compressed to N+1 (pre + summary)
        assert len(result.messages) < len(msgs) + 7

    def test_lifecycle_prompt_injected(self):
        called_with = []

        class CapturingExecutor:
            def execute(self, messages, extra_tools=None):
                called_with.append([m.content for m in messages])
                return messages + [Message(role=MessageRole.ASSISTANT, content="done")]

        lifecycle = self._make_lifecycle()
        lifecycle.run(self._normal_skill(), make_messages(2), CapturingExecutor())
        # Check that the skill prompt was in the messages passed to executor
        all_content = " ".join(called_with[0])
        assert "You are a test assistant" in all_content

    def test_meta_skill_no_prompt_injected(self):
        from context_stack.skill.builtins.meta import MetaSkill
        called_with = []

        class CapturingExecutor:
            def execute(self, messages, extra_tools=None):
                called_with.append(messages)
                return messages + [Message(role=MessageRole.ASSISTANT, content="done")]

        lifecycle = self._make_lifecycle()
        meta = MetaSkill.create(task="do something")
        lifecycle.run(meta, make_messages(2), CapturingExecutor())
        # No skill prompt injected — message count should not increase due to prompt
        all_content = " ".join(m.content for m in called_with[0])
        assert "You are a test assistant" not in all_content

    def test_lifecycle_stores_raw_messages(self):
        executor = MockExecutor()
        lifecycle = self._make_lifecycle()
        lifecycle.run(self._normal_skill(), make_messages(2), executor)
        records = self.store.list_all()
        assert len(records) == 1
        assert len(records[0].raw_messages) > 0

    def test_lifecycle_scope_compacted_state(self):
        executor = MockExecutor()
        lifecycle = self._make_lifecycle()
        result = lifecycle.run(self._normal_skill(), make_messages(2), executor)
        assert result.scope.state == ScopeState.COMPACTED

    def test_lifecycle_executor_called_once(self):
        executor = MockExecutor()
        lifecycle = self._make_lifecycle()
        lifecycle.run(self._normal_skill(), make_messages(2), executor)
        assert executor.call_count == 1

    def test_lifecycle_with_global_pre_hook(self):
        hook_called = []

        def my_pre(scope, messages):
            hook_called.append(scope.name)
            return messages

        self.hooks.register_pre("test", my_pre)
        executor = MockExecutor()
        lifecycle = self._make_lifecycle()
        lifecycle.run(self._normal_skill(), make_messages(2), executor)
        assert "test-skill" in hook_called

    def test_lifecycle_with_global_post_hook(self):
        hook_called = []

        def my_post(scope, messages):
            hook_called.append(scope.name)

        self.hooks.register_post("test", my_post)
        executor = MockExecutor()
        lifecycle = self._make_lifecycle()
        lifecycle.run(self._normal_skill(), make_messages(2), executor)
        assert "test-skill" in hook_called

    def test_lifecycle_failure_returns_error_result(self):
        class BoomExecutor:
            def execute(self, messages, extra_tools=None):
                raise RuntimeError("agent crashed")

        lifecycle = self._make_lifecycle()
        result = lifecycle.run(self._normal_skill(), make_messages(2), BoomExecutor())
        assert result.success is False
        assert "crashed" in result.error

    def test_lifecycle_extra_tools_passed_to_executor(self):
        extra_tools = [{"name": "memory_expand", "description": "test"}]
        executor = MockExecutor()
        lifecycle = self._make_lifecycle()
        lifecycle.run(
            self._normal_skill(),
            make_messages(2),
            executor,
            extra_tools=extra_tools,
        )
        assert executor.last_extra_tools == extra_tools
