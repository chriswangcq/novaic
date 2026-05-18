# Result: P431 / T419 archive/direct diagnostics inventory

## Summary

Inventoried Cortex archive/direct diagnostic paths. The main live surfaces are `ScopeEndRequest` and `/v1/scope/end` in `api.py`, workspace archive projection helpers in `workspace.py`, wake archive event writing in `context_event_writer.py`, and tests around scope-end/finalize behavior.

## Live Source Classification

| Surface | Files / Functions | Classification |
|---|---|---|
| Direct scope-end request contract | `api.py::ScopeEndRequest` | Live API contract; validates archive diagnostics when any diagnostic field is supplied |
| Direct scope-end handler | `api.py::scope_end` | Live API; archives root/child scopes, appends wake archive event, finalizes active stack for wake/root |
| Wake archive event writer | `context_event_writer.py::wake_archived` | Live event writer; persists reason, remaining stack, optional archive diagnostics |
| Active stack finalize projection | `active_stack_projection.py`, `_finalize_active_stack_for_archive` | Live operational projection |
| Archive projection helpers | `workspace.py::_build_archive_scope_index_projection`, `archive_root_scope_projection`, child completion | Live archive/debug projection |
| Scope transition history | `scope_transition_events.py`, `/v1/scope/history` | Live diagnostic/history endpoint |

## Test Coverage Classification

- `tests/test_context_event_api_lifecycle.py`: direct scope-end event/diagnostics validation.
- `tests/test_context_event_api_skill_lifecycle.py`: root/wake finalize and retry behavior.
- `tests/test_context_event_read_source_guards.py`: guards active stack projection usage.
- `tests/test_scope_state.py`: state transition/archive invariants.
- `tests/test_pr67_wake_child_api.py`: wake child scope archive behavior.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p431/archive-direct-inventory-rg.txt`
- `.complex-problems/L20260516-222011/tmp/p431/api-scope-end-request-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p431/api-scope-end-handler-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p431/workspace-archive-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p431/context-wake-archived-slice.txt`

## Downstream Targets

- P432 should verify/fix direct scope-end diagnostics and finalize ownership.
- P433 should verify/fix archive projection/readback behavior.
