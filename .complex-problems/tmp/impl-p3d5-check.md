# File-Walk Helper Deletion And Guard Rails Success Check

## Summary

P039 is solved. R033 physically deletes the file-walk active-stack helper from `api.py`, removes all `resolve_active_scope_path` API references, and adds whole-file guards to prevent reintroduction.

## Evidence

- `api.py` no longer defines or calls `_collect_active_stack`.
- `api.py` no longer references `resolve_active_scope_path`.
- Wake creation projection seeding now builds explicit deterministic wake frames.
- Static guard asserts both old symbols are absent from `api.py`.
- Targeted tests passed: 42 tests.
- Full Cortex suite passed: 462 tests.

## Criteria Map

- `api.py` has no `_collect_active_stack(...)` function or call sites: satisfied.
- `api.py` has no `resolve_active_scope_path(...)` references: satisfied.
- Root creation still projects an empty active stack: satisfied by lifecycle/status tests.
- Wake creation and idempotent wake creation project the wake frame into SQLite active-stack state: satisfied by updated wake idempotency test.
- Static guards fail if file-walk active-stack authority is reintroduced: satisfied by whole-file guard.
- Targeted tests and full Cortex test suite pass: satisfied.

## Execution Map

- T036 was classified `one_go`.
- R033 records implementation and verification.
- No follow-up is required for P039.

## Stress Test

- Whole-file static guard is stricter than section guards and catches helper redefinition, call-site reintroduction, and stale docstring residue.
- Full suite confirms the deterministic wake frame does not regress status, lifecycle, context event, assistant write, tool step, or projection behavior.

## Residual Risk

- Lower-level `Workspace.resolve_active_scope_path(...)` can remain as non-API legacy/repair utility; this problem only targeted live Cortex API stack authority.
- Further parent-level P020 and Phase 3E checks should verify the aggregate state across all child results.

## Result IDs

- R033
