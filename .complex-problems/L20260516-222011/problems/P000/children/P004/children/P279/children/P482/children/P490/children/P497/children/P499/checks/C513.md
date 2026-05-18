# Attach builder strictness implementation check

## Summary

Success for P499. The one-go implementation is small, directly scoped to `build_attach_input_effect()`, and has focused tests plus guard evidence proving the optional generation builder contract was removed.

## Evidence

- R484 records the code change and test evidence.
- `novaic-agent-runtime/queue_service/session_effects.py` now validates `expected_session_generation` through `require_positive_session_generation_value()`.
- `novaic-agent-runtime/tests/test_pr267_session_outbox_effect_boundary.py` now covers invalid builder inputs and a valid normalized payload.
- `.complex-problems/L20260516-222011/tmp/p499/attach-builder-strictness-tests.log` shows `28 passed`.
- `rg` guard output confirms no remaining `expected_session_generation: int | None` or `expected_session_generation=None` hits in the checked runtime/test scope.

## Criteria Map

- `build_attach_input_effect()` requires and validates a positive explicit `expected_session_generation`: satisfied by the new helper call before payload construction.
- Builder reuses the existing session generation contract helper: satisfied by importing `require_positive_session_generation_value()`.
- Focused tests prove missing, bool, zero, and invalid generation values are rejected: satisfied by the new parametrized invalid-generation test.
- Valid attach effects keep the existing payload shape: satisfied by the existing shape test plus the new valid normalization test.

## Execution Map

- T490 was classified one_go because the change touched one builder and one focused test file.
- R484 records the bounded implementation, test run, guard checks, and the remaining P500 verification gap.

## Stress Test

- Plausible failure mode: caller accidentally passes `None` or a stale non-positive value and the builder emits a malformed attach effect that later layers may mishandle.
- The new builder-level helper rejects those values before any effect is returned, so the malformed effect cannot be constructed through this boundary.

## Residual Risk

- This does not by itself prove all attach-race behavior still works; that independent regression proof is intentionally left to P500.
- The helper accepts numeric strings and normalizes them, matching the existing canonical helper behavior; this is acceptable for this boundary because the emitted payload is a positive integer.

## Result IDs

- R484
