# P017 T015 Result - Active Stack Authority Audit

## Summary

Completed the Phase 3A audit. The current runtime control stack still uses file-walk authority in `api.py` and `workspace.py`; the semantic context stack is a separate context-event projection; operational SQLite already has an active-stack table but no runtime API path uses it as authority yet.

## Call-Site Map

- Runtime file-walk stack collector:
  - `novaic-cortex/novaic_cortex/api.py:855` `_collect_active_stack(ws, root_path)` walks `steps/_index.jsonl` plus child `meta.json`, returns top-first frames.
- Runtime control API reads/writes using `_collect_active_stack`:
  - `api.py:909-924` validation errors in `skill_begin` return file-walk stack.
  - `api.py:935-958` duplicate scope-id errors in `skill_begin` return file-walk stack.
  - `api.py:960-980` skill depth limit uses file-walk stack length.
  - `api.py:1010-1028` successful `skill_begin` returns file-walk stack.
  - `api.py:1031-1040` `skill_begin` exception response attempts file-walk stack.
  - `api.py:1058-1068` missing scope id in `skill_end` returns file-walk stack.
  - `api.py:1087-1103` LIFO mismatch in `skill_end` uses file-walk-derived active path/stack.
  - `api.py:1115-1131` successful `skill_end` returns file-walk stack.
  - `api.py:1133-1146` `skill_end` exception response attempts file-walk stack.
  - `api.py:1163-1174` default `context_status` reads file-walk stack.
- Runtime active-path routing using `Workspace.resolve_active_scope_path`:
  - `api.py:982` `skill_begin` chooses parent path from file-walk active path.
  - `api.py:1071` `skill_end` chooses active path/top id from file-walk active path.
  - `api.py:664` `scope_write_assistant` writes assistant messages to file-walk active path.
  - `api.py:1422` `steps_write` writes tool steps to file-walk active path.
  - `api.py:749`, `770`, `1299`, `1347` context/meta helper endpoints resolve by scope id/path and may walk scope tree when no explicit path is supplied.
  - `workspace.py:638-668` `resolve_active_scope_path` is the file-walk implementation over `read_step_index` and `meta.phase`.
- Structural archive/finalize path:
  - `api.py:432-452` `_append_wake_archived_event` writes `WakeArchived` with `remaining_stack=[]`.
  - `api.py:540-631` `scope_end` calls wake archived event and `archive_root_scope_projection`/`complete_child_scope_projection`.
  - `workspace.py:398-435` archive uses `_auto_close_open_children`, writes summaries, and moves the tree.
- Operational SQLite substrate:
  - `operational_store.py:344-387` has `set_active_stack` and `get_active_stack`, including `top_scope_id`, frames JSON, generation, and updated timestamp.
  - No runtime `api.py` path currently reads/writes `set_active_stack`/`get_active_stack`.
- Semantic context stack:
  - `context_event_writer.py:150-181` writes `SkillScopeOpened`/`SkillScopeClosed`.
  - `context_event_projection.py:101-165` projects semantic wake/skill stack from context events and enforces event-projection LIFO.
  - `context_event_read_model.py:112-130` returns semantic/LLM stack top-first for `include_usage=True`.
  - This stack is for LLM context semantics and usage rendering; it should not be conflated with operational control stack authority unless explicitly bridged.
- Test surfaces:
  - `test_context_event_read_source_guards.py` currently allows one default `context_status` `_collect_active_stack` call; Phase 3C/D must update this guard.
  - `test_pr67_wake_child_api.py`, `test_pr84_minimal_structure_invariants.py`, `test_pr234_control_stack.py`, and `test_context_event_api_skill_lifecycle.py` cover current begin/end/status behavior and are likely migration targets.

## Boundary Decisions

- Operational control stack authority should be SQLite `active_stack_projection`.
- Workspace scope tree files remain trace/projection artifacts and path materialization targets.
- Context event projection stack remains semantic LLM context state, not the primary operational LIFO authority.
- File-walk helpers may only remain under a repair/debug name after cutover.
- Phase 3C/D must include active-path routing users (`steps_write`, `scope_write_assistant`, and no-explicit-path context/meta endpoints), not only `skill_begin`, `skill_end`, and `context_status`.

## Verification

- Used `rg` and numbered source reads over `api.py`, `workspace.py`, `context_event_writer.py`, `context_event_projection.py`, `context_event_read_model.py`, `operational_store.py`, and stack-related tests.
- No production code was modified during this audit.

## Known Gaps

- The existing P019/P020 child problem bodies are broad enough to cover runtime read/quarantine, but their future tickets must explicitly include active-path routing endpoints discovered here.
- Finalize currently writes `remaining_stack=[]`; Phase 3B should decide whether root-finalize always clears stack or must record any remaining stack before archive.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/novaic_cortex/context_event_writer.py`
- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/novaic_cortex/context_event_read_model.py`
