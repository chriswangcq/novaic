# normalize_step contract audit result

## Summary

`normalize_step` is already the enforced boundary for new tool-step writes, and the missing-observation criterion needed an explicit regression test. I added that test so both unsafe legacy inline `result` and absent/non-dict `observation` are covered.

## Done

- Mapped `normalize_step` at `novaic-cortex/novaic_cortex/workspace.py:700-736`.
- Verified inline tool `result` is rejected at `workspace.py:715-716`.
- Verified missing/non-dict tool `observation` is rejected at `workspace.py:717-718`.
- Added `test_write_step_rejects_missing_tool_observation` in `novaic-cortex/tests/test_step_index_outcome.py`.

## Verification

- Ran `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_step_index_outcome.py`.
- Result: `20 passed in 0.16s`.

## Known Gaps

- This result only covers `normalize_step` and the `write_step` normalization entry point. Payload mirroring, index metadata, and active projection call sites remain under sibling P146-P148.

## Artifacts

- Modified `novaic-cortex/tests/test_step_index_outcome.py`.
