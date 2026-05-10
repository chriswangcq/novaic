# Phase 3C4 Skill End LIFO SQLite Cutover Result

## Summary

Cut `skill_end` stack-empty, mismatch, and successful close authority to SQLite active-stack projection. Successful close uses the SQLite top frame path and updates the projection by removing the top frame.

## Done

- Updated `skill_end` to read `read_active_stack_projection` at entry.
- Empty-stack and mismatch responses now use SQLite projection frames/top id.
- Successful close uses SQLite `active_scope_path` instead of `resolve_active_scope_path`.
- Successful close writes the popped SQLite frame list back to projection.
- Added fresh Workspace/registry test that monkeypatches `resolve_active_scope_path` to fail while mismatch and successful close still work from SQLite.
- Updated an old control-stack test to create scopes through public lifecycle APIs so it writes SQLite projection.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_pr67_wake_child_api.py`
  - Passed: 29 tests.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_pr234_control_stack.py novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
  - Passed: 12 tests.
- `python3 -m py_compile novaic-cortex/novaic_cortex/api.py novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_pr234_control_stack.py`
  - Passed.
- Static search showed `_context_skill_end_locked` reads `read_active_stack_projection`; remaining file-walk matches are outside P033 or exception/future cleanup scope.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 453 tests.

## Known Gaps

- Some exception/failure diagnostic branches still collect file-walk stack context and remain P020 quarantine scope.
- P034 still needs the final static gate for P019.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_pr234_control_stack.py`
