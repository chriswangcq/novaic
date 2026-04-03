"""
Tests for skill/builtins/recall.py — RecallSkill and memory tools.
"""
import pytest

from context_stack.context.types import Message, MessageRole, ScopeRecord, ScopeState
from context_stack.memory.store import MemoryScopeStore
from context_stack.skill.builtins.recall import RecallSkill
from context_stack.skill.types import SkillType
from tests.conftest import MockCounter


def make_compacted_scope(name, summary="", files=None, decisions=None, raw_messages=None):
    s = ScopeRecord(name=name)
    s.state = ScopeState.COMPACTED
    s.ended_at = s.started_at + 2.0
    s.summary = summary or f"Done: {name}"
    s.files_changed = files or []
    s.decisions = decisions or []
    s.raw_messages = raw_messages or []
    s.tools_used = {"write_file": 2, "run_command": 1}
    return s


@pytest.fixture
def store():
    s = MemoryScopeStore()
    s.save(make_compacted_scope(
        "user-auth",
        summary="Implemented bcrypt password hashing. Created user model.",
        files=["src/models/user.py", "src/routes/auth.py"],
        decisions=["chose bcrypt over argon2 for simplicity"],
        raw_messages=[
            Message(role=MessageRole.ASSISTANT, content="I'll use bcrypt."),
            Message(role=MessageRole.TOOL, content="Created file src/models/user.py", tool_name="write_file"),
            Message(role=MessageRole.TOOL, content="Error: test failed", tool_name="run_command"),
        ],
    ))
    s.save(make_compacted_scope(
        "db-setup",
        summary="Set up PostgreSQL database with migrations.",
        files=["src/db.py"],
    ))
    return s


@pytest.fixture
def recall(store):
    return RecallSkill(store, MockCounter())


class TestRecallSkillCreate:
    def test_creates_recall_skill(self, recall):
        skill = recall.create(query="password hashing")
        assert skill.skill_type == SkillType.RECALL
        assert "recall:" in skill.name

    def test_prompt_mentions_tools(self, recall):
        skill = recall.create(query="test")
        assert "memory_expand" in skill.prompt
        assert "memory_search" in skill.prompt


class TestToolDefinitions:
    def test_returns_two_tools(self, recall):
        assert len(recall.get_tool_definitions()) == 2

    def test_tool_names(self, recall):
        names = {t["name"] for t in recall.get_tool_definitions()}
        assert names == {"memory_expand", "memory_search"}

    def test_memory_expand_has_scope_id_and_level(self, recall):
        tools = recall.get_tool_definitions()
        expand = next(t for t in tools if t["name"] == "memory_expand")
        params = expand["parameters"]["properties"]
        assert "scope_id" in params
        assert "level" in params

    def test_memory_search_requires_query(self, recall):
        tools = recall.get_tool_definitions()
        search = next(t for t in tools if t["name"] == "memory_search")
        assert "query" in search["parameters"].get("required", [])


class TestMemoryExpand:
    def test_level_0_lists_scopes(self, recall):
        result = recall.execute_tool("memory_expand", {"level": 0})
        assert "user-auth" in result
        assert "db-setup" in result

    def test_level_0_when_no_scope_id(self, recall):
        result = recall.execute_tool("memory_expand", {})
        assert "Available Scopes" in result

    def test_empty_store_message(self):
        r = RecallSkill(MemoryScopeStore(), MockCounter())
        result = r.execute_tool("memory_expand", {"level": 0})
        assert "No past scopes" in result

    def test_level_1_shows_summary(self, recall, store):
        scope = next(s for s in store._records.values() if s.name == "user-auth")
        result = recall.execute_tool("memory_expand", {"scope_id": scope.id, "level": 1})
        assert "Summary" in result
        assert "user-auth" in result

    def test_level_1_shows_files_and_decisions(self, recall, store):
        scope = next(s for s in store._records.values() if s.name == "user-auth")
        result = recall.execute_tool("memory_expand", {"scope_id": scope.id, "level": 1})
        assert "src/models/user.py" in result
        assert "bcrypt" in result

    def test_level_2_shows_assistant_messages(self, recall, store):
        scope = next(s for s in store._records.values() if s.name == "user-auth")
        result = recall.execute_tool("memory_expand", {"scope_id": scope.id, "level": 2})
        assert "ASSISTANT" in result

    def test_level_2_highlights_errors(self, recall, store):
        scope = next(s for s in store._records.values() if s.name == "user-auth")
        result = recall.execute_tool("memory_expand", {"scope_id": scope.id, "level": 2})
        assert "Error" in result or "⚠️" in result

    def test_level_3_shows_all(self, recall, store):
        scope = next(s for s in store._records.values() if s.name == "user-auth")
        result = recall.execute_tool("memory_expand", {"scope_id": scope.id, "level": 3})
        assert "Full Messages" in result

    def test_missing_scope_returns_not_found(self, recall):
        result = recall.execute_tool("memory_expand", {"scope_id": "bad-id", "level": 1})
        assert "not found" in result.lower()

    def test_level_2_no_raw_falls_back(self, recall, store):
        scope = next(s for s in store._records.values() if s.name == "db-setup")
        assert scope.raw_messages == []
        result = recall.execute_tool("memory_expand", {"scope_id": scope.id, "level": 2})
        assert scope.name in result


class TestMemorySearch:
    def test_search_by_summary(self, recall):
        result = recall.execute_tool("memory_search", {"query": "bcrypt"})
        assert "user-auth" in result

    def test_search_by_name(self, recall):
        result = recall.execute_tool("memory_search", {"query": "db-setup"})
        assert "db-setup" in result

    def test_no_results_message(self, recall):
        result = recall.execute_tool("memory_search", {"query": "kubernetes_xyz_404"})
        assert "No scopes" in result or "No" in result

    def test_empty_query_error(self, recall):
        result = recall.execute_tool("memory_search", {"query": ""})
        assert "Please provide" in result

    def test_within_scope_search(self, recall, store):
        scope = next(s for s in store._records.values() if s.name == "user-auth")
        result = recall.execute_tool("memory_search", {"query": "bcrypt", "scope_id": scope.id})
        assert "bcrypt" in result.lower()

    def test_within_scope_no_match(self, recall, store):
        scope = next(s for s in store._records.values() if s.name == "user-auth")
        result = recall.execute_tool("memory_search", {"query": "kubernetes_xyz", "scope_id": scope.id})
        assert "No matches" in result

    def test_empty_store(self):
        r = RecallSkill(MemoryScopeStore(), MockCounter())
        result = r.execute_tool("memory_search", {"query": "anything"})
        assert "No scopes" in result

    def test_unknown_tool(self, recall):
        result = recall.execute_tool("unknown_tool", {})
        assert "Unknown" in result
