"""
Context Stack v2 — M4 Test Suite

Covers:
  - SqliteScopeStore: CRUD, search, WAL mode, schema versioning
  - NovAIC Adapter: message conversion, registry adapter, factory
  - End-to-end: engine with SQLite store + full lifecycle
  - Persistence: scopes survive store close/reopen
"""
from __future__ import annotations

import json
import os
import tempfile
import time
import pytest
from typing import List

from context_stack.v2.types import (
    Message,
    MessageRole,
    ScopeRecord,
    ScopeState,
)
from context_stack.v2.config import CompactConfig
from context_stack.v2.engine import ContextEngine
from context_stack.v2.sqlite_store import SqliteScopeStore, SCHEMA_VERSION
from context_stack.v2.novaic_adapter import (
    SkillRegistryAdapter,
    NovAICSummarizerAdapter,
    convert_messages,
    create_engine_for_novaic,
    export_messages,
    novaic_msg_to_v2,
    v2_msg_to_novaic,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_messages(n: int = 5) -> List[Message]:
    msgs = [Message(role=MessageRole.SYSTEM, content="You are a coding assistant.")]
    for i in range(n - 1):
        role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
        msgs.append(Message(role=role, content=f"Message {i} content here."))
    return msgs


def make_scope_record(name: str = "test", **kwargs) -> ScopeRecord:
    defaults = dict(
        name=name,
        skill_name="meta",
        state=ScopeState.COMPACTED,
        summary=f"Test summary for {name}.",
        files_changed=["file_a.py", "file_b.py"],
        tools_used={"write_file": 2, "run_command": 1},
        decisions=["decision A"],
        errors=[],
        message_count=10,
        tokens_before=5000,
        tokens_after=500,
        tokens_saved=4500,
    )
    defaults.update(kwargs)
    rec = ScopeRecord(**defaults)
    rec.ended_at = rec.started_at + 30
    return rec


def make_config(**kwargs) -> CompactConfig:
    defaults = dict(
        context_window=10_000,
        compact_threshold=0.70,
        emergency_threshold=0.95,
        scope_store_raw=True,
        max_skill_depth=4,
        auto_meta_when_stack_empty=False,
    )
    defaults.update(kwargs)
    return CompactConfig(**defaults)


# ═════════════════════════════════════════════
# Test: SqliteScopeStore — Core CRUD
# ═════════════════════════════════════════════

class TestSqliteStoreCRUD:
    def test_save_and_load(self):
        """Save a scope → load it back → fields match."""
        with SqliteScopeStore(":memory:") as store:
            rec = make_scope_record("test-crud")
            store.save(rec)

            loaded = store.load(rec.id)
            assert loaded is not None
            assert loaded.name == "test-crud"
            assert loaded.skill_name == "meta"
            assert loaded.summary == "Test summary for test-crud."
            assert loaded.files_changed == ["file_a.py", "file_b.py"]
            assert loaded.tools_used == {"write_file": 2, "run_command": 1}
            assert loaded.decisions == ["decision A"]
            assert loaded.tokens_saved == 4500

    def test_load_not_found(self):
        with SqliteScopeStore(":memory:") as store:
            assert store.load("nonexistent") is None

    def test_upsert(self):
        """Save same ID twice → second overwrites first."""
        with SqliteScopeStore(":memory:") as store:
            rec = make_scope_record("v1")
            store.save(rec)

            rec.summary = "Updated summary."
            store.save(rec)

            loaded = store.load(rec.id)
            assert loaded.summary == "Updated summary."
            assert store.count == 1

    def test_delete(self):
        with SqliteScopeStore(":memory:") as store:
            rec = make_scope_record()
            store.save(rec)
            assert store.count == 1

            deleted = store.delete(rec.id)
            assert deleted
            assert store.count == 0
            assert store.load(rec.id) is None

    def test_delete_nonexistent(self):
        with SqliteScopeStore(":memory:") as store:
            assert not store.delete("nonexistent")

    def test_count(self):
        with SqliteScopeStore(":memory:") as store:
            assert store.count == 0
            store.save(make_scope_record("a"))
            store.save(make_scope_record("b"))
            assert store.count == 2

    def test_compacted_count(self):
        with SqliteScopeStore(":memory:") as store:
            r1 = make_scope_record("a")
            r2 = ScopeRecord(name="b", state=ScopeState.OPEN)
            r2.started_at = time.time()
            store.save(r1)
            store.save(r2)
            assert store.compacted_count == 1


# ═════════════════════════════════════════════
# Test: SqliteScopeStore — Raw Messages
# ═════════════════════════════════════════════

class TestSqliteStoreMessages:
    def test_save_and_load_raw_messages(self):
        with SqliteScopeStore(":memory:") as store:
            rec = make_scope_record("with-messages")
            rec.raw_messages = [
                Message(role=MessageRole.ASSISTANT, content="I'll fix the bug."),
                Message(role=MessageRole.TOOL, content="Fixed!", tool_name="edit_file"),
                Message(role=MessageRole.ASSISTANT, content="Bug fixed."),
            ]
            store.save(rec)

            loaded = store.load(rec.id)
            assert len(loaded.raw_messages) == 3
            assert loaded.raw_messages[0].content == "I'll fix the bug."
            assert loaded.raw_messages[1].tool_name == "edit_file"

    def test_raw_messages_budget_limit(self):
        """Raw messages exceeding budget are truncated."""
        with SqliteScopeStore(":memory:", raw_max_chars=50) as store:
            rec = make_scope_record()
            rec.raw_messages = [
                Message(role=MessageRole.ASSISTANT, content="A" * 30),
                Message(role=MessageRole.ASSISTANT, content="B" * 30),
                Message(role=MessageRole.ASSISTANT, content="C" * 30),
            ]
            store.save(rec)

            loaded = store.load(rec.id)
            # Only first message fits within 50 chars budget
            assert len(loaded.raw_messages) == 1
            assert loaded.raw_messages[0].content == "A" * 30

    def test_no_raw_when_disabled(self):
        with SqliteScopeStore(":memory:", store_raw_messages=False) as store:
            rec = make_scope_record()
            rec.raw_messages = [
                Message(role=MessageRole.ASSISTANT, content="test"),
            ]
            store.save(rec)

            loaded = store.load(rec.id)
            assert loaded.raw_messages == []


# ═════════════════════════════════════════════
# Test: SqliteScopeStore — Search & List
# ═════════════════════════════════════════════

class TestSqliteStoreSearch:
    def _populate(self, store):
        records = [
            make_scope_record("implement-auth"),
            make_scope_record("fix-bug-42"),
            make_scope_record("deploy-prod"),
        ]
        records[0].summary = "Implemented JWT authentication."
        records[0].files_changed = ["auth.py", "middleware.py"]
        records[1].summary = "Fixed null pointer bug."
        records[1].files_changed = ["main.c"]
        records[2].summary = "Deployed to production."
        records[2].files_changed = ["Dockerfile"]

        for r in records:
            store.save(r)
        return records

    def test_list_all(self):
        with SqliteScopeStore(":memory:") as store:
            self._populate(store)
            all_recs = store.list_all()
            assert len(all_recs) == 3

    def test_list_all_limit(self):
        with SqliteScopeStore(":memory:") as store:
            self._populate(store)
            limited = store.list_all(limit=2)
            assert len(limited) == 2

    def test_search_by_name(self):
        with SqliteScopeStore(":memory:") as store:
            self._populate(store)
            results = store.search("auth")
            assert len(results) >= 1
            assert any(r.name == "implement-auth" for r in results)

    def test_search_by_summary(self):
        with SqliteScopeStore(":memory:") as store:
            self._populate(store)
            results = store.search("JWT")
            assert len(results) >= 1

    def test_search_by_files(self):
        with SqliteScopeStore(":memory:") as store:
            self._populate(store)
            results = store.search("main.c")
            assert len(results) >= 1

    def test_search_no_results(self):
        with SqliteScopeStore(":memory:") as store:
            self._populate(store)
            results = store.search("xyznonexistent")
            assert len(results) == 0

    def test_search_empty_query(self):
        with SqliteScopeStore(":memory:") as store:
            self._populate(store)
            results = store.search("")
            assert len(results) == 3  # Returns all

    def test_get_recallable_names(self):
        with SqliteScopeStore(":memory:") as store:
            rec = make_scope_record("with-raw")
            rec.raw_messages = [
                Message(role=MessageRole.ASSISTANT, content="test"),
            ]
            store.save(rec)

            # Also save one without raw messages
            store.save(make_scope_record("no-raw"))

            names = store.get_recallable_names()
            assert "with-raw" in names
            assert "no-raw" not in names


# ═════════════════════════════════════════════
# Test: SqliteScopeStore — Persistence (file-based)
# ═════════════════════════════════════════════

class TestSqliteStorePersistence:
    def test_file_persistence(self, tmp_path):
        """Data survives close/reopen cycle."""
        db_path = str(tmp_path / "test.db")

        # Session 1: write
        store1 = SqliteScopeStore(db_path)
        rec = make_scope_record("persistent")
        rec.raw_messages = [
            Message(role=MessageRole.ASSISTANT, content="persisted content"),
        ]
        store1.save(rec)
        saved_id = rec.id
        store1.close()

        # Session 2: read
        store2 = SqliteScopeStore(db_path)
        loaded = store2.load(saved_id)
        assert loaded is not None
        assert loaded.name == "persistent"
        assert loaded.summary == "Test summary for persistent."
        assert len(loaded.raw_messages) == 1
        assert loaded.raw_messages[0].content == "persisted content"
        store2.close()

    def test_schema_version_stored(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = SqliteScopeStore(db_path)
        conn = store._get_connection()
        cur = conn.execute(
            "SELECT value FROM schema_info WHERE key = 'schema_version'"
        )
        assert int(cur.fetchone()[0]) == SCHEMA_VERSION
        store.close()

    def test_db_size(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = SqliteScopeStore(db_path)
        store.save(make_scope_record())
        assert store.db_size_bytes > 0
        store.close()


# ═════════════════════════════════════════════
# Test: SqliteScopeStore — Lifecycle
# ═════════════════════════════════════════════

class TestSqliteStoreLifecycle:
    def test_context_manager(self):
        with SqliteScopeStore(":memory:") as store:
            store.save(make_scope_record())
            assert store.count == 1
        # After context manager, store should be closed
        with pytest.raises(RuntimeError, match="closed"):
            store.count

    def test_double_close_safe(self):
        store = SqliteScopeStore(":memory:")
        store.close()
        store.close()  # Should not raise

    def test_operations_after_close_raise(self):
        store = SqliteScopeStore(":memory:")
        store.close()
        with pytest.raises(RuntimeError, match="closed"):
            store.save(make_scope_record())


# ═════════════════════════════════════════════
# Test: Message Format Conversion
# ═════════════════════════════════════════════

class TestMessageConversion:
    def test_v2_to_novaic_round_trip(self):
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Hello world",
            tool_name="test",
            metadata={"key": "value"},
        )
        d = v2_msg_to_novaic(msg)
        assert d["role"] == "assistant"
        assert d["content"] == "Hello world"
        assert d["tool_name"] == "test"
        assert d["metadata"]["key"] == "value"

        # Convert back
        msg2 = novaic_msg_to_v2(d)
        assert msg2.role == MessageRole.ASSISTANT
        assert msg2.content == "Hello world"
        assert msg2.tool_name == "test"

    def test_dict_to_v2(self):
        d = {
            "role": "system",
            "content": "You are helpful.",
        }
        msg = novaic_msg_to_v2(d)
        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are helpful."

    def test_v2_passthrough(self):
        """v2 Message passed to novaic_msg_to_v2 → returned as-is."""
        msg = Message(role=MessageRole.USER, content="test")
        assert novaic_msg_to_v2(msg) is msg

    def test_batch_convert(self):
        dicts = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        msgs = convert_messages(dicts)
        assert len(msgs) == 2
        assert msgs[0].role == MessageRole.USER

    def test_batch_export(self):
        msgs = make_messages(3)
        dicts = export_messages(msgs)
        assert len(dicts) == 3
        assert all(isinstance(d, dict) for d in dicts)
        assert all("role" in d for d in dicts)

    def test_object_style_conversion(self):
        """Convert an object with attributes (duck-typed NovAIC message)."""
        class FakeMsg:
            role = "tool"
            content = "output"
            tool_name = "run_cmd"
            name = None
            tool_input = None
            tool_call_id = "tc-1"
            id = None
            token_count = 42
            timestamp = 0
            metadata = {}

        msg = novaic_msg_to_v2(FakeMsg())
        assert msg.role == MessageRole.TOOL
        assert msg.tool_name == "run_cmd"
        assert msg.tool_call_id == "tc-1"


# ═════════════════════════════════════════════
# Test: SkillRegistry Adapter
# ═════════════════════════════════════════════

class TestSkillRegistryAdapter:
    def test_get_existing_skill(self):
        """Adapter wraps NovAIC registry.get_by_name → _SkillWrapper."""
        class FakeSkill:
            name = "code-review"
            class body:
                prompt = "Review code carefully."
                workflow = "1. Read code\n2. Comment"
            class metadata:
                category = "analysis"

        class FakeRegistry:
            def get_by_name(self, name):
                if name == "code-review":
                    return FakeSkill()
                return None

        adapter = SkillRegistryAdapter(FakeRegistry())

        skill = adapter.get("code-review")
        assert skill is not None
        assert skill.name == "code-review"
        prompt = skill.build_prompt()
        assert "Review code carefully" in prompt
        assert "Workflow" in prompt
        assert skill.skill_type.value == "analysis"

    def test_get_unknown_skill(self):
        class FakeRegistry:
            def get_by_name(self, name):
                return None

        adapter = SkillRegistryAdapter(FakeRegistry())
        assert adapter.get("nonexistent") is None

    def test_skill_without_body(self):
        class FakeSkill:
            name = "empty"
            body = None
            class metadata:
                category = None

        class FakeRegistry:
            def get_by_name(self, name):
                return FakeSkill()

        adapter = SkillRegistryAdapter(FakeRegistry())
        skill = adapter.get("empty")
        assert skill.build_prompt() is None
        assert skill.skill_type.value == "normal"


# ═════════════════════════════════════════════
# Test: Factory — create_engine_for_novaic
# ═════════════════════════════════════════════

class TestFactory:
    def test_in_memory_defaults(self):
        """Minimal factory call → engine with in-memory store."""
        engine = create_engine_for_novaic(
            context_window=10_000,
            auto_meta=False,
        )
        assert engine is not None
        assert not engine.is_closed
        assert engine.stack.is_empty
        engine.close()

    def test_with_sqlite(self, tmp_path):
        """Factory with db_path → SqliteScopeStore."""
        db_path = str(tmp_path / "factory.db")
        engine = create_engine_for_novaic(
            context_window=10_000,
            db_path=db_path,
            auto_meta=False,
        )

        # Use the engine
        msgs = make_messages(3)
        r = engine.router.dispatch(
            "skill_begin", {"skill_name": "test"}, msgs,
        )
        assert r.success
        msgs = r.messages + [
            Message(role=MessageRole.ASSISTANT, content="Done."),
        ]
        r2 = engine.router.dispatch(
            "skill_end",
            {"report": "Completed test task successfully."},
            msgs,
        )
        assert r2.success

        # Verify scope was persisted
        assert os.path.exists(db_path)
        engine.close()

        # Verify data survives in DB
        store = SqliteScopeStore(db_path)
        assert store.compacted_count >= 1
        store.close()

    def test_with_registry(self):
        """Factory with skill_registry → SkillRegistryAdapter injected."""
        class FakeRegistry:
            def get_by_name(self, name):
                return None

        engine = create_engine_for_novaic(
            context_window=10_000,
            skill_registry=FakeRegistry(),
            auto_meta=False,
        )
        assert engine._registry is not None
        engine.close()


# ═════════════════════════════════════════════
# Test: End-to-End — Engine with SQLite Store
# ═════════════════════════════════════════════

class TestEndToEnd:
    def test_full_lifecycle_with_sqlite(self):
        """Complete lifecycle: begin → work → end → recall from SQLite."""
        with SqliteScopeStore(":memory:") as store:
            engine = ContextEngine(
                config=make_config(),
                store=store,
            )

            msgs = make_messages(5)

            # Begin scope
            r1 = engine.router.dispatch(
                "skill_begin",
                {"skill_name": "deploy", "task": "Deploy to prod"},
                msgs,
            )
            assert r1.success
            msgs = r1.messages

            # Simulate work
            msgs = msgs + [
                Message(role=MessageRole.ASSISTANT, content="Starting deploy..."),
                Message(role=MessageRole.TOOL, content="Build OK", tool_name="run_command"),
                Message(role=MessageRole.ASSISTANT, content="Deploy complete."),
            ]

            # End scope
            r2 = engine.router.dispatch(
                "skill_end",
                {"report": "Deployed v1.2.3 to production. Build succeeded. No errors."},
                msgs,
            )
            assert r2.success
            assert engine.stack.is_empty

            # Verify persisted in SQLite
            assert store.compacted_count == 1
            all_scopes = store.list_all()
            assert len(all_scopes) == 1
            assert all_scopes[0].name == "deploy"

            # Use recall to search
            recall_result = engine.router.dispatch(
                "memory_search",
                {"query": "deploy"},
                r2.messages,
            )
            assert recall_result.success
            assert "deploy" in recall_result.content.lower()

            # Expand scope (auto-advancing — first call = L1)
            scope_id = all_scopes[0].id
            expand_result = engine.router.dispatch(
                "memory_expand",
                {"scope_id": scope_id},
                r2.messages,
            )
            assert expand_result.success
            # Content is injected into messages, tool response is confirmation
            assert "injected" in expand_result.content.lower()
            # The detail is in the enrichment message appended to messages
            assert len(expand_result.messages) > len(r2.messages)
            enrichment = expand_result.messages[-1]
            assert enrichment.metadata.get("memory_expansion") is True
            assert "deploy" in enrichment.content.lower()

            engine.close()

    def test_multi_scope_with_sqlite(self):
        """Multiple scopes: all persisted to SQLite, searchable."""
        with SqliteScopeStore(":memory:") as store:
            engine = ContextEngine(config=make_config(), store=store)
            msgs = make_messages(3)

            for skill_name in ["code-review", "testing", "deploy"]:
                r = engine.router.dispatch(
                    "skill_begin", {"skill_name": skill_name}, msgs,
                )
                msgs = r.messages + [
                    Message(role=MessageRole.ASSISTANT, content=f"{skill_name} done."),
                ]
                r2 = engine.router.dispatch(
                    "skill_end",
                    {"report": f"Completed {skill_name} successfully."},
                    msgs,
                )
                msgs = r2.messages

            assert store.compacted_count == 3
            assert len(store.search("review")) >= 1
            assert len(store.search("deploy")) >= 1

            engine.close()

    def test_checkpoint_restore_with_sqlite(self, tmp_path):
        """Checkpoint + restore with SQLite store."""
        db_path = str(tmp_path / "checkpoint.db")

        # Session 1: start work, checkpoint
        store1 = SqliteScopeStore(db_path)
        engine1 = ContextEngine(config=make_config(), store=store1)
        msgs = make_messages(3)
        r = engine1.router.dispatch(
            "skill_begin", {"skill_name": "long-task"}, msgs,
        )
        msgs = r.messages + [
            Message(role=MessageRole.ASSISTANT, content="Working..."),
        ]
        blob = engine1.checkpoint_blob(meta={"session": "1"})
        store1.close()

        # Session 2: restore, continue, finalize
        store2 = SqliteScopeStore(db_path)
        engine2 = ContextEngine(config=make_config(), store=store2)
        engine2.restore_from_blob(blob, msgs)

        assert engine2.stack.depth == 1
        assert engine2.stack.peek().skill_name == "long-task"

        r2 = engine2.router.dispatch(
            "skill_end",
            {"report": "Long task completed after restore."},
            msgs,
        )
        assert r2.success
        assert engine2.stack.is_empty
        assert store2.compacted_count >= 1
        store2.close()
