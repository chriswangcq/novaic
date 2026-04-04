"""
Context Stack v2 — M3 Test Suite

Covers:
  - Checkpoint blob create/validate/restore cycle
  - Config hash determinism and mismatch detection
  - Blob version validation (forward/backward)
  - Gold fixture: restore → continue push_turn → finalize is consistent
  - Idempotency: duplicate keys are deduplicated across checkpoint/restore
  - Chaos: corrupted blob, missing fields, tampered hash
  - Engine lifecycle: checkpoint_blob/restore_from_blob integration
"""
from __future__ import annotations

import copy
import json
import time
import pytest
from typing import List

from context_stack.v2.types import (
    Message,
    MessageRole,
    ScopePhase,
    ScopeRecord,
    ScopeState,
    StackFrame,
    TurnPayload,
)
from context_stack.v2.config import CompactConfig
from context_stack.v2.defaults import InMemoryScopeStore, CharTokenCounter
from context_stack.v2.engine import ContextEngine
from context_stack.v2.blob import (
    BLOB_VERSION,
    BlobConfigHashError,
    BlobCorruptedError,
    BlobVersionError,
    CheckpointBlobError,
    compute_blob_hash,
    compute_config_hash,
    create_checkpoint_blob,
    restore_from_blob,
    validate_blob,
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


def make_engine(**kwargs) -> ContextEngine:
    return ContextEngine(config=make_config(), **kwargs)


def open_scope(engine: ContextEngine, msgs: List[Message], name: str = "test"):
    """Helper: open a scope via router and return updated messages."""
    r = engine.router.dispatch("skill_begin", {"skill_name": name}, msgs)
    assert r.success
    return r.messages


# ═════════════════════════════════════════════
# Test: Config Hash
# ═════════════════════════════════════════════

class TestConfigHash:
    def test_deterministic(self):
        """Same config → same hash."""
        c1 = make_config()
        c2 = make_config()
        assert compute_config_hash(c1) == compute_config_hash(c2)

    def test_different_configs(self):
        """Different config values → different hash."""
        c1 = make_config(context_window=10_000)
        c2 = make_config(context_window=200_000)
        assert compute_config_hash(c1) != compute_config_hash(c2)

    def test_hash_format(self):
        """Hash should be prefixed with 'sha256:'."""
        h = compute_config_hash(make_config())
        assert h.startswith("sha256:")
        assert len(h) > 70  # sha256: + 64 hex chars

    def test_engine_config_hash(self):
        """Engine exposes config_hash property."""
        engine = make_engine()
        h = engine.config_hash
        assert h == compute_config_hash(engine._config)


# ═════════════════════════════════════════════
# Test: Blob Create
# ═════════════════════════════════════════════

class TestBlobCreate:
    def test_create_empty_engine(self):
        """Empty engine produces a valid blob."""
        engine = make_engine()
        blob = engine.checkpoint_blob()
        assert blob["blob_version"] == BLOB_VERSION
        assert blob["engine_config_hash"] == engine.config_hash
        assert blob["stack_frames"] == []
        assert blob["sessions"] == {}

    def test_create_with_active_scope(self):
        """Engine with active scope serializes frame + session."""
        engine = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine, msgs, "code-review")

        blob = engine.checkpoint_blob(meta={"task_id": "T-42"})

        assert len(blob["stack_frames"]) == 1
        assert blob["stack_frames"][0]["skill_name"] == "code-review"
        assert len(blob["sessions"]) == 1
        assert blob["meta"]["task_id"] == "T-42"

    def test_create_with_nested_scopes(self):
        """Nested scopes: both frames serialized."""
        engine = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine, msgs, "outer")
        msgs = open_scope(engine, msgs, "inner")

        blob = engine.checkpoint_blob()
        assert len(blob["stack_frames"]) == 2
        assert blob["stack_frames"][0]["skill_name"] == "outer"
        assert blob["stack_frames"][1]["skill_name"] == "inner"

    def test_create_is_json_serializable(self):
        """Blob must be JSON serializable."""
        engine = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine, msgs, "test")
        blob = engine.checkpoint_blob()
        serialized = json.dumps(blob)
        deserialized = json.loads(serialized)
        assert deserialized["blob_version"] == BLOB_VERSION

    def test_create_after_close_raises(self):
        """Cannot create blob after engine is closed."""
        engine = make_engine()
        engine.close()
        with pytest.raises(RuntimeError, match="closed"):
            engine.checkpoint_blob()


# ═════════════════════════════════════════════
# Test: Blob Validate
# ═════════════════════════════════════════════

class TestBlobValidate:
    def test_valid_blob_passes(self):
        """A properly created blob passes validation."""
        engine = make_engine()
        msgs = open_scope(engine, make_messages(3), "test")
        blob = engine.checkpoint_blob()
        validate_blob(blob, engine._config)  # Should not raise

    def test_future_version_rejected(self):
        """Blob with future version is rejected."""
        blob = {
            "blob_version": BLOB_VERSION + 1,
            "engine_config_hash": "sha256:xxx",
            "stack_frames": [],
            "sessions": {},
        }
        with pytest.raises(BlobVersionError, match="newer"):
            validate_blob(blob, make_config())

    def test_invalid_version_rejected(self):
        """Blob with version < 1 is rejected."""
        blob = {
            "blob_version": 0,
            "engine_config_hash": "sha256:xxx",
            "stack_frames": [],
            "sessions": {},
        }
        with pytest.raises(BlobVersionError, match="Invalid"):
            validate_blob(blob, make_config())

    def test_config_mismatch_rejected(self):
        """Blob from different config is rejected."""
        config1 = make_config(context_window=10_000)
        engine = ContextEngine(config=config1)
        blob = engine.checkpoint_blob()
        different_config = make_config(context_window=200_000)
        with pytest.raises(BlobConfigHashError, match="mismatch"):
            validate_blob(blob, different_config)

    def test_missing_version_rejected(self):
        """Blob without version field is rejected."""
        blob = {"engine_config_hash": "sha256:xxx", "stack_frames": [], "sessions": {}}
        with pytest.raises(BlobCorruptedError, match="blob_version"):
            validate_blob(blob, make_config())

    def test_missing_fields_rejected(self):
        """Blob with missing required fields is rejected."""
        blob = {
            "blob_version": 1,
            "engine_config_hash": compute_config_hash(make_config()),
        }
        with pytest.raises(BlobCorruptedError, match="missing"):
            validate_blob(blob, make_config())


# ═════════════════════════════════════════════
# Test: Blob Restore
# ═════════════════════════════════════════════

class TestBlobRestore:
    def test_restore_round_trip(self):
        """Create blob → restore into new engine → state matches."""
        engine1 = make_engine()
        msgs = make_messages(5)
        msgs = open_scope(engine1, msgs, "code-review")

        # Do some work
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Working..."),
            Message(role=MessageRole.TOOL, content="result", tool_name="run_test"),
        ]

        blob = engine1.checkpoint_blob(meta={"task_id": "T-1"})

        # Restore into new engine
        engine2 = make_engine()
        engine2.restore_from_blob(blob, msgs)

        # Verify restored state
        assert engine2.stack.depth == 1
        assert engine2.stack.peek().skill_name == "code-review"
        assert engine2.stack.peek().scope_id == engine1.stack.peek().scope_id
        assert len(engine2._sessions) == 1

    def test_restore_then_finalize(self):
        """Restore from blob → push_turn(done=True) → lifecycle completes."""
        engine1 = make_engine()
        msgs = make_messages(5)
        msgs = open_scope(engine1, msgs, "debug")

        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Found the bug."),
        ]
        blob = engine1.checkpoint_blob()

        # Restore
        engine2 = make_engine()
        engine2.restore_from_blob(blob, msgs)

        # Finalize via router
        r = engine2.router.dispatch(
            "skill_end",
            {"report": "Fixed the null pointer dereference in main.c."},
            msgs,
        )
        assert r.success
        assert engine2.stack.is_empty

    def test_restore_preserves_idempotency_keys(self):
        """Idempotency keys are restored and prevent duplicate push_turn."""
        engine1 = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine1, msgs, "test")

        # Push a turn with an idempotency key
        scope_id = engine1.stack.peek().scope_id
        session = engine1._sessions[scope_id]
        session.push_turn(
            TurnPayload(messages=msgs, idempotency_key="key-1"),
            msgs,
        )

        blob = engine1.checkpoint_blob()

        # Restore
        engine2 = make_engine()
        engine2.restore_from_blob(blob, msgs)

        # The restored session should know about "key-1"
        session2 = engine2._sessions[scope_id]
        assert "key-1" in session2._idempotency_keys

    def test_restore_turn_count(self):
        """Turn count is preserved across checkpoint/restore."""
        engine1 = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine1, msgs, "test")

        scope_id = engine1.stack.peek().scope_id
        session = engine1._sessions[scope_id]
        session.push_turn(TurnPayload(messages=msgs), msgs)
        session.push_turn(TurnPayload(messages=msgs), msgs)
        assert session._turn_count == 2

        blob = engine1.checkpoint_blob()

        engine2 = make_engine()
        engine2.restore_from_blob(blob, msgs)
        session2 = engine2._sessions[scope_id]
        assert session2._turn_count == 2

    def test_restore_nested_scopes(self):
        """Checkpoint/restore with nested scopes."""
        engine1 = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine1, msgs, "outer")
        msgs = open_scope(engine1, msgs, "inner")

        blob = engine1.checkpoint_blob()

        engine2 = make_engine()
        engine2.restore_from_blob(blob, msgs)

        assert engine2.stack.depth == 2
        assert engine2.stack.peek().skill_name == "inner"
        assert len(engine2._sessions) == 2

    def test_restore_stats(self):
        """Stats are preserved."""
        engine1 = make_engine()
        with engine1._stats_lock:
            engine1._total_tokens_saved = 42_000
            engine1._total_lifecycles = 7

        blob = engine1.checkpoint_blob()

        engine2 = make_engine()
        engine2.restore_from_blob(blob, make_messages(3))
        assert engine2._total_tokens_saved == 42_000
        assert engine2._total_lifecycles == 7

    def test_restore_into_non_empty_engine_fails(self):
        """Cannot restore into an engine that already has scopes."""
        engine = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine, msgs, "existing")

        blob = engine.checkpoint_blob()

        with pytest.raises(RuntimeError, match="active scopes"):
            engine.restore_from_blob(blob, msgs)

    def test_restore_after_close_raises(self):
        """Cannot restore after engine close."""
        engine = make_engine()
        engine.close()
        with pytest.raises(RuntimeError, match="closed"):
            engine.restore_from_blob({}, [])


# ═════════════════════════════════════════════
# Test: Gold Fixture (versioned checkpoint test)
# ═════════════════════════════════════════════

class TestGoldFixture:
    """
    Gold fixture tests verify that a known-good checkpoint blob
    can be restored and produce consistent results.

    This catches serialization drift between versions.
    """

    def _create_gold_blob(self):
        """Create a deterministic gold blob for testing."""
        engine = make_engine()
        msgs = make_messages(5)
        msgs = open_scope(engine, msgs, "gold-task")

        # Simulate work
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Gold output A."),
            Message(role=MessageRole.TOOL, content="Success", tool_name="build"),
            Message(role=MessageRole.ASSISTANT, content="Gold output B."),
        ]

        blob = engine.checkpoint_blob(meta={"test": "gold"})
        return blob, msgs, engine

    def test_gold_blob_consistent_restore(self):
        """
        Given: a known blob + messages
        When: restore into a new engine and finalize
        Then: result is structurally consistent
        """
        blob, msgs, engine1 = self._create_gold_blob()
        scope_id = engine1.stack.peek().scope_id

        # Restore
        engine2 = make_engine()
        engine2.restore_from_blob(blob, msgs)

        # Verify structural consistency
        assert engine2.stack.depth == 1
        assert engine2.stack.peek().scope_id == scope_id
        assert engine2.stack.peek().skill_name == "gold-task"

        # Finalize
        r = engine2.router.dispatch(
            "skill_end",
            {"report": "Gold task completed successfully."},
            msgs,
        )
        assert r.success
        assert engine2.stack.is_empty

    def test_gold_blob_is_json_stable(self):
        """Serialized blob JSON is deterministic (same config → same structure)."""
        blob1, _, _ = self._create_gold_blob()
        blob2, _, _ = self._create_gold_blob()

        # Keys should be identical (values may differ slightly due to timestamps)
        assert set(blob1.keys()) == set(blob2.keys())
        assert blob1["blob_version"] == blob2["blob_version"]
        assert blob1["engine_config_hash"] == blob2["engine_config_hash"]

    def test_gold_full_cycle_via_push_turn(self):
        """Golden path: checkpoint → restore → push_turn(done=True)."""
        engine1 = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine1, msgs, "golden")

        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Done."),
        ]
        blob = engine1.checkpoint_blob()

        engine2 = make_engine()
        engine2.restore_from_blob(blob, msgs)

        result = engine2.push_turn(TurnPayload(messages=msgs, done=True))
        assert result is not None
        assert result.success
        assert engine2.stack.is_empty


# ═════════════════════════════════════════════
# Test: Chaos (corrupted/tampered blobs)
# ═════════════════════════════════════════════

class TestChaos:
    def test_missing_blob_version(self):
        """Blob without version → BlobCorruptedError."""
        blob = {"engine_config_hash": "x", "stack_frames": [], "sessions": {}}
        with pytest.raises(BlobCorruptedError):
            validate_blob(blob, make_config())

    def test_empty_blob(self):
        """Empty dict → BlobCorruptedError."""
        with pytest.raises(BlobCorruptedError):
            validate_blob({}, make_config())

    def test_wrong_type_stack_frames(self):
        """stack_frames as dict → BlobCorruptedError."""
        blob = {
            "blob_version": 1,
            "engine_config_hash": compute_config_hash(make_config()),
            "stack_frames": "not a list",
            "sessions": {},
        }
        with pytest.raises(BlobCorruptedError, match="list"):
            validate_blob(blob, make_config())

    def test_wrong_type_sessions(self):
        """sessions as list → BlobCorruptedError."""
        blob = {
            "blob_version": 1,
            "engine_config_hash": compute_config_hash(make_config()),
            "stack_frames": [],
            "sessions": [],
        }
        with pytest.raises(BlobCorruptedError, match="dict"):
            validate_blob(blob, make_config())

    def test_tampered_hash(self):
        """Modified config hash → BlobConfigHashError."""
        engine = make_engine()
        blob = engine.checkpoint_blob()
        blob["engine_config_hash"] = "sha256:tampered"
        with pytest.raises(BlobConfigHashError):
            validate_blob(blob, engine._config)

    def test_truncated_blob(self):
        """Blob with removed fields → BlobCorruptedError."""
        engine = make_engine()
        blob = engine.checkpoint_blob()
        del blob["stack_frames"]
        with pytest.raises(BlobCorruptedError, match="missing"):
            validate_blob(blob, engine._config)

    def test_extra_fields_tolerated(self):
        """Extra fields in blob should not cause errors (forward compat)."""
        engine = make_engine()
        blob = engine.checkpoint_blob()
        blob["future_field"] = "hello"
        validate_blob(blob, engine._config)  # Should not raise

    def test_blob_integrity_hash(self):
        """compute_blob_hash detects changes."""
        engine = make_engine()
        blob = engine.checkpoint_blob()
        h1 = compute_blob_hash(blob)

        blob_copy = copy.deepcopy(blob)
        h2 = compute_blob_hash(blob_copy)
        assert h1 == h2  # Same content → same hash

        blob_copy["meta"]["injected"] = "evil"
        h3 = compute_blob_hash(blob_copy)
        assert h1 != h3  # Modified → different hash

    def test_restore_corrupted_session(self):
        """Session with non-resumable phase is skipped."""
        engine1 = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine1, msgs, "test")
        blob = engine1.checkpoint_blob()

        # Mark session as CLOSED (non-resumable)
        scope_id = list(blob["sessions"].keys())[0]
        blob["sessions"][scope_id]["phase"] = "closed"

        engine2 = make_engine()
        engine2.restore_from_blob(blob, msgs)
        # Session should be skipped, but frame is still there
        assert engine2.stack.depth == 1
        assert len(engine2._sessions) == 0  # Session was skipped


# ═════════════════════════════════════════════
# Test: Idempotency across checkpoint boundary
# ═════════════════════════════════════════════

class TestIdempotencyAcrossCheckpoint:
    def test_duplicate_key_after_restore(self):
        """
        Push with key-1 → checkpoint → restore → push with key-1 again
        → should be deduplicated (no double processing).
        """
        engine1 = make_engine()
        msgs = make_messages(3)
        msgs = open_scope(engine1, msgs, "test")

        scope_id = engine1.stack.peek().scope_id
        session1 = engine1._sessions[scope_id]
        session1.push_turn(
            TurnPayload(messages=msgs, idempotency_key="key-A"),
            msgs,
        )
        assert session1._turn_count == 1

        blob = engine1.checkpoint_blob()

        engine2 = make_engine()
        engine2.restore_from_blob(blob, msgs)
        session2 = engine2._sessions[scope_id]

        # Replay key-A → should be skipped
        result = session2.push_turn(
            TurnPayload(messages=msgs, idempotency_key="key-A"),
            msgs,
        )
        assert result is None  # Deduplicated
        assert session2._turn_count == 1  # Not incremented

        # New key → should proceed
        result = session2.push_turn(
            TurnPayload(messages=msgs, idempotency_key="key-B"),
            msgs,
        )
        assert result is None  # Normal (not done)
        assert session2._turn_count == 2  # Incremented
