# Active Path Routing Endpoint Cutover Success Check

## Summary

P038 is solved. R032 cuts active write routing from filesystem active-path walking to SQLite active-stack projection for both assistant message writes and tool step writes.

## Evidence

- `scope_write_assistant` now reads `read_active_stack_projection(...).active_scope_path`.
- `steps_write` now reads `read_active_stack_projection(...).active_scope_path`.
- `Workspace.write_assistant(...)` exists and is covered by endpoint tests.
- Reopened Workspace tests prove routing works from persisted operational SQLite.
- Static audit shows no `resolve_active_scope_path(...)` references remain in `api.py`.
- Targeted tests passed: 9 tests.
- Full Cortex suite passed: 461 tests.

## Criteria Map

- `scope_write_assistant` contains no `resolve_active_scope_path(...)` call and writes to projection active path: satisfied.
- `steps_write` contains no `resolve_active_scope_path(...)` call and writes to projection active path: satisfied.
- Root/wake and nested child routing write to expected scope path: satisfied by steps tests.
- Tests prove routing works after Workspace/registry reconstruction from operational SQLite: satisfied.

## Execution Map

- T035 was classified `one_go`.
- R032 records implementation and verification.
- No follow-up is required for P038.

## Stress Test

- Monkeypatch tests make `resolve_active_scope_path(...)` fail if called by routing endpoints.
- Static guard catches both code and stale-docstring residue in endpoint sections.
- Full suite covers interaction with context events, blob payload externalization, step indices, and assistant message materialization.

## Residual Risk

- Direct non-wake child `scope_create` no longer acts as active-stack routing authority; intended live child lifecycle is `context_skill_begin`.
- Remaining stack file-walk residue is wake creation seeding and helper deletion, owned by P039.

## Result IDs

- R032
