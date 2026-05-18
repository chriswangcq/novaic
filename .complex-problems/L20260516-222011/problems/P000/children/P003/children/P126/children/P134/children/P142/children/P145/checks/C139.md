# normalize_step observation contract success check

## Summary

Success. The result closes `P145`: `normalize_step` now has both source evidence and regression coverage for rejecting unsafe tool-step shapes before they become durable step files.

## Evidence

- `normalize_step` is implemented at `novaic-cortex/novaic_cortex/workspace.py:700-736`.
- Inline tool `result` rejection is at `novaic-cortex/novaic_cortex/workspace.py:715-716`.
- Missing/non-dict observation rejection is at `novaic-cortex/novaic_cortex/workspace.py:717-718`.
- Existing inline-result test is at `novaic-cortex/tests/test_step_index_outcome.py:362-373`.
- Added missing/invalid observation test is at `novaic-cortex/tests/test_step_index_outcome.py:376-398`.
- Focused test run passed: `20 passed in 0.16s`.

## Criteria Map

- Source pointers map implementation and validation branches: satisfied by `workspace.py:700-736`.
- Inline `result` input rejected: satisfied by source branch and `test_write_step_rejects_inline_tool_result`.
- Missing/invalid observation rejected: satisfied by source branch and the new `test_write_step_rejects_missing_tool_observation`.
- Historical compatibility scope: no archived read behavior was changed; this child only asserts new write normalization through `write_step`.

## Execution Map

- Result `R125` inspected the source boundary, found missing test coverage, added a targeted regression test, and reran the focused test file.
- No runtime child was needed because the discovered gap was a small local test coverage gap in the same leaf problem.

## Stress Test

- The added test exercises two plausible bypasses: no `observation` at all and a non-dict `observation` value. Both must raise before writing a step file.
- The existing inline-result test exercises the historical raw-output bypass that previously could have put raw terminal output or base64 into step JSON.

## Residual Risk

- Non-blocking for `P145`: this does not prove payload mirroring, index metadata, or active API projection call sites. Those are explicitly covered by sibling problems `P146`, `P147`, and `P148`.

## Result IDs

- `R125`
