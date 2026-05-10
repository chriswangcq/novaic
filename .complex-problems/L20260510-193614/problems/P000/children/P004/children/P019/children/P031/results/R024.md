# Phase 3C2 Context Status SQLite Stack Read Cutover Result

## Summary

Cut `context_status(include_usage=False)` to the SQLite active-stack read adapter. The default status path now reads operational projection frames, while `include_usage=True` remains backed by the semantic ContextEvent read model.

## Done

- Updated `context_status` default path to call `read_active_stack_projection`.
- Preserved default response fields: `stack_depth`, `current_skill`, `frames`, and zero usage counters.
- Added a test that monkeypatches `_collect_active_stack` to fail while default status succeeds from SQLite projection.
- Updated the read-source guard test so it now forbids `_collect_active_stack` in `context_status`.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_pr67_wake_child_api.py novaic-cortex/tests/test_active_stack_projection.py`
  - Passed: 19 tests.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_pr67_wake_child_api.py novaic-cortex/tests/test_context_event_read_source_guards.py novaic-cortex/tests/test_active_stack_projection.py`
  - Passed: 21 tests.
- `python3 -m py_compile novaic-cortex/novaic_cortex/api.py novaic-cortex/tests/test_pr67_wake_child_api.py novaic-cortex/tests/test_context_event_read_source_guards.py`
  - Passed.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 451 tests.

## Known Gaps

- `skill_begin` and `skill_end` still need read/LIFO cutover in P032/P033.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_pr67_wake_child_api.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
