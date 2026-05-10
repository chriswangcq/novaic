# File-Walk Helper Deletion And Guard Rails Result

## Summary

Completed P039/T036. The file-walk active-stack helper was physically deleted from `api.py`; wake creation projection seeding now constructs deterministic wake frames directly, and static guards assert no `_collect_active_stack` or `resolve_active_scope_path` residue remains in `api.py`.

## Done

- Replaced idempotent wake `scope_create` projection seeding with a deterministic wake frame.
- Replaced new wake `scope_create` projection seeding with a deterministic wake frame.
- Added `_active_stack_frame(...)` helper for explicit projection frame construction.
- Reused `_active_stack_frame(...)` in `skill_begin` successful push path.
- Deleted `_collect_active_stack(...)` from `api.py`.
- Added a whole-file guard asserting `_collect_active_stack` and `resolve_active_scope_path` are absent from `api.py`.
- Strengthened wake creation idempotency test to assert the active-stack projection frame shape.
- Removed tests' dependency on monkeypatching the deleted helper.

## Verification

- Static audit:
  - `rg -n "_collect_active_stack|resolve_active_scope_path" novaic-cortex/novaic_cortex/api.py -S`
  - No matches.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_pr67_wake_child_api.py novaic-cortex/tests/test_context_event_read_source_guards.py novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_active_stack_projection.py`
  - Passed: 42 tests.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 462 tests.

## Residual Risk

- `Workspace.resolve_active_scope_path(...)` may still exist outside `api.py` as lower-level legacy/repair surface, but live Cortex API stack authority no longer calls it. P039 acceptance only required `api.py` live authority cleanup.
- Direct non-wake `scope_create` remains non-authoritative for active-stack routing; live child skill routing is established by `context_skill_begin`.

## Changed Files

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_pr67_wake_child_api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
