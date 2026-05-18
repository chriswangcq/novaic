# PR-288A — Wake Created Observed Handler

Status: Closed

## Goal

Move wake-created state activation and input consumption out of the outbox
publisher body into an observed-event handler.

## Scope

- Add `SessionObservedEventHandler`.
- Handle wake-created observation by recording active session and consuming
  input events.
- Keep race-loser cancellation behavior intact.
- Update residue tests so active-state ownership is no longer in
  `session_outbox.py`.

## Acceptance Criteria

- Wake-created observation activates state and consumes input.
- `session_outbox.py` no longer directly calls `record_active_session`.
- Existing wake creation outbox tests still pass.

## Verification

- `tests/test_pr288_session_observed_event_handler.py`
- Wake creation outbox tests.
- Residue guard tests.

## Closure Notes

- Added `queue_service/session_observed_events.py`.
- Moved active state recording and input consumption from
  `SessionOutboxDispatcher._publish_create_wake_saga` into
  `SessionObservedEventHandler.apply_wake_created`.
- Updated active-state residue guards.
- Verified with targeted observed/outbox/residue tests: 15 passed.
