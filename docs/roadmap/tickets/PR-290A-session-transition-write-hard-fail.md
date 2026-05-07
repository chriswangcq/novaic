# PR-290A — Session Transition Writes Hard Fail

Status: Closed

## Goal

Stop swallowing `record_transition` failures. Dispatch/finalize must not return
success if the durable transition ledger was not written.

## Scope

- Remove soft fallback from transition write helpers.
- Add failure-injection tests.
- Keep non-critical pending projection handling for later tickets.

## Dependencies

- Existing `SessionLedgerRepository.record_transition`.

## Acceptance Criteria

- `_record_session_transition_after_transaction` does not return `[]` on
  exception.
- `_record_session_transition_in_current_transaction` does not swallow
  exception.
- Dispatch raises when transition ledger write fails.

## Verification

- Targeted PR-290A test.

## Closure Notes

- Removed exception swallowing from
  `_record_session_transition_after_transaction`.
- Removed exception swallowing from
  `_record_session_transition_in_current_transaction`.
- Added failure-injection test ensuring dispatch raises when
  `record_transition` fails.
- Verified with targeted failure/input/attach/wake tests: 9 passed.
