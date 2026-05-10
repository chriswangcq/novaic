# Phase 5B1 Scope Lookup And Uniqueness SQLite Cutover Result

## Summary

Completed the scope lookup and uniqueness cutover from workspace-file authority to operational SQLite projection. `skill_begin` duplicate rejection now reads `scope_projection`; `_find_scope_path_by_id` resolves via `scope_projection`; root `meta.scope_ids` helper methods and filesystem-walk duplicate checks were removed.

## Done

- Added `scope_path` to `scope_projection` and bumped operational SQLite schema version to 3.
- Added scope projection schema migration for existing SQLite files missing `scope_path`.
- Added `OperationalSqliteStore.list_scope_projections(...)`.
- Added `parse_scope_projection_identity(...)` helper for deterministic root/scope/parent/depth derivation from logical scope paths.
- `Workspace.create_scope` now writes `scope_projection` rows when an operational store is present.
- `scope_state.transition` now updates `scope_projection` on non-noop scope transitions.
- `archive_root_scope` now updates projection paths to `/ro/scopes/...` after moving the archived tree.
- Removed `Workspace.register_scope_id(...)` and `Workspace.get_scope_id_index(...)`.
- Replaced `skill_begin` duplicate child scope-id rejection with `operational_store.get_scope_projection(...)`.
- Replaced `_find_scope_path_by_id` filesystem tree walk with `operational_store.get_scope_projection(...)` / `list_scope_projections(...)`.
- Added/updated tests asserting projection `scope_path`, duplicate rejection via projection, and static guards that `skill_begin` / lookup do not call `_walk_scope_tree`.

## Verification

- Targeted projection/lifecycle/API tests passed:
  - `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_operational_store.py novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_context_event_read_source_guards.py`
  - Result: 45 passed.
- Additional scope lifecycle/history/control tests passed:
  - `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_scope_state.py novaic-cortex/tests/test_scope_history_api.py novaic-cortex/tests/test_pr67_wake_child_api.py novaic-cortex/tests/test_pr234_control_stack.py`
  - Result: 31 passed.
- Compile check passed:
  - `python3 -m py_compile novaic-cortex/novaic_cortex/operational_store.py novaic-cortex/novaic_cortex/workspace.py novaic-cortex/novaic_cortex/api.py novaic-cortex/novaic_cortex/scope_state.py novaic-cortex/novaic_cortex/scope_transition_events.py`
- Static audit:
  - `register_scope_id`, `get_scope_id_index`, and `meta.scope_ids` are absent from live source/tests.
  - `_walk_scope_tree` no longer appears in `api.py`; remaining `_walk_scope_tree` usage is confined to `workspace.py` archive/tree projection behavior and will be handled by P050.

## Known Gaps

- `_walk_scope_tree` still exists in `workspace.py` for archive projection (`/ro/scopes/_index.jsonl`). P050 owns renaming/quarantining or removing that helper.
- Current docs still mention `_walk_scope_tree` as scope lifecycle behavior. P047 owns docs/comment cleanup.

## Artifacts

- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/scope_state.py`
- `novaic-cortex/novaic_cortex/scope_transition_events.py`
- `novaic-cortex/tests/test_operational_store.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
