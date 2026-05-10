# Phase 3B2 Follow-up Nested And Restart Projection Result

## Summary

Closed the P023 verification gap by adding focused nested API lifecycle coverage and a restart-like operational-store persistence test. The stricter evidence now proves both nested begin/end active-stack projection behavior and SQLite projection readability through a fresh store instance.

## Done

- Added `test_nested_skill_begin_end_updates_sqlite_active_stack_top_first` to `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`.
- The nested lifecycle test opens `skill-1`, opens `skill-2` under it, verifies top-first frames `skill-2 -> skill-1 -> wake-1`, closes `skill-2`, and verifies the projected stack pops to `skill-1 -> wake-1`.
- Added `test_active_stack_projection_survives_store_reopen` to `novaic-cortex/tests/test_operational_store.py`.
- The restart-like store test writes an active stack, constructs a fresh `OperationalSqliteStore` for the same SQLite path, and verifies the persisted projection exactly.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_operational_store.py`
  - Passed: 12 tests.
- `python3 -m py_compile novaic-cortex/tests/test_context_event_api_skill_lifecycle.py novaic-cortex/tests/test_operational_store.py`
  - Passed.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 440 tests.

## Known Gaps

- None for this follow-up. P019/P020 still own the separate read-cutover and file-walk quarantine work.

## Artifacts

- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_operational_store.py`
