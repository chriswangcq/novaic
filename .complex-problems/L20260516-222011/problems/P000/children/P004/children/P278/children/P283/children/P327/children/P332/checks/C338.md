# Check: Runtime attach handler generation enforcement audit

## Summary

Success. The one-go audit maps the runtime fail-closed boundary and adds the missing expected-scope test. Runtime attach now has focused coverage for missing expected scope, missing expected generation, stale scope, stale generation, and happy-path append/claim.

## Evidence

- R317 maps `handle_session_attach_input(...)` validation order and current root meta checks.
- Handler rejects missing `expected_wake_scope_id` and missing `expected_session_generation` before reading/writing Cortex.
- Handler rejects stale `current_wake_scope_id` and stale `current_session_generation` before `append_scope_input(...)` or notification claim.
- Focused runtime tests passed: `18 passed`.

## Criteria Map

- Runtime current wake/scope/generation source mapped: satisfied by R317.
- Missing expected wake scope and generation rejected: satisfied by new and existing tests.
- Stale wake scope and stale generation rejected before mutation: satisfied by existing tests with `append_scope_input.assert_not_called()`.
- Focused tests prove enforcement: satisfied by R317 verification.

## Execution Map

- T322 executed one bounded runtime-handler audit.
- Added one missing expected wake scope test.

## Stress Test

- Bad payload with generation but no expected wake scope now fails before reading root meta or appending input.
- Stale root meta scope/generation fail before context mutation.

## Residual Risk

- Non-blocking: P333 remains for aggregate end-to-end regression coverage across all attach layers.

## Result IDs

- R317
