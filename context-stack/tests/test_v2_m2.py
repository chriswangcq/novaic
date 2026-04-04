"""
Context Stack v2 — M2 Test Suite

Covers:
  - SkillToolRouter: skill_begin/skill_end/memory_* dispatch
  - RecallSkill: L0-L3 expand, search, within-scope search
  - HookRegistry: pre/post hooks, priority ordering
  - Full lifecycle: skill_begin → work → skill_end via router
  - Auto-meta replacement (§4.6.7 replace_when_only_auto)
  - Report validator with retry semantics
  - Engine tool definitions injection
"""
from __future__ import annotations

import json
import pytest
from typing import List

from context_stack.v2.types import (
    Message,
    MessageRole,
    ScopeRecord,
    ScopeState,
)
from context_stack.v2.config import CompactConfig
from context_stack.v2.defaults import InMemoryScopeStore, CharTokenCounter
from context_stack.v2.engine import ContextEngine
from context_stack.v2.tool_router import SkillToolRouter, ToolResult, ENGINE_TOOL_NAMES
from context_stack.v2.recall import RecallSkill
from context_stack.v2.hooks import HookRegistry


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


def make_scope_record(name: str = "test", **kwargs) -> ScopeRecord:
    return ScopeRecord(name=name, state=ScopeState.COMPACTED, **kwargs)


# ═════════════════════════════════════════════
# Test: SkillToolRouter
# ═════════════════════════════════════════════

class TestSkillToolRouter:
    def test_is_engine_tool(self):
        engine = make_engine()
        router = engine.router
        assert router.is_engine_tool("skill_begin")
        assert router.is_engine_tool("skill_end")
        assert router.is_engine_tool("memory_expand")
        assert router.is_engine_tool("memory_search")
        assert not router.is_engine_tool("read_file")

    def test_get_tool_definitions(self):
        engine = make_engine()
        tools = engine.router.get_tool_definitions()
        names = {t["name"] for t in tools}
        assert "skill_begin" in names
        assert "skill_end" in names
        assert "memory_expand" in names
        assert "memory_search" in names

    def test_get_skill_tool_definitions_only(self):
        engine = make_engine()
        tools = engine.router.get_skill_tool_definitions()
        names = {t["name"] for t in tools}
        assert "skill_begin" in names
        assert "skill_end" in names
        assert "memory_expand" not in names

    def test_skill_begin_dispatch(self):
        engine = make_engine()
        msgs = make_messages(3)
        result = engine.router.dispatch(
            "skill_begin",
            {"skill_name": "code-review", "task": "Review the PR"},
            msgs,
        )
        assert result.success
        data = json.loads(result.content)
        assert data["ok"]
        assert data["skill_name"] == "code-review"
        assert data["depth"] == 0
        assert engine.stack.depth == 1

    def test_skill_begin_missing_name(self):
        engine = make_engine()
        msgs = make_messages(3)
        result = engine.router.dispatch("skill_begin", {}, msgs)
        assert not result.success
        data = json.loads(result.content)
        assert not data["ok"]

    def test_skill_begin_depth_limit(self):
        engine = ContextEngine(config=make_config(max_skill_depth=1))
        msgs = make_messages(3)
        r1 = engine.router.dispatch(
            "skill_begin", {"skill_name": "a"}, msgs,
        )
        assert r1.success
        msgs = r1.messages

        r2 = engine.router.dispatch(
            "skill_begin", {"skill_name": "b"}, msgs,
        )
        assert not r2.success
        data = json.loads(r2.content)
        assert "depth limit" in data["error"].lower()

    def test_skill_end_dispatch(self):
        engine = make_engine()
        msgs = make_messages(3)

        # Begin
        r1 = engine.router.dispatch(
            "skill_begin", {"skill_name": "code-review"}, msgs,
        )
        msgs = r1.messages

        # Add work
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Review complete."),
        ]

        # End
        r2 = engine.router.dispatch(
            "skill_end",
            {"report": "Reviewed 3 files. No issues found."},
            msgs,
        )
        assert r2.success
        data = json.loads(r2.content)
        assert data["ok"]
        assert data["tokens_saved"] >= 0
        assert data["depth_after_pop"] == 0
        assert engine.stack.is_empty

    def test_skill_end_wrong_scope_id(self):
        engine = make_engine()
        msgs = make_messages(3)
        r1 = engine.router.dispatch(
            "skill_begin", {"skill_name": "a"}, msgs,
        )
        msgs = r1.messages

        r2 = engine.router.dispatch(
            "skill_end",
            {"report": "done", "scope_id": "wrong-id"},
            msgs,
        )
        assert not r2.success

    def test_unknown_tool(self):
        engine = make_engine()
        result = engine.router.dispatch("foobar", {}, make_messages(3))
        assert not result.success

    def test_full_lifecycle_via_router(self):
        """Full lifecycle: skill_begin → work → skill_end via router."""
        engine = make_engine()
        msgs = make_messages(5)

        # Begin
        r1 = engine.router.dispatch(
            "skill_begin",
            {"skill_name": "debugging", "task": "Fix the segfault"},
            msgs,
        )
        assert r1.success
        msgs = r1.messages

        # Simulate work
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Found the bug."),
            Message(role=MessageRole.TOOL, content="Fixed in main.c", tool_name="edit_file"),
            Message(role=MessageRole.ASSISTANT, content="Bug fixed, tests pass."),
        ]

        # End with comprehensive report
        r2 = engine.router.dispatch(
            "skill_end",
            {"report": "Fixed segfault in main.c line 42. Root cause: null pointer dereference."},
            msgs,
        )
        assert r2.success
        data = json.loads(r2.content)
        assert data["ok"]
        assert engine.stack.is_empty

        # Messages should be compacted
        assert len(r2.messages) < len(msgs)


# ═════════════════════════════════════════════
# Test: Auto-meta replacement (§4.6.7)
# ═════════════════════════════════════════════

class TestAutoMetaReplacement:
    def test_stack_under_mode(self):
        """Default: auto_meta stays at bottom, new skill stacks on top."""
        engine = ContextEngine(
            config=make_config(auto_meta_when_stack_empty=True),
        )
        msgs = make_messages(3)
        msgs = engine.prepare_messages_for_llm(msgs)
        assert engine.stack.depth == 1
        assert engine.stack.peek().auto_meta

        # Explicit skill_begin stacks on top
        r = engine.router.dispatch(
            "skill_begin", {"skill_name": "code-review"}, msgs,
        )
        assert r.success
        assert engine.stack.depth == 2
        assert engine.stack.peek().skill_name == "code-review"

    def test_replace_when_only_auto(self):
        """replace_when_only_auto: auto_meta is replaced by explicit skill."""
        engine = ContextEngine(
            config=make_config(
                auto_meta_when_stack_empty=True,
                auto_meta_explicit_mode="replace_when_only_auto",
            ),
        )
        msgs = make_messages(3)
        msgs = engine.prepare_messages_for_llm(msgs)
        assert engine.stack.depth == 1
        assert engine.stack.peek().auto_meta

        # Explicit skill_begin should replace auto_meta
        r = engine.router.dispatch(
            "skill_begin", {"skill_name": "code-review"}, msgs,
        )
        assert r.success
        # Stack should be depth 1 (auto_meta replaced, not stacked)
        assert engine.stack.depth == 1
        assert engine.stack.peek().skill_name == "code-review"
        assert not engine.stack.peek().auto_meta


# ═════════════════════════════════════════════
# Test: RecallSkill
# ═════════════════════════════════════════════

class TestRecallSkill:
    """
    Tests for v2 RecallSkill with tree-based ID navigation.

    The new API uses a single `id` parameter for memory_expand:
      - ""               → list all root scopes
      - "scope_id"       → scope overview with child node IDs
      - "scope_id.meta"  → decisions, tools, errors
      - "scope_id.files" → file change list
      - "scope_id.messages" → message list with per-msg IDs
      - "scope_id.msg.N" → full content of message N
    """

    def _make_recall_with_data(self):
        """Create a RecallSkill with some pre-populated scope records."""
        store = InMemoryScopeStore()
        counter = CharTokenCounter()

        # Add some scope records
        r1 = ScopeRecord(
            name="implement-auth",
            skill_name="coding",
            state=ScopeState.COMPACTED,
            summary="Implemented JWT authentication.",
            files_changed=["auth.py", "middleware.py"],
            tools_used={"write_file": 3, "run_command": 2},
            decisions=["chose JWT over session cookies"],
            errors=[],
            message_count=12,
        )
        r1.raw_messages = [
            Message(role=MessageRole.ASSISTANT, content="I'll implement JWT auth."),
            Message(role=MessageRole.TOOL, content="Created auth.py", tool_name="write_file"),
            Message(role=MessageRole.ASSISTANT, content="Auth implementation complete."),
        ]
        r1.ended_at = r1.started_at + 120

        r2 = ScopeRecord(
            name="fix-bug-42",
            skill_name="debugging",
            state=ScopeState.COMPACTED,
            summary="Fixed null pointer dereference bug.",
            files_changed=["main.c"],
            tools_used={"edit_file": 1},
            decisions=[],
            errors=["Error: segfault in main.c:42"],
            message_count=8,
        )
        r2.ended_at = r2.started_at + 60

        store.save(r1)
        store.save(r2)

        recall = RecallSkill(store, counter)
        return recall, store, r1, r2

    # ── Tool Definitions ──

    def test_tool_definitions(self):
        store = InMemoryScopeStore()
        recall = RecallSkill(store)
        tools = recall.get_tool_definitions()
        names = {t["name"] for t in tools}
        assert names == {"memory_expand", "memory_search"}

    def test_memory_expand_has_id_param(self):
        """memory_expand should have a single 'id' parameter (no 'scope_id' or 'level')."""
        store = InMemoryScopeStore()
        recall = RecallSkill(store)
        tools = recall.get_tool_definitions()
        expand = next(t for t in tools if t["name"] == "memory_expand")
        params = expand["parameters"]["properties"]
        assert "id" in params
        assert "scope_id" not in params
        assert "level" not in params

    # ── Root listing (empty id) ──

    def test_expand_root_lists_scopes(self):
        recall, _, r1, r2 = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {})
        assert "Available Scopes" in result
        assert r1.name in result
        assert r2.name in result
        # Root listing should contain scope IDs for drilling
        assert r1.id in result
        assert r2.id in result

    def test_expand_root_empty_store(self):
        recall = RecallSkill(InMemoryScopeStore(), CharTokenCounter())
        result = recall.execute_tool("memory_expand", {"id": ""})
        assert "No past scopes" in result

    # ── Scope overview (id = scope_id) ──

    def test_expand_overview(self):
        """Expanding a scope ID shows summary + child node IDs."""
        recall, _, r1, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": r1.id})
        assert "implement-auth" in result
        assert "JWT" in result
        # Should expose child node IDs
        assert f"{r1.id}.meta" in result
        assert f"{r1.id}.files" in result
        assert f"{r1.id}.messages" in result

    def test_expand_overview_no_raw_messages(self):
        """Scope without raw_messages should not expose .messages child."""
        recall, _, _, r2 = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": r2.id})
        assert r2.name in result
        assert f"{r2.id}.messages" not in result
        assert f"{r2.id}.files" in result

    # ── Meta expansion (id = scope_id.meta) ──

    def test_expand_meta(self):
        recall, _, r1, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": f"{r1.id}.meta"})
        assert "Metadata" in result
        assert "JWT" in result  # decision content
        assert "write_file" in result  # tools used

    def test_expand_meta_with_errors(self):
        recall, _, _, r2 = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": f"{r2.id}.meta"})
        assert "segfault" in result
        assert "⚠️" in result

    # ── Files expansion (id = scope_id.files) ──

    def test_expand_files(self):
        recall, _, r1, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": f"{r1.id}.files"})
        assert "auth.py" in result
        assert "middleware.py" in result

    # ── Messages expansion (id = scope_id.messages) ──

    def test_expand_messages(self):
        recall, _, r1, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": f"{r1.id}.messages"})
        assert "Messages" in result
        assert "ASSISTANT" in result
        # Should expose per-message IDs
        assert f"{r1.id}.msg.0" in result
        assert f"{r1.id}.msg.1" in result
        assert f"{r1.id}.msg.2" in result

    # ── Single message (id = scope_id.msg.N) ──

    def test_expand_single_message(self):
        recall, _, r1, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": f"{r1.id}.msg.0"})
        assert "I'll implement JWT auth." in result
        assert "ASSISTANT" in result

    def test_expand_single_message_with_tool(self):
        recall, _, r1, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": f"{r1.id}.msg.1"})
        assert "Created auth.py" in result
        assert "write_file" in result

    def test_expand_single_message_navigation(self):
        """Single message should show prev/next navigation hints."""
        recall, _, r1, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": f"{r1.id}.msg.1"})
        # msg.1 should have both prev and next
        assert f"{r1.id}.msg.0" in result  # prev
        assert f"{r1.id}.msg.2" in result  # next

    def test_expand_single_message_out_of_range(self):
        recall, _, r1, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": f"{r1.id}.msg.99"})
        assert "out of range" in result

    # ── Not found ──

    def test_expand_not_found(self):
        recall, _, _, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": "nonexistent"})
        assert "not found" in result.lower()

    def test_expand_not_found_child(self):
        recall, _, _, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_expand", {"id": "nonexistent.meta"})
        assert "not found" in result.lower()

    # ── Stateless: same call, same result ──

    def test_stateless_idempotent(self):
        """Same ID always returns the same result (no hidden state)."""
        recall, _, r1, _ = self._make_recall_with_data()
        result1 = recall.execute_tool("memory_expand", {"id": r1.id})
        result2 = recall.execute_tool("memory_expand", {"id": r1.id})
        assert result1 == result2  # Exactly the same — no state advancement

    # ── Search ──

    def test_search(self):
        recall, _, _, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_search", {"query": "JWT"})
        assert "implement-auth" in result
        assert "auth.py" in result

    def test_search_no_results(self):
        recall, _, _, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_search", {"query": "xyznonexistent"})
        assert "No scopes matched" in result

    def test_search_within_scope(self):
        recall, _, r1, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_search", {
            "query": "JWT",
            "scope_id": r1.id,
        })
        assert "Search Results" in result

    def test_search_empty_query(self):
        recall, _, _, _ = self._make_recall_with_data()
        result = recall.execute_tool("memory_search", {"query": ""})
        assert "provide a search query" in result.lower()

    # ── Router integration ──

    def test_recall_via_router(self):
        """Test recall tools via the full engine router."""
        store = InMemoryScopeStore()
        rec = ScopeRecord(
            name="test-scope",
            state=ScopeState.COMPACTED,
            summary="test summary",
        )
        rec.ended_at = rec.started_at + 10
        store.save(rec)

        engine = ContextEngine(config=make_config(), store=store)
        # Empty id → directory listing, injected as SYSTEM message
        msgs = make_messages(3)
        result = engine.router.dispatch("memory_expand", {}, msgs)
        assert result.success
        # Content is the router acknowledgement
        assert "root" in result.content.lower()
        # The actual expand content is in the injected SYSTEM message
        injected = [m for m in result.messages if m.metadata.get("memory_expansion")]
        assert len(injected) == 1
        assert "test-scope" in injected[0].content

    def test_recall_via_router_with_id(self):
        """Test expanding a specific scope via router."""
        store = InMemoryScopeStore()
        rec = ScopeRecord(
            name="test-scope",
            state=ScopeState.COMPACTED,
            summary="test summary",
            files_changed=["foo.py"],
        )
        rec.ended_at = rec.started_at + 10
        store.save(rec)

        engine = ContextEngine(config=make_config(), store=store)
        msgs = make_messages(3)
        result = engine.router.dispatch(
            "memory_expand", {"id": rec.id}, msgs,
        )
        assert result.success
        injected = [m for m in result.messages if m.metadata.get("memory_expansion")]
        assert len(injected) == 1
        assert "test-scope" in injected[0].content
        assert f"{rec.id}.files" in injected[0].content

    # ── Prompt ──

    def test_build_prompt(self):
        store = InMemoryScopeStore()
        recall = RecallSkill(store)
        prompt = recall.build_prompt("what did I do?")
        assert "Recall Mode" in prompt
        assert "what did I do?" in prompt
        assert "memory_expand" in prompt

    def test_unknown_tool(self):
        recall, _, _, _ = self._make_recall_with_data()
        result = recall.execute_tool("unknown_tool", {})
        assert "Unknown" in result


# ═════════════════════════════════════════════
# Test: HookRegistry
# ═════════════════════════════════════════════

class TestHookRegistry:
    def test_pre_hook_modifies_messages(self):
        registry = HookRegistry()

        def add_msg(scope, messages):
            return messages + [
                Message(role=MessageRole.SYSTEM, content="Hook injected!")
            ]

        registry.register_pre("test-hook", add_msg)
        scope = ScopeRecord(name="test")
        msgs = make_messages(3)
        result = registry.run_pre_hooks(scope, msgs)
        assert len(result) == len(msgs) + 1
        assert result[-1].content == "Hook injected!"

    def test_post_hook_observes(self):
        registry = HookRegistry()
        observed = []

        def observer(scope, messages):
            observed.append(len(messages))

        registry.register_post("observer", observer)
        registry.run_post_hooks(ScopeRecord(name="test"), make_messages(5))
        assert observed == [5]

    def test_priority_ordering(self):
        registry = HookRegistry()
        order = []

        def fn_a(scope, messages):
            order.append("a")
            return messages

        def fn_b(scope, messages):
            order.append("b")
            return messages

        registry.register_pre("b", fn_b, priority=200)
        registry.register_pre("a", fn_a, priority=10)
        registry.run_pre_hooks(ScopeRecord(name="test"), [])
        assert order == ["a", "b"]  # lower priority runs first

    def test_hook_failure_doesnt_crash(self):
        registry = HookRegistry()

        def failing_hook(scope, messages):
            raise ValueError("boom")

        registry.register_post("fail", failing_hook)
        # Should not raise
        registry.run_post_hooks(ScopeRecord(name="test"), [])

    def test_unregister(self):
        registry = HookRegistry()
        registry.register_pre("a", lambda s, m: m)
        registry.register_post("a", lambda s, m: None)
        assert registry.pre_hook_count == 1
        assert registry.post_hook_count == 1

        registry.unregister("a")
        assert registry.pre_hook_count == 0
        assert registry.post_hook_count == 0

    def test_clear(self):
        registry = HookRegistry()
        registry.register_pre("a", lambda s, m: m)
        registry.register_post("b", lambda s, m: None)
        registry.clear()
        assert registry.pre_hook_count == 0
        assert registry.post_hook_count == 0

    def test_hooks_via_engine(self):
        """Test hooks accessible via engine.hooks."""
        engine = make_engine()
        observed = []

        def observer(scope, messages):
            observed.append(scope.name)

        engine.hooks.register_post("test", observer)
        assert engine.hooks.post_hook_count == 1


# ═════════════════════════════════════════════
# Test: Nested scopes via router (multi-level)
# ═════════════════════════════════════════════

class TestNestedScopesViaRouter:
    def test_nested_begin_end_lifo(self):
        """Nested skills must be closed in LIFO order."""
        engine = make_engine()
        msgs = make_messages(3)

        # Open outer
        r1 = engine.router.dispatch(
            "skill_begin", {"skill_name": "meta"}, msgs,
        )
        msgs = r1.messages

        # Open inner
        r2 = engine.router.dispatch(
            "skill_begin", {"skill_name": "code-review"}, msgs,
        )
        msgs = r2.messages
        assert engine.stack.depth == 2

        # Add work
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Inner work."),
        ]

        # Close inner first
        r3 = engine.router.dispatch(
            "skill_end", {"report": "Inner review complete."}, msgs,
        )
        assert r3.success
        msgs = r3.messages
        assert engine.stack.depth == 1

        # Now close outer
        msgs = msgs + [
            Message(role=MessageRole.ASSISTANT, content="Outer done."),
        ]
        r4 = engine.router.dispatch(
            "skill_end", {"report": "Outer scope complete."}, msgs,
        )
        assert r4.success
        assert engine.stack.is_empty

    def test_close_outer_without_inner_fails(self):
        """Closing outer scope while inner is open should fail."""
        engine = make_engine()
        msgs = make_messages(3)

        r1 = engine.router.dispatch(
            "skill_begin", {"skill_name": "outer"}, msgs,
        )
        outer_scope_id = json.loads(r1.content)["scope_id"]
        msgs = r1.messages

        r2 = engine.router.dispatch(
            "skill_begin", {"skill_name": "inner"}, msgs,
        )
        msgs = r2.messages

        # Try to close outer (should fail — inner is on top)
        r3 = engine.router.dispatch(
            "skill_end",
            {"report": "outer done", "scope_id": outer_scope_id},
            msgs,
        )
        assert not r3.success
        data = json.loads(r3.content)
        assert "LIFO" in data.get("error", "") or "top of stack" in data.get("error", "")


# ═════════════════════════════════════════════
# Test: Report Validator via Router
# ═════════════════════════════════════════════

class TestReportValidatorViaRouter:
    def test_rejected_report_via_router(self):
        class MinLengthValidator:
            def validate(self, report, scope):
                if len(report) < 20:
                    return "Report too short (minimum 20 chars)"
                return None

        engine = ContextEngine(
            config=make_config(),
            report_validator=MinLengthValidator(),
        )
        msgs = make_messages(5)

        r1 = engine.router.dispatch(
            "skill_begin", {"skill_name": "test"}, msgs,
        )
        msgs = r1.messages + [
            Message(role=MessageRole.ASSISTANT, content="Done."),
        ]

        # Short report → rejected
        r2 = engine.router.dispatch(
            "skill_end", {"report": "OK"}, msgs,
        )
        assert not r2.success
        data = json.loads(r2.content)
        assert "rejected" in data.get("error", "").lower()
        # Stack should NOT be popped
        assert engine.stack.depth == 1

        # Retry with good report
        r3 = engine.router.dispatch(
            "skill_end",
            {"report": "Completed code review, found 3 issues and fixed all of them."},
            msgs,
        )
        assert r3.success
        assert engine.stack.is_empty


# ═════════════════════════════════════════════
# Test: Engine Integration (combined M1+M2)
# ═════════════════════════════════════════════

class TestEngineM2Integration:
    def test_engine_has_router_recall_hooks(self):
        engine = make_engine()
        assert engine.router is not None
        assert engine.recall is not None
        assert engine.hooks is not None

    def test_close_clears_all(self):
        engine = make_engine()
        msgs = make_messages(3)
        engine.router.dispatch("skill_begin", {"skill_name": "a"}, msgs)
        assert engine.stack.depth == 1

        engine.close()
        assert engine.is_closed

        # Router catches RuntimeError and returns failure ToolResult
        r = engine.router.dispatch("skill_begin", {"skill_name": "b"}, msgs)
        assert not r.success
        data = json.loads(r.content)
        assert "closed" in data["error"].lower()

    def test_engine_tool_names_constant(self):
        """ENGINE_TOOL_NAMES should include all 4 engine tools."""
        assert ENGINE_TOOL_NAMES == {
            "skill_begin", "skill_end",
            "memory_expand", "memory_search",
        }
