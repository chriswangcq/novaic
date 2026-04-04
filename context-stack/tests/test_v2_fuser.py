"""
Context Stack v2 — Gem Fusion (宝石合成 / 消消乐) Test Suite

Covers:
  - Basic fusion: 5 × L0 → 1 × L1
  - Cascade: 5 × L0 triggers L1, 5 × L1 triggers L2
  - Partial: < N scopes → no fusion
  - Force fusion: session-end cleanup
  - fuse_all_remaining: multi-level cleanup
  - Fusion tree: drill-down hierarchy
  - Stats: level counts, max level
  - Custom fuse_fn: pluggable summarization
  - Engine integration: auto-fuse after scope finalization
  - SQLite persistence: fused scopes survive reopen
"""
from __future__ import annotations

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
from context_stack.v2.defaults import InMemoryScopeStore
from context_stack.v2.engine import ContextEngine
from context_stack.v2.fuser import ScopeFuser, _default_fuse_fn
from context_stack.v2.sqlite_store import SqliteScopeStore


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_messages(n: int = 3) -> List[Message]:
    msgs = [Message(role=MessageRole.SYSTEM, content="You are a coding assistant.")]
    for i in range(n - 1):
        role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
        msgs.append(Message(role=role, content=f"Message {i}."))
    return msgs


def make_scope(name: str, level: int = 0, **kwargs) -> ScopeRecord:
    """Create a compacted scope record."""
    now = time.time()
    defaults = dict(
        name=name,
        skill_name="test",
        state=ScopeState.COMPACTED,
        started_at=now - 30,
        ended_at=now,
        summary=f"Completed {name}: implemented feature X.",
        files_changed=[f"{name}.py"],
        tools_used={"write_file": 1, "run_command": 1},
        message_count=8,
        tokens_saved=1000,
        level=level,
    )
    defaults.update(kwargs)
    return ScopeRecord(**defaults)


def make_fuser_config(**kwargs) -> CompactConfig:
    defaults = dict(
        context_window=10_000,
        auto_meta_when_stack_empty=False,
        gem_fusion_enabled=True,
        gem_fusion_merge_factor=5,
    )
    defaults.update(kwargs)
    return CompactConfig(**defaults)


def populate_store(store, count: int, level: int = 0, name_prefix: str = "task") -> List[ScopeRecord]:
    """Create and save N scope records."""
    scopes = []
    for i in range(count):
        t = time.time() + i * 0.01  # Ensure ordering
        s = make_scope(
            f"{name_prefix}-{i}",
            level=level,
            started_at=t - 30,
            ended_at=t,
        )
        store.save(s)
        scopes.append(s)
    return scopes


# ═════════════════════════════════════════════
# Test: Basic Fusion (5 × L0 → 1 × L1)
# ═════════════════════════════════════════════

class TestBasicFusion:
    def test_no_fusion_below_threshold(self):
        """4 scopes at L0 → no fusion (need 5)."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        scopes = populate_store(store, 4)

        result = fuser.maybe_fuse(scopes[-1])
        assert result == []

    def test_exact_threshold_fuses(self):
        """Exactly 5 scopes at L0 → 1 × L1."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        scopes = populate_store(store, 5)

        result = fuser.maybe_fuse(scopes[-1])
        assert len(result) == 1

        fused = result[0]
        assert fused.level == 1
        assert len(fused.children_ids) == 5
        assert fused.state == ScopeState.COMPACTED
        assert fused.skill_name == "__fusion__"
        assert "★" in fused.summary

    def test_children_marked_fused(self):
        """After fusion, children become state=FUSED."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        scopes = populate_store(store, 5)

        fuser.maybe_fuse(scopes[-1])

        for s in scopes:
            loaded = store.load(s.id)
            assert loaded.state == ScopeState.FUSED
            assert loaded.parent_id is not None

    def test_children_have_parent_id(self):
        """Children's parent_id points to the fused scope."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        scopes = populate_store(store, 5)

        result = fuser.maybe_fuse(scopes[-1])
        fused_id = result[0].id

        for s in scopes:
            loaded = store.load(s.id)
            assert loaded.parent_id == fused_id

    def test_six_fuses_first_five(self):
        """6 scopes → first 5 fused, 1 remains as L0."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        scopes = populate_store(store, 6)

        result = fuser.maybe_fuse(scopes[-1])
        assert len(result) == 1

        # Check remaining unfused at L0
        unfused_l0 = [
            r for r in store.list_all(500)
            if r.level == 0 and r.state == ScopeState.COMPACTED
        ]
        assert len(unfused_l0) == 1  # The 6th scope

    def test_fused_aggregates_metadata(self):
        """Fused scope aggregates files, tools, tokens from children."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=3)
        scopes = populate_store(store, 3)

        result = fuser.maybe_fuse(scopes[-1])
        fused = result[0]

        # 3 scopes × 1000 tokens_saved = 3000
        assert fused.tokens_saved == 3000
        # 3 scopes × 8 messages = 24
        assert fused.message_count == 24
        # Each scope had write_file:1, run_command:1 → aggregated
        assert fused.tools_used["write_file"] == 3


# ═════════════════════════════════════════════
# Test: Cascade (消消乐 chain reaction)
# ═════════════════════════════════════════════

class TestCascade:
    def test_l0_to_l1_cascade(self):
        """5 × L0 → 1 × L1 (no further cascade)."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        populate_store(store, 5)

        # Should produce exactly 1 L1
        scopes = store.list_all(500)
        last = [s for s in scopes if s.level == 0][0]
        result = fuser.maybe_fuse(last)
        assert len(result) == 1
        assert result[0].level == 1

    def test_cascade_l0_l1_l2(self):
        """
        25 scopes (5 batches of 5):
          - 5 × L0 → L1 (5 times) → 5 × L1 → L2!
        
        The 消消乐 chain reaction: filling both levels triggers cascade.
        """
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)

        all_fused = []
        for batch in range(5):
            scopes = populate_store(store, 5, name_prefix=f"batch{batch}")
            fused = fuser.maybe_fuse(scopes[-1])
            all_fused.extend(fused)

        # Last batch triggers both L0→L1 AND L1→L2
        # We should have created 5 L1 scopes and 1 L2 scope
        l1_scopes = [f for f in all_fused if f.level == 1]
        l2_scopes = [f for f in all_fused if f.level == 2]
        assert len(l1_scopes) == 5
        assert len(l2_scopes) == 1

        # L2 scope should have 5 children (the L1s)
        assert len(l2_scopes[0].children_ids) == 5

        # Max level reached
        assert fuser.max_level_reached == 2
        assert fuser.total_fusions == 6  # 5 L0→L1 + 1 L1→L2

    def test_merge_factor_3(self):
        """Base-3 carry: 9 scopes → 3 L1 → 1 L2."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=3)

        all_fused = []
        for batch in range(3):
            scopes = populate_store(store, 3, name_prefix=f"b{batch}")
            fused = fuser.maybe_fuse(scopes[-1])
            all_fused.extend(fused)

        l2_scopes = [f for f in all_fused if f.level == 2]
        assert len(l2_scopes) == 1
        assert fuser.total_fusions == 4  # 3 L0→L1 + 1 L1→L2


# ═════════════════════════════════════════════
# Test: Force Fusion (session-end cleanup)
# ═════════════════════════════════════════════

class TestForceFusion:
    def test_force_fuse_partial(self):
        """Force-fuse 3 scopes even though merge_factor is 5."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        populate_store(store, 3)

        result = fuser.force_fuse_level(0)
        assert result is not None
        assert result.level == 1
        assert len(result.children_ids) == 3

    def test_force_fuse_single_no_op(self):
        """Cannot force-fuse just 1 scope."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        populate_store(store, 1)

        result = fuser.force_fuse_level(0)
        assert result is None

    def test_fuse_all_remaining(self):
        """Session-end cleanup: fuse everything into minimal set."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)

        # 7 scopes: fusion produces 1×L1 (5 fused) + 2 remain L0
        # fuse_all: force the remaining 2 into another L1
        populate_store(store, 7)

        # First auto-fuse: 5 → L1
        scopes_l0 = [r for r in store.list_all(500) if r.level == 0]
        fuser.maybe_fuse(scopes_l0[-1])

        # Now force-fuse the remaining 2
        remaining = fuser.fuse_all_remaining()
        assert len(remaining) >= 1

        # All L0 should be fused now
        unfused_l0 = [
            r for r in store.list_all(500)
            if r.level == 0 and r.state == ScopeState.COMPACTED
        ]
        assert len(unfused_l0) == 0


# ═════════════════════════════════════════════
# Test: Fusion Tree (drill-down)
# ═════════════════════════════════════════════

class TestFusionTree:
    def test_tree_structure(self):
        """Fusion tree has correct parent-child structure."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=3)
        scopes = populate_store(store, 3)

        result = fuser.maybe_fuse(scopes[-1])
        fused = result[0]

        tree = fuser.get_fusion_tree(fused.id)
        assert tree["scope"]["id"] == fused.id
        assert tree["scope"]["level"] == 1
        assert len(tree["children"]) == 3
        for child in tree["children"]:
            assert child["scope"]["level"] == 0

    def test_tree_nonexistent(self):
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        tree = fuser.get_fusion_tree("nonexistent")
        assert tree["scope"] is None


# ═════════════════════════════════════════════
# Test: Stats & Queries
# ═════════════════════════════════════════════

class TestFuserStats:
    def test_level_counts(self):
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        populate_store(store, 7)
        fuser.maybe_fuse(store.list_all(500)[-1])

        counts = fuser.get_level_counts()
        assert counts.get(0, 0) == 2   # 7 - 5 = 2 remaining L0
        assert counts.get(1, 0) == 1   # 1 L1

    def test_top_summaries(self):
        """Top summaries = only COMPACTED (not FUSED) scopes."""
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=3)
        populate_store(store, 4)
        fuser.maybe_fuse(store.list_all(500)[-1])

        tops = fuser.get_top_summaries()
        # 1 L1 (fused) + 1 L0 (unfused) = 2 active
        assert len(tops) == 2
        assert all(t.state == ScopeState.COMPACTED for t in tops)

    def test_stats_dict(self):
        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=5)
        populate_store(store, 5)
        fuser.maybe_fuse(store.list_all(500)[-1])

        stats = fuser.get_stats()
        assert stats["merge_factor"] == 5
        assert stats["total_fusions"] == 1
        assert stats["max_level_reached"] == 1

    def test_merge_factor_validation(self):
        """merge_factor < 2 should raise ValueError."""
        with pytest.raises(ValueError, match="≥ 2"):
            ScopeFuser(InMemoryScopeStore(), merge_factor=1)


# ═════════════════════════════════════════════
# Test: Custom fuse_fn
# ═════════════════════════════════════════════

class TestCustomFuseFn:
    def test_custom_summarizer(self):
        """Plug in a custom fuse function for LLM-quality summaries."""
        def my_fuser(children, level):
            names = ", ".join(c.name for c in children)
            return f"[CUSTOM L{level}] Merged: {names}"

        store = InMemoryScopeStore()
        fuser = ScopeFuser(store, merge_factor=3, fuse_fn=my_fuser)
        scopes = populate_store(store, 3)

        result = fuser.maybe_fuse(scopes[-1])
        fused = result[0]
        assert fused.summary.startswith("[CUSTOM L1]")
        assert "task-0" in fused.summary


# ═════════════════════════════════════════════
# Test: Engine Integration (auto-fuse)
# ═════════════════════════════════════════════

class TestEngineIntegration:
    def _make_engine(self, **kwargs):
        config = make_fuser_config(**kwargs)
        return ContextEngine(config=config)

    def _do_scope(self, engine, msgs, name):
        """Helper: open scope → add message → close scope."""
        r1 = engine.router.dispatch(
            "skill_begin", {"skill_name": name}, msgs,
        )
        assert r1.success
        new_msgs = r1.messages + [
            Message(role=MessageRole.ASSISTANT, content=f"{name} done."),
        ]
        r2 = engine.router.dispatch(
            "skill_end",
            {"report": f"Completed {name} successfully."},
            new_msgs,
        )
        assert r2.success
        return r2.messages

    def test_auto_fuse_after_5_scopes(self):
        """Engine with fusion enabled: 5 scopes → auto L1 fusion."""
        engine = self._make_engine()
        msgs = make_messages(3)

        for i in range(5):
            msgs = self._do_scope(engine, msgs, f"task-{i}")

        # Check fuser stats
        assert engine.fuser is not None
        assert engine.fuser.total_fusions >= 1
        assert engine.fuser.max_level_reached >= 1

    def test_fuser_disabled_by_default(self):
        """Without gem_fusion_enabled, fuser is None."""
        config = CompactConfig(auto_meta_when_stack_empty=False)
        engine = ContextEngine(config=config)
        assert engine.fuser is None

    def test_auto_fuse_cascade(self):
        """25 scopes → auto L1 + L2 cascade."""
        engine = self._make_engine()
        msgs = make_messages(3)

        for i in range(25):
            msgs = self._do_scope(engine, msgs, f"task-{i}")

        assert engine.fuser.max_level_reached >= 2
        assert engine.fuser.total_fusions >= 6  # 5×L0→L1 + 1×L1→L2

    def test_fuser_stats_consistent(self):
        """Fuser stats match actual store state."""
        engine = self._make_engine(gem_fusion_merge_factor=3)
        msgs = make_messages(3)

        for i in range(9):
            msgs = self._do_scope(engine, msgs, f"task-{i}")

        stats = engine.fuser.get_stats()
        assert stats["total_fusions"] >= 4  # 3×L0→L1 + 1×L1→L2


# ═════════════════════════════════════════════
# Test: SQLite Persistence
# ═════════════════════════════════════════════

class TestSqliteFusion:
    def test_fused_scopes_in_sqlite(self):
        """Fused scopes persist to SQLite with level/parent/children."""
        with SqliteScopeStore(":memory:") as store:
            fuser = ScopeFuser(store, merge_factor=3)
            scopes = populate_store(store, 3)

            result = fuser.maybe_fuse(scopes[-1])
            fused = result[0]

            # Reload from DB
            loaded = store.load(fused.id)
            assert loaded.level == 1
            assert len(loaded.children_ids) == 3
            assert loaded.skill_name == "__fusion__"

            # Children are FUSED
            for child_id in loaded.children_ids:
                child = store.load(child_id)
                assert child.state == ScopeState.FUSED
                assert child.parent_id == fused.id

    def test_file_persistence(self, tmp_path):
        """Fused scopes survive close/reopen."""
        db_path = str(tmp_path / "fusion.db")

        # Session 1: fuse
        store1 = SqliteScopeStore(db_path)
        fuser1 = ScopeFuser(store1, merge_factor=3)
        scopes = populate_store(store1, 3)
        result = fuser1.maybe_fuse(scopes[-1])
        fused_id = result[0].id
        store1.close()

        # Session 2: verify
        store2 = SqliteScopeStore(db_path)
        loaded = store2.load(fused_id)
        assert loaded is not None
        assert loaded.level == 1
        assert len(loaded.children_ids) == 3
        store2.close()


# ═════════════════════════════════════════════
# Test: Default fuse_fn
# ═════════════════════════════════════════════

class TestDefaultFuseFn:
    def test_produces_markdown(self):
        """Default fuse_fn produces readable markdown."""
        children = [make_scope(f"task-{i}") for i in range(5)]
        summary = _default_fuse_fn(children, 1)

        assert "★" in summary
        assert "Level 1" in summary
        assert "5 scopes merged" in summary
        assert "task-0" in summary

    def test_l2_produces_double_star(self):
        children = [make_scope(f"group-{i}", level=1) for i in range(3)]
        summary = _default_fuse_fn(children, 2)
        assert "★★" in summary
        assert "Level 2" in summary
