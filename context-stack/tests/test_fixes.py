"""
Tests for all 7 audit fixes.
"""
import threading
import pytest

from context_stack import (
    ContextEngine, CompactConfig, Skill, SkillType,
    RecallToolRouter,
)
from context_stack.context.types import (
    Message, MessageRole, ScopeRecord, ScopeState,
)
from context_stack.context.checkpoint import CheckpointManager
from context_stack.context.summarizer import StructuredSummarizer
from context_stack.memory.store import MemoryScopeStore
from context_stack.skill.builtins.recall import RecallSkill
from tests.conftest import (
    MockCounter, MockSummarizer, MockExecutor,
    make_messages, make_scope, default_config,
)


# ═══════════════════════════════════════════
# Fix #1: Skill prompt filtered from raw_messages
# ═══════════════════════════════════════════

class TestFix1SkillPromptFiltered:
    def test_raw_messages_exclude_skill_prompt(self):
        """After reload, raw_messages should NOT contain the injected skill prompt."""
        counter = MockCounter()
        config = CompactConfig()
        mgr = CheckpointManager(counter, config)

        pre = [
            Message(role=MessageRole.SYSTEM, content="system"),
            Message(role=MessageRole.USER, content="do something"),
        ]
        # Simulate what lifecycle does: checkpoint → inject prompt → agent work
        scope = make_scope()
        mgr.checkpoint(scope, pre)

        # Pre-hooks inject skill prompt
        skill_prompt = Message(
            role=MessageRole.SYSTEM,
            content="You are an auth expert.",
            metadata={"skill_prompt": True, "skill_name": "user-auth"},
        )
        # Agent work
        agent_msgs = [
            skill_prompt,
            Message(role=MessageRole.ASSISTANT, content="I'll implement auth."),
            Message(role=MessageRole.TOOL, content="Created file", tool_name="write_file"),
            Message(role=MessageRole.ASSISTANT, content="Done."),
        ]
        all_messages = pre + agent_msgs

        summary = Message(role=MessageRole.ASSISTANT, content="Summary")
        mgr.reload(scope, all_messages, summary)

        # raw_messages should NOT contain the skill prompt
        for m in scope.raw_messages:
            assert not m.metadata.get("skill_prompt"), \
                f"Found skill_prompt in raw_messages: {m.content[:50]}"
        # But should contain the agent work
        assert len(scope.raw_messages) == 3  # assistant + tool + assistant (no prompt)

    def test_skill_prompt_in_raw_when_no_metadata(self):
        """Regular system messages (without skill_prompt flag) ARE stored."""
        counter = MockCounter()
        mgr = CheckpointManager(counter)

        scope = make_scope()
        mgr.checkpoint(scope, [])

        agent_msgs = [
            Message(role=MessageRole.SYSTEM, content="context info"),
            Message(role=MessageRole.ASSISTANT, content="Done."),
        ]
        summary = Message(role=MessageRole.ASSISTANT, content="Summary")
        mgr.reload(scope, agent_msgs, summary)

        # System messages without skill_prompt metadata ARE stored
        assert any(m.role == MessageRole.SYSTEM for m in scope.raw_messages)


# ═══════════════════════════════════════════
# Fix #2: Decisions extraction
# ═══════════════════════════════════════════

class TestFix2DecisionsExtraction:
    def setup_method(self):
        self.counter = MockCounter()
        self.summarizer = StructuredSummarizer(
            MockSummarizer("Done."), self.counter,
        )

    def test_extracts_chose_over(self):
        scope = make_scope()
        msgs = [
            Message(
                role=MessageRole.ASSISTANT,
                content="I chose bcrypt over argon2 because it's simpler to deploy.",
            ),
        ]
        self.summarizer.summarize(scope, msgs)
        assert len(scope.decisions) > 0
        assert any("bcrypt" in d for d in scope.decisions)

    def test_extracts_decided_to(self):
        scope = make_scope()
        msgs = [
            Message(
                role=MessageRole.ASSISTANT,
                content="I decided to use PostgreSQL instead of MySQL for the project.",
            ),
        ]
        self.summarizer.summarize(scope, msgs)
        assert len(scope.decisions) > 0

    def test_extracts_ill_use(self):
        scope = make_scope()
        msgs = [
            Message(
                role=MessageRole.ASSISTANT,
                content="I'll use bcrypt for password hashing in this project.",
            ),
        ]
        self.summarizer.summarize(scope, msgs)
        assert len(scope.decisions) > 0

    def test_extracts_going_with(self):
        scope = make_scope()
        msgs = [
            Message(
                role=MessageRole.ASSISTANT,
                content="Going with asyncpg for database connections.",
            ),
        ]
        self.summarizer.summarize(scope, msgs)
        assert len(scope.decisions) > 0

    def test_no_false_positives_from_tool(self):
        scope = make_scope()
        msgs = [
            Message(
                role=MessageRole.TOOL,
                content="chose bcrypt via config",  # tool msg, not assistant
                tool_name="read_file",
            ),
        ]
        self.summarizer.summarize(scope, msgs)
        assert scope.decisions == []

    def test_decisions_capped_at_20(self):
        scope = make_scope()
        # 25 decision-like messages
        msgs = [
            Message(
                role=MessageRole.ASSISTANT,
                content=f"I'll use library_{i} for feature {i} in this project.",
            )
            for i in range(25)
        ]
        self.summarizer.summarize(scope, msgs)
        assert len(scope.decisions) <= 20


# ═══════════════════════════════════════════
# Fix #3: RecallToolRouter
# ═══════════════════════════════════════════

class TestFix3RecallToolRouter:
    def _setup(self):
        store = MemoryScopeStore()
        # seed a scope
        s = ScopeRecord(name="past-work")
        s.state = ScopeState.COMPACTED
        s.summary = "Did some work with bcrypt."
        s.ended_at = s.started_at + 1.0
        store.save(s)
        recall = RecallSkill(store, MockCounter())
        return store, recall

    def test_router_resolves_unresolved_calls(self):
        """If executor returns unresolved recall tool calls, router resolves them."""
        store, recall = self._setup()

        class StubExecutor:
            def execute(self, messages, extra_tools=None):
                # Agent makes a tool call but executor doesn't resolve it
                return messages + [
                    Message(
                        role=MessageRole.ASSISTANT,
                        content="Let me search.",
                        tool_name="memory_search",
                        tool_input='{"query": "bcrypt"}',
                    ),
                ]

        router = RecallToolRouter(StubExecutor(), recall)
        result = router.execute(make_messages(2))

        # Should have the original + assistant call + TOOL response
        tool_msgs = [m for m in result if m.role == MessageRole.TOOL and m.tool_name == "memory_search"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0].metadata.get("recall_routed") is True

    def test_router_skips_already_resolved(self):
        """If a recall call already has a TOOL response, router doesn't duplicate it."""
        store, recall = self._setup()

        class StubExecutor:
            def execute(self, messages, extra_tools=None):
                return messages + [
                    Message(
                        role=MessageRole.ASSISTANT,
                        content="Searching...",
                        tool_name="memory_search",
                        tool_input='{"query": "test"}',
                    ),
                    Message(
                        role=MessageRole.TOOL,
                        content="Already resolved",
                        tool_name="memory_search",
                    ),
                ]

        router = RecallToolRouter(StubExecutor(), recall)
        result = router.execute(make_messages(2))

        tool_msgs = [m for m in result if m.role == MessageRole.TOOL and m.tool_name == "memory_search"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0].content == "Already resolved"

    def test_router_passes_extra_tools_through(self):
        """Extra tools are passed to the underlying executor."""
        store, recall = self._setup()
        received = []

        class CapturingExecutor:
            def execute(self, messages, extra_tools=None):
                received.append(extra_tools)
                return messages

        router = RecallToolRouter(CapturingExecutor(), recall)
        tools = [{"name": "memory_expand"}]
        router.execute(make_messages(2), extra_tools=tools)
        assert received[0] == tools

    def test_engine_auto_wraps_recall_executor(self):
        """Engine should auto-wrap executor during run_recall."""
        executor = MockExecutor()
        engine = ContextEngine(
            executor=executor,
            summarizer=MockSummarizer(),
            counter=MockCounter(),
        )
        # Seed a scope first
        engine.run(Skill(name="seed", prompt="p"), make_messages(2))
        # Run recall — engine should auto-wrap
        result = engine.run_recall(make_messages(2), query="test")
        assert result.success is True


# ═══════════════════════════════════════════
# Fix #4: scope_store_raw config respected
# ═══════════════════════════════════════════

class TestFix4ScopeStoreRawConfig:
    def test_raw_not_stored_when_disabled(self):
        config = CompactConfig(scope_store_raw=False)
        counter = MockCounter()
        mgr = CheckpointManager(counter, config)

        scope = make_scope()
        mgr.checkpoint(scope, [])

        msgs = [
            Message(role=MessageRole.ASSISTANT, content="Did work."),
            Message(role=MessageRole.TOOL, content="result", tool_name="cmd"),
        ]
        summary = Message(role=MessageRole.ASSISTANT, content="Summary")
        mgr.reload(scope, msgs, summary)

        assert scope.raw_messages == []

    def test_raw_stored_when_enabled(self):
        config = CompactConfig(scope_store_raw=True)
        counter = MockCounter()
        mgr = CheckpointManager(counter, config)

        scope = make_scope()
        mgr.checkpoint(scope, [])

        msgs = [
            Message(role=MessageRole.ASSISTANT, content="Did work."),
            Message(role=MessageRole.TOOL, content="result", tool_name="cmd"),
        ]
        summary = Message(role=MessageRole.ASSISTANT, content="Summary")
        mgr.reload(scope, msgs, summary)

        assert len(scope.raw_messages) == 2


# ═══════════════════════════════════════════
# Fix #5: Nested scope guard
# ═══════════════════════════════════════════

class TestFix5NestedScopeGuard:
    def test_nested_run_raises(self):
        """Running a lifecycle while one is active should raise RuntimeError."""
        from context_stack.lifecycle import LifecycleExecutor
        from context_stack.hooks import HookRegistry

        counter = MockCounter()
        store = MemoryScopeStore()
        hooks = HookRegistry()
        checkpoint = CheckpointManager(counter)
        summarizer = StructuredSummarizer(MockSummarizer(), counter)

        lifecycle = LifecycleExecutor(
            checkpoint_mgr=checkpoint,
            summarizer=summarizer,
            counter=counter,
            store=store,
            hooks=hooks,
        )

        error_raised = []

        class NestedExecutor:
            """Tries to start another lifecycle during execute."""
            def execute(self, messages, extra_tools=None):
                try:
                    lifecycle.run(
                        Skill(name="nested", prompt="p"),
                        messages,
                        self,
                    )
                except RuntimeError as e:
                    error_raised.append(str(e))
                return messages + [
                    Message(role=MessageRole.ASSISTANT, content="done"),
                ]

        result = lifecycle.run(
            Skill(name="outer", prompt="p"),
            make_messages(2),
            NestedExecutor(),
        )
        assert result.success is True
        assert len(error_raised) == 1
        assert "Nested scopes are not supported" in error_raised[0]

    def test_active_flag_released_on_failure(self):
        """After a failed lifecycle, the active flag should be released."""
        from context_stack.lifecycle import LifecycleExecutor
        from context_stack.hooks import HookRegistry

        counter = MockCounter()
        lifecycle = LifecycleExecutor(
            checkpoint_mgr=CheckpointManager(counter),
            summarizer=StructuredSummarizer(MockSummarizer(), counter),
            counter=counter,
            store=MemoryScopeStore(),
            hooks=HookRegistry(),
        )

        class CrashExecutor:
            def execute(self, messages, extra_tools=None):
                raise RuntimeError("crash")

        result = lifecycle.run(Skill(name="crash", prompt="p"), make_messages(2), CrashExecutor())
        assert result.success is False

        # Should be able to run again (flag released)
        result2 = lifecycle.run(
            Skill(name="ok", prompt="p"),
            make_messages(2),
            MockExecutor(),
        )
        assert result2.success is True


# ═══════════════════════════════════════════
# Fix #6: Raw messages memory budget
# ═══════════════════════════════════════════

class TestFix6RawMessagesBudget:
    def test_truncates_to_budget(self):
        config = CompactConfig(raw_max_chars_per_scope=500)
        counter = MockCounter()
        mgr = CheckpointManager(counter, config)

        scope = make_scope()
        mgr.checkpoint(scope, [])

        # Create messages totaling ~2000 chars
        msgs = [
            Message(role=MessageRole.ASSISTANT, content="x" * 500)
            for _ in range(4)
        ]
        summary = Message(role=MessageRole.ASSISTANT, content="Summary")
        mgr.reload(scope, msgs, summary)

        # Should have kept at most 500 chars worth
        total_chars = sum(len(m.content) for m in scope.raw_messages)
        assert total_chars <= 500
        assert len(scope.raw_messages) == 1  # only 1 x 500 fits in 500 budget

    def test_keeps_most_recent(self):
        config = CompactConfig(raw_max_chars_per_scope=200)
        counter = MockCounter()
        mgr = CheckpointManager(counter, config)

        scope = make_scope()
        mgr.checkpoint(scope, [])

        msgs = [
            Message(role=MessageRole.ASSISTANT, content=f"msg_{i}_" + "x" * 50)
            for i in range(5)
        ]
        summary = Message(role=MessageRole.ASSISTANT, content="Summary")
        mgr.reload(scope, msgs, summary)

        # Should keep the MOST RECENT messages (last ones)
        if scope.raw_messages:
            last_kept = scope.raw_messages[-1].content
            assert "msg_4_" in last_kept

    def test_no_truncation_under_budget(self):
        config = CompactConfig(raw_max_chars_per_scope=50_000)
        counter = MockCounter()
        mgr = CheckpointManager(counter, config)

        scope = make_scope()
        mgr.checkpoint(scope, [])

        msgs = [
            Message(role=MessageRole.ASSISTANT, content="short msg")
            for _ in range(5)
        ]
        summary = Message(role=MessageRole.ASSISTANT, content="Summary")
        mgr.reload(scope, msgs, summary)

        assert len(scope.raw_messages) == 5


# ═══════════════════════════════════════════
# Fix #7: Thread safety
# ═══════════════════════════════════════════

class TestFix7ThreadSafety:
    def test_concurrent_store_saves(self):
        """Multiple threads saving to store should not crash."""
        store = MemoryScopeStore(max_records=100)
        errors = []

        def save_many(start):
            try:
                for i in range(20):
                    s = ScopeRecord(name=f"scope-{start}-{i}")
                    s.state = ScopeState.COMPACTED
                    s.ended_at = s.started_at + 1.0
                    store.save(s)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=save_many, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert store.count <= 100

    def test_concurrent_reads_and_writes(self):
        """Reading while writing should not crash."""
        store = MemoryScopeStore(max_records=100)
        # Seed some data
        for i in range(10):
            s = ScopeRecord(name=f"scope-{i}")
            s.state = ScopeState.COMPACTED
            s.ended_at = s.started_at + 1.0
            store.save(s)

        errors = []

        def reader():
            try:
                for _ in range(50):
                    store.list_all()
                    store.search("scope")
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for i in range(50):
                    s = ScopeRecord(name=f"new-{i}")
                    s.state = ScopeState.COMPACTED
                    s.ended_at = s.started_at + 1.0
                    store.save(s)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
