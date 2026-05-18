# Media-Like Shell Stdout Regression Check

## Summary

Successful. The new tests directly cover the media-like stdout failure mode with both runtime and Cortex projection assertions.

## Evidence

- `R046` added runtime and Cortex regression tests.
- Runtime shell test simulates large `/9j/` stdout and asserts bounded `tool-output.v1` terminal text.
- Cortex projection test simulates shell `tool-step-payload.v1` with raw media-like stdout and asserts no image/display projection.
- Focused tests passed: runtime `6 passed`, Cortex `15 passed`.

## Criteria Map

- Large `/9j/`-style base64 stdout simulated:
  - Satisfied by both new tests.
- Public shell observation bounded and marked truncated:
  - Satisfied by runtime test assertions on text length and `stdout_truncated`.
- Cortex projection does not create display files or image blocks:
  - Satisfied by Cortex test assertions on `display_files` and display perception content.
- Focused runtime and Cortex tests pass:
  - Satisfied by recorded pytest runs.

## Execution Map

- `T052` added focused regression coverage in runtime and Cortex.

## Stress Test

- The regression payload intentionally uses the `/9j/` JPEG base64 prefix that previously appeared in leaked screenshot output.

## Residual Risk

- Low. Shell can still print base64-like text because shell is a terminal, but the test pins the important contract: bounded text only, no media reclassification.

## Result IDs

- R046
