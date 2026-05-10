# Phase 3C3 Skill Begin Parent Selection SQLite Cutover Result

## Summary

Cut successful `skill_begin` parent selection and depth-limit authority to SQLite active-stack projection. Empty projections attach under root, non-empty projections attach under the top frame `scope_path`, and a fresh Workspace/registry test proves persisted SQLite projection drives parent selection after process-local reconstruction.

## Done

- Updated `skill_begin` to call `read_active_stack_projection` for current stack frames and `active_scope_path`.
- Replaced successful-path `resolve_active_scope_path(root_path)` parent selection with SQLite adapter `active_scope_path`.
- Added fresh Workspace/registry test that monkeypatches `resolve_active_scope_path` to fail and proves `skill_begin` attaches under the SQLite top frame.
- Preserved response shape and projection writes.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_pr67_wake_child_api.py`
  - Passed: 28 tests.
- `python3 -m py_compile novaic-cortex/novaic_cortex/api.py novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
  - Passed.
- Static search showed `skill_begin` now reads `read_active_stack_projection` and uses `active_stack["active_scope_path"]`; remaining `resolve_active_scope_path` matches are outside P032.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 452 tests.

## Known Gaps

- `skill_end` LIFO validation still needs SQLite cutover in P033.
- Some error response branches still collect file-walk stack context and are scheduled for P020 quarantine.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
