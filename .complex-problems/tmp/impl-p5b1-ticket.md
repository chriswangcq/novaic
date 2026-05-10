# Cut Scope Lookup And Uniqueness To SQLite

## Problem Definition

`skill_begin` and some lookup helpers still use workspace-file projections for scope identity decisions: root `meta.scope_ids` is a file-backed uniqueness index, and `_walk_scope_tree` is used to cross-check duplicate child scope ids and locate nested scope paths. This violates the Phase 5 goal that live authority decisions use SQLite projections rather than local file walking.

## Proposed Solution

- Add operational-store read/list helpers for `scope_projection` so callers can check scope-id existence and lookup scope paths by SQLite state.
- Ensure root, wake, and child scope creation/close paths write `scope_projection` rows with root id, scope id, parent scope id, phase, depth, generation, skill/name/task, and timestamps.
- Replace `skill_begin` duplicate-scope check with SQLite projection lookup.
- Replace `_resolve_scope_path_for_lookup` tree walking with SQLite projection lookup for scope ids.
- Remove root `meta.scope_ids` helper methods and related warning/fallback comments.
- Update tests to verify duplicate rejection/lookup through SQLite projection and absence of old file-walk authority in live sections.

## Acceptance Criteria

- `skill_begin` duplicate rejection works without `get_scope_id_index`, `register_scope_id`, or `_walk_scope_tree`.
- Lookup by nested scope id works through `scope_projection` state.
- Existing lifecycle and active-stack tests pass.
- Static audit shows no `_walk_scope_tree` call from `skill_begin` or `_resolve_scope_path_for_lookup`.

## Verification Plan

- Run targeted tests:
  - `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
  - `novaic-cortex/tests/test_context_event_api_steps_write.py`
  - `novaic-cortex/tests/test_active_stack_projection.py`
  - `novaic-cortex/tests/test_operational_store.py`
  - `novaic-cortex/tests/test_context_event_read_source_guards.py`
- Run static `rg` for `_walk_scope_tree`, `scope_ids`, `register_scope_id`, and `get_scope_id_index`.
- Run `python3 -m py_compile` for modified Cortex modules.

## Risks

- Missing projection writes could make old scopes invisible to lookup.
- Idempotent create paths must keep projection writes deterministic.
- Archive paths may still need file projection behavior, but that belongs to P050, not this ticket.

## Assumptions

- No migration of old pre-projection data is required.
- Existing tests can create fresh workspaces and assert the new projection behavior.
