# Phase 3C1 SQLite Active Stack Read Adapter Result

## Summary

Implemented the SQLite active-stack read adapter. It reads operational projection rows through explicit inputs, returns response-compatible top-first frames and stack depth, resolves the current active scope path from the top frame, and fails loudly for non-empty projections missing `scope_path`.

## Done

- Added `read_active_stack_projection` to `novaic-cortex/novaic_cortex/active_stack_projection.py`.
- Empty/missing projection returns root active path, empty frames, depth 0, and generation 0.
- Non-empty projection requires top frame `scope_path` and returns it as `active_scope_path`.
- Added focused tests for empty, non-empty, malformed, and missing-input cases.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_operational_store.py`
  - Passed: 19 tests.
- `python3 -m py_compile novaic-cortex/novaic_cortex/active_stack_projection.py novaic-cortex/tests/test_active_stack_projection.py`
  - Passed.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 450 tests.

## Known Gaps

- Adapter is not wired into live endpoints yet; P031/P032/P033 own status, begin, and end cutover.

## Artifacts

- `novaic-cortex/novaic_cortex/active_stack_projection.py`
- `novaic-cortex/tests/test_active_stack_projection.py`
