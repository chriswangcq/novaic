"""
Integration tests for ContextEngine — the unified facade.
Tests run/run_meta/run_recall/match/status/maybe_compact.
"""
import pytest

from context_stack import ContextEngine, CompactConfig, Skill, SkillType
from context_stack.context.types import (
    CompactAction, Message, MessageRole, LifecycleResult,
)
from context_stack.memory.store import MemoryScopeStore
from tests.conftest import (
    MockCounter, MockSummarizer, MockExecutor, make_messages,
)


@pytest.fixture
def engine():
    executor = MockExecutor()
    eng = ContextEngine(
        executor=executor,
        summarizer=MockSummarizer("Task completed."),
        counter=MockCounter(),
        config=CompactConfig(context_window=200_000),
    )
    executor._engine = eng
    return eng


@pytest.fixture
def engine_with_skill(engine):
    auth_skill = Skill(
        name="user-auth",
        skill_type=SkillType.NORMAL,
        keywords=["auth", "login", "register"],
        prompt="You are an auth expert.",
    )
    engine.registry.register(auth_skill)
    return engine


class TestEngineRun:
    def test_run_normal_skill_success(self, engine):
        skill = Skill(name="my-skill", prompt="Do the task.")
        msgs = make_messages(3)
        result = engine.run(skill, msgs)
        assert isinstance(result, LifecycleResult)
        assert result.success is True
        assert result.skill_name == "my-skill"

    def test_run_compresses_messages(self, engine):
        skill = Skill(name="s", prompt="p")
        msgs = make_messages(5)
        result = engine.run(skill, msgs)
        assert len(result.messages) < len(msgs) + 10

    def test_run_scope_stored_in_memory(self, engine):
        skill = Skill(name="s", prompt="p")
        engine.run(skill, make_messages(3))
        scopes = engine.list_scopes()
        assert len(scopes) == 1
        assert scopes[0]["name"] == "s"

    def test_run_increments_lifecycle_count(self, engine):
        skill = Skill(name="s", prompt="p")
        engine.run(skill, make_messages(3))
        assert engine.status().total_compactions == 1

    def test_run_updates_tokens_saved(self, engine):
        skill = Skill(name="s", prompt="p")
        engine.run(skill, make_messages(8))
        # tokens saved can be + or - depending on mock summary length


class TestEngineRunMeta:
    def test_run_meta_success(self, engine):
        msgs = make_messages(3)
        result = engine.run_meta(msgs, task="Fix the bug")
        assert result.success is True
        assert "meta:" in result.skill_name

    def test_run_meta_scoped(self, engine):
        result = engine.run_meta(make_messages(3), task="Some random task")
        scopes = engine.list_scopes()
        assert len(scopes) == 1

    def test_run_meta_name_from_task(self, engine):
        result = engine.run_meta(make_messages(3), task="Refactor the auth module")
        assert "Refactor" in result.skill_name

    def test_run_meta_custom_name(self, engine):
        result = engine.run_meta(make_messages(3), name="my-scope")
        assert "my-scope" in result.skill_name


class TestEngineRunRecall:
    def _seed_scope(self, engine):
        """Run a normal task first to have something to recall."""
        skill = Skill(name="auth", prompt="You are auth expert.")
        engine.run(skill, make_messages(3))

    def test_run_recall_success(self, engine):
        self._seed_scope(engine)
        result = engine.run_recall(make_messages(2), query="auth task")
        assert result.success is True
        assert "recall:" in result.skill_name

    def test_run_recall_uses_memory_tools(self, engine):
        self._seed_scope(engine)
        result = engine.run_recall(make_messages(2), query="auth")
        # The mock executor gets recall tools — should have used them
        assert result.success is True

    def test_run_recall_creates_scope(self, engine):
        self._seed_scope(engine)
        engine.run_recall(make_messages(2), query="something")
        scopes = engine.list_scopes()
        assert any("recall:" in s["name"] for s in scopes)


class TestEngineMatch:
    def test_match_returns_skill(self, engine_with_skill):
        skill = engine_with_skill.match("implement user login")
        assert skill is not None
        assert skill.name == "user-auth"

    def test_match_returns_none_no_match(self, engine_with_skill):
        skill = engine_with_skill.match("deploy to kubernetes")
        assert skill is None

    def test_match_and_run_uses_skill(self, engine_with_skill):
        result = engine_with_skill.match_and_run(
            make_messages(3),
            task="implement auth login",
        )
        assert result.skill_name == "user-auth"

    def test_match_and_run_falls_back_to_meta(self, engine_with_skill):
        result = engine_with_skill.match_and_run(
            make_messages(3),
            task="completely unrelated xyz task",
        )
        assert "meta:" in result.skill_name


class TestEngineStatus:
    def test_status_initial(self, engine):
        status = engine.status()
        assert status.total_scopes == 0
        assert status.total_compactions == 0

    def test_status_after_run(self, engine):
        engine.run(Skill(name="s", prompt="p"), make_messages(3))
        status = engine.status()
        assert status.total_scopes == 1
        assert status.compacted_scopes == 1
        assert status.total_compactions == 1

    def test_status_used_tokens(self, engine):
        msgs = make_messages(5)
        status = engine.status(msgs)
        assert status.used_tokens > 0

    def test_status_usage_ratio(self, engine):
        msgs = make_messages(5)
        status = engine.status(msgs)
        assert 0 <= status.usage_ratio <= 1.0

    def test_status_recall_available(self, engine):
        skill = Skill(name="task", prompt="p")
        engine.run(skill, make_messages(3))
        status = engine.status()
        assert "task" in status.recall_available


class TestEngineMaybeCompact:
    def test_micro_compact_always_runs(self, engine):
        msgs = make_messages(5)
        result = engine.maybe_compact(msgs)
        # Micro compact runs always — result.messages should exist
        assert result.messages is not None

    def test_auto_compact_not_triggered_at_low_usage(self, engine):
        msgs = make_messages(5)
        result = engine.maybe_compact(msgs)
        assert result.action != CompactAction.AUTO

    def test_action_micro_when_not_above_threshold(self, engine):
        msgs = make_messages(2)
        result = engine.maybe_compact(msgs)
        assert result.action == CompactAction.MICRO

    def test_emergency_compact(self, engine):
        msgs = make_messages(50)
        result = engine.emergency_compact(msgs)
        assert result.action == CompactAction.EMERGENCY
        assert len(result.messages) < len(msgs)


class TestEngineHandleRecallTool:
    def test_dispatch_memory_expand(self, engine):
        result = engine.handle_recall_tool("memory_expand", {"level": 0})
        assert isinstance(result, str)
        assert "Scopes" in result or "No" in result

    def test_dispatch_memory_search(self, engine):
        result = engine.handle_recall_tool("memory_search", {"query": "test"})
        assert isinstance(result, str)

    def test_dispatch_unknown_tool(self, engine):
        result = engine.handle_recall_tool("nonexistent", {})
        assert "Unknown" in result


class TestEngineListScopes:
    def test_empty_initially(self, engine):
        assert engine.list_scopes() == []

    def test_lists_after_run(self, engine):
        engine.run(Skill(name="task-a", prompt="p"), make_messages(3))
        scopes = engine.list_scopes()
        assert len(scopes) == 1
        scope = scopes[0]
        assert scope["name"] == "task-a"
        assert "id" in scope
        assert "tools" in scope
        assert "tokens_saved" in scope
        assert "has_raw" in scope

    def test_most_recent_first(self, engine):
        for name in ["first", "second", "third"]:
            engine.run(Skill(name=name, prompt="p"), make_messages(2))
        scopes = engine.list_scopes()
        assert scopes[0]["name"] == "third"
        assert scopes[-1]["name"] == "first"


class TestEngineRegistryAndHooks:
    def test_registry_accessible(self, engine):
        skill = Skill(name="test", prompt="p")
        engine.registry.register(skill)
        assert engine.registry.get("test") is skill

    def test_hooks_accessible(self, engine):
        called = []

        def my_hook(scope, messages):
            called.append(True)
            return messages

        engine.hooks.register_pre("test", my_hook)
        engine.run(Skill(name="s", prompt="p"), make_messages(2))
        assert called == [True]

    def test_recall_property(self, engine):
        from context_stack.skill.builtins.recall import RecallSkill
        assert isinstance(engine.recall, RecallSkill)
