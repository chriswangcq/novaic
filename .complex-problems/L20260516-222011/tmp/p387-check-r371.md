# P387 Cortex operational store generation validation check

## Summary

Success. The Cortex operational store no longer uses raw `int(generation)` in the targeted write boundaries, and focused tests prove invalid generations are rejected.

## Evidence

- `upsert_scope_projection` now validates through `_require_non_negative_generation`.
- `set_active_stack` now validates through `_require_non_negative_generation`.
- The cross-repo generation coercion guard returned no matches after the patch.
- Focused Cortex suite passed: 104 tests.

## Criteria Map

- No raw `int(generation)` remains in `operational_store.py`: satisfied.
- Focused operational store tests reject bool and negative generation: satisfied by `test_operational_store_rejects_invalid_generation_boundaries`.
- Existing Cortex context-event/projection tests pass: satisfied by the 104-test focused suite.

## Execution Map

- R371 records the code patch, focused test addition, compile check, test run, and guard result.

## Stress Test

- The test covers bool rejection at the event append/projection boundary and negative rejection at active stack persistence, including the tricky Python `bool`-is-`int` case.

## Residual Risk

- None for the targeted operational store raw generation coercions. Other textual guard hits are left for P388 guard matrix classification.

## Result IDs

- R371
