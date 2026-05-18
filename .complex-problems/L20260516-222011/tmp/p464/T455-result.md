# T455 Result: Remove observed wake outbox residue

## Summary

Removed the obsolete production `OBSERVE_CREATE_WAKE_SAGA` constant from `SessionOutboxDispatcher` and updated negative guard tests to use a test-local obsolete effect string. Focused observed-wake/wake-creation tests passed.

## Changes

- `novaic-agent-runtime/queue_service/session_outbox.py`
  - Removed `OBSERVE_CREATE_WAKE_SAGA = "observe_create_wake_saga"`.
- `novaic-agent-runtime/tests/test_pr249_observed_wake_outbox_cleanup.py`
  - Added test-local `OLD_OBSERVE_CREATE_WAKE_SAGA_EFFECT`.
  - Updated negative assertions to use the test-local constant.
- `novaic-agent-runtime/tests/test_pr250_observed_wake_effect_rename.py`
  - Added test-local `OLD_OBSERVE_CREATE_WAKE_SAGA_EFFECT`.
  - Updated negative assertions to use the test-local constant.
- `novaic-agent-runtime/tests/test_pr251_wake_creation_outbox_cutover.py`
  - Added test-local `OLD_OBSERVE_CREATE_WAKE_SAGA_EFFECT`.
  - Updated negative assertion to use the test-local constant.

## Evidence

- After-cleanup guard: `.complex-problems/L20260516-222011/tmp/p464/observe-wake-after.txt`
- Focused test log: `.complex-problems/L20260516-222011/tmp/p464/observe-wake-focused-tests.log`
- Focused test exit: `.complex-problems/L20260516-222011/tmp/p464/observe-wake-focused-tests.exit` = `0`
- Pytest summary: `13 passed in 0.18s`

## Classification After Cleanup

- Production hits for `OBSERVE_CREATE_WAKE_SAGA` / `observe_create_wake_saga`: none in `novaic-agent-runtime/queue_service`.
- Remaining hits are test-local negative guards in three test files.

## Residual Risk

None for P464. P462 can now be rechecked after this follow-up closes.
