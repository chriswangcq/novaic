# PR-194D — Business/Device Schema Push Fail-Fast

Status: `[implemented]`

## Current-State Analysis

Business and Device schema push code currently logs schema registration errors
but does not fail startup. This allows "service appears healthy but Entangled
schema is incomplete".

## Small Tickets

- [x] Make Business schema push raise on HTTP failure, response `errors`, or
      registration count mismatch.
- [x] Make Device schema push raise on HTTP failure, response `errors`, or
      registration count mismatch.
- [x] Ensure Business schema proxy preserves Entangled non-2xx failures.
- [x] Add unit tests for fail-fast behavior.

## Validation

- Business schema push tests: covered by the 155-test Business suite.
- Device schema push tests: covered by the 8-test Device suite.
