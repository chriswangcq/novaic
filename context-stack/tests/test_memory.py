"""
Tests for memory/store.py and memory/search.py
"""
import pytest

from context_stack.context.types import ScopeRecord, ScopeState
from context_stack.memory.store import MemoryScopeStore
from context_stack.memory.search import ScopeSearch


def make_compacted_scope(
    name: str,
    summary: str = "",
    files: list = None,
    decisions: list = None,
    errors: list = None,
    raw_messages: list = None,
):
    s = ScopeRecord(name=name)
    s.state = ScopeState.COMPACTED
    s.ended_at = s.started_at + 1.0
    s.summary = summary or f"Completed task: {name}"
    s.files_changed = files or []
    s.decisions = decisions or []
    s.errors = errors or []
    s.raw_messages = raw_messages or []
    return s


class TestMemoryScopeStore:
    def setup_method(self):
        self.store = MemoryScopeStore(max_records=5)

    def test_save_and_load(self):
        s = make_compacted_scope("task-1")
        self.store.save(s)
        loaded = self.store.load(s.id)
        assert loaded is not None
        assert loaded.id == s.id
        assert loaded.name == "task-1"

    def test_load_missing_returns_none(self):
        assert self.store.load("nonexistent-id") is None

    def test_count(self):
        for i in range(3):
            self.store.save(make_compacted_scope(f"task-{i}"))
        assert self.store.count == 3

    def test_compacted_count(self):
        self.store.save(make_compacted_scope("a"))
        open_scope = ScopeRecord(name="b")
        open_scope.state = ScopeState.OPEN
        self.store.save(open_scope)
        assert self.store.compacted_count == 1

    def test_list_all_most_recent_first(self):
        for i in range(3):
            self.store.save(make_compacted_scope(f"task-{i}"))
        all_scopes = self.store.list_all()
        assert all_scopes[0].name == "task-2"
        assert all_scopes[-1].name == "task-0"

    def test_list_all_excludes_open(self):
        self.store.save(make_compacted_scope("done"))
        open_scope = ScopeRecord(name="in-progress")
        self.store.save(open_scope)
        all_scopes = self.store.list_all()
        assert all(s.name != "in-progress" for s in all_scopes)

    def test_max_records_evicts_oldest(self):
        store = MemoryScopeStore(max_records=3)
        records = [make_compacted_scope(f"task-{i}") for i in range(5)]
        for r in records:
            store.save(r)
        # Should only have last 3
        assert store.count == 3
        listed = store.list_all()
        names = [s.name for s in listed]
        assert "task-0" not in names
        assert "task-4" in names

    def test_update_existing_record(self):
        s = make_compacted_scope("task-1")
        self.store.save(s)
        s.summary = "Updated summary"
        self.store.save(s)
        assert self.store.count == 1
        loaded = self.store.load(s.id)
        assert loaded.summary == "Updated summary"

    def test_get_recallable_names(self):
        from context_stack.context.types import Message, MessageRole
        s1 = make_compacted_scope("scope-with-raw", raw_messages=[
            Message(role=MessageRole.ASSISTANT, content="something")
        ])
        s2 = make_compacted_scope("scope-without-raw")
        self.store.save(s1)
        self.store.save(s2)
        names = self.store.get_recallable_names()
        assert "scope-with-raw" in names
        assert "scope-without-raw" not in names

    def test_search_by_name(self):
        self.store.save(make_compacted_scope("auth-implementation"))
        self.store.save(make_compacted_scope("database-setup"))
        results = self.store.search("auth")
        assert len(results) == 1
        assert results[0].name == "auth-implementation"

    def test_search_no_match(self):
        self.store.save(make_compacted_scope("task-a"))
        results = self.store.search("nomatch_xyz")
        assert results == []


class TestScopeSearch:
    def setup_method(self):
        self.searcher = ScopeSearch()

    def _records(self):
        return [
            make_compacted_scope("user-auth", summary="Implemented bcrypt password hashing",
                                 files=["src/auth.py", "src/models/user.py"],
                                 decisions=["chose bcrypt over argon2"]),
            make_compacted_scope("db-setup", summary="Set up PostgreSQL with connection pool",
                                 files=["src/db.py"],
                                 decisions=["used asyncpg for async queries"]),
            make_compacted_scope("ui-components", summary="Created React components for login",
                                 files=["frontend/Login.tsx"]),
        ]

    def test_keyword_match_name(self):
        results = self.searcher.search(self._records(), "auth")
        assert len(results) >= 1
        assert results[0].name == "user-auth"

    def test_keyword_match_summary(self):
        results = self.searcher.search(self._records(), "bcrypt")
        assert len(results) >= 1
        assert results[0].name == "user-auth"

    def test_keyword_match_files(self):
        results = self.searcher.search(self._records(), "asyncpg")
        assert len(results) >= 1
        assert results[0].name == "db-setup"

    def test_keyword_match_decisions(self):
        results = self.searcher.search(self._records(), "argon2")
        assert len(results) >= 1
        assert results[0].name == "user-auth"

    def test_no_match_returns_empty(self):
        results = self.searcher.search(self._records(), "kubernetes_xyz")
        assert results == []

    def test_limit_respected(self):
        results = self.searcher.search(self._records(), "src", limit=1)
        assert len(results) == 1

    def test_name_has_highest_weight(self):
        # "auth" appears in name "user-auth" AND possibly summary "user-auth"
        results = self.searcher.search(self._records(), "user-auth")
        assert results[0].name == "user-auth"

    def test_search_within_scope_summary(self):
        scope = make_compacted_scope("test", summary="We used bcrypt for passwords")
        results = self.searcher.search_within_scope(scope, "bcrypt")
        assert len(results) > 0
        assert any(r["source"] == "summary" for r in results)

    def test_search_within_scope_files(self):
        scope = make_compacted_scope("test", files=["src/auth.py", "src/db.py"])
        results = self.searcher.search_within_scope(scope, "auth.py")
        assert any(r["source"] == "file" for r in results)

    def test_search_within_scope_decisions(self):
        scope = make_compacted_scope("test", decisions=["chose bcrypt because..."])
        results = self.searcher.search_within_scope(scope, "bcrypt")
        assert any(r["source"] == "decision" for r in results)

    def test_search_within_scope_errors(self):
        scope = make_compacted_scope("test", errors=["AssertionError: test failed"])
        results = self.searcher.search_within_scope(scope, "AssertionError")
        assert any(r["source"] == "error" for r in results)

    def test_search_within_scope_raw_messages(self):
        from context_stack.context.types import Message, MessageRole
        scope = make_compacted_scope("test", raw_messages=[
            Message(role=MessageRole.ASSISTANT, content="We should use postgres for this"),
        ])
        results = self.searcher.search_within_scope(scope, "postgres")
        assert any("message" in r["source"] for r in results)

    def test_search_within_scope_no_match(self):
        scope = make_compacted_scope("test", summary="nothing relevant here")
        results = self.searcher.search_within_scope(scope, "kubernetes_xyz")
        assert results == []

    def test_extract_context_around_match(self):
        text = "prefix " * 10 + "TARGET" + " suffix " * 10
        result = self.searcher._extract_context(text, "target", chars=30)
        assert "TARGET" in result
