# Phase 3B3A Active Stack Finalize Helper Result

## Summary

Implemented the operational active-stack finalize helper. The helper appends an idempotent `active_stack_finalized` SQLite event containing the normalized remaining stack, top scope id, and explicit reason, then clears the active-stack projection with the same generation.

## Done

- Added `ACTIVE_STACK_FINALIZED` and `finalize_active_stack_projection` to `novaic-cortex/novaic_cortex/active_stack_projection.py`.
- Required explicit operational store, root scope id, frames, generation, reason, and idempotency key.
- Reused active-stack frame normalization so finalize payload shape matches projection shape.
- Added tests for empty-stack finalize idempotency, non-empty remaining-stack recording plus projection clearing, and explicit input validation.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_active_stack_projection.py novaic-cortex/tests/test_operational_store.py`
  - Passed: 15 tests.
- `python3 -m py_compile novaic-cortex/novaic_cortex/active_stack_projection.py novaic-cortex/tests/test_active_stack_projection.py`
  - Passed.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 443 tests.

## Known Gaps

- The helper is not wired into live archive/finalize paths yet; P028 owns that.
- Helper event append and projection clear are still two operational-store calls. P028/P029 should decide whether this needs a transactional store primitive before live cutover.

## Artifacts

- `novaic-cortex/novaic_cortex/active_stack_projection.py`
- `novaic-cortex/tests/test_active_stack_projection.py`
