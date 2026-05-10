# Active Path Routing Endpoint Cutover Result

## Summary

Completed P038/T035. `scope_write_assistant` and `steps_write` now route live writes through SQLite active-stack projection instead of `resolve_active_scope_path(...)`. The previously untested `scope_write_assistant` endpoint now has a concrete Workspace projection method and test coverage.

## Done

- Replaced `scope_write_assistant` active path resolution with `read_active_stack_projection(...).active_scope_path`.
- Replaced `steps_write` active path resolution with `read_active_stack_projection(...).active_scope_path`.
- Added `Workspace.write_assistant(...)` to materialize assistant message steps and index rows.
- Updated nested `steps_write` test to use public `context_skill_begin` projection writes instead of direct non-wake `scope_create`.
- Added reopened Workspace/registry tests proving routing works from persisted operational SQLite.
- Added monkeypatch tests that fail if `resolve_active_scope_path(...)` is called by live write routing.
- Added static guard for active write routing sections.
- Removed stale `resolve_active_scope_path` mention from `steps_write` docstring.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_context_event_read_source_guards.py`
  - Passed: 9 tests.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 461 tests.
- Static audit:
  - No `resolve_active_scope_path(...)` references remain in `novaic-cortex/novaic_cortex/api.py`.
  - Active write routing sections use `read_active_stack_projection(...)`.

## Residual Risk

- Direct non-wake child creation through `scope_create` no longer establishes active routing authority for tool-step writes; tests were moved to `context_skill_begin`, which is the intended stack-authoritative lifecycle API.
- Remaining `_collect_active_stack(...)` call sites are wake creation projection seeding plus helper definition, owned by P039.

## Changed Files

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
