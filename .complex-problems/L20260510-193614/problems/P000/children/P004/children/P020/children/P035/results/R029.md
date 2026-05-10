# Archive Finalize Stack Snapshot Cutover Result

## Summary

Completed P035/T032. `scope_end` root and child archive/finalize branches now derive active-stack frames from SQLite active-stack projection instead of `_collect_active_stack(...)`.

## Done

- Replaced root archive stack snapshot with `read_active_stack_projection(...)["frames"]`.
- Replaced child archive stack snapshot with `read_active_stack_projection(...)["frames"]`.
- Kept idempotent already-archived paths unchanged.
- Added monkeypatch tests proving root empty-stack archive, root wake-stack archive, and child wake archive do not call `_collect_active_stack(...)`.
- Added a static read-source guard asserting the `scope_end` section contains `read_active_stack_projection` and no `_collect_active_stack`.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_context_event_read_source_guards.py`
  - Passed: 25 tests.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 454 tests.
- Static audit:
  - `scope_end` now has `read_active_stack_projection(...)` in root/child archive paths.
  - `_collect_active_stack(...)` is absent from the `scope_end` section.

## Residual Risk

- File-walk stack collection still exists in other explicit P020 child scopes:
  - wake creation projection seeding;
  - `skill_begin` error/post-create paths;
  - `skill_end` exception diagnostics;
  - final helper deletion and guard rails.
- This result intentionally does not solve those later child problems.

## Changed Files

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
