# Finalize pending restart atomicity fix

## Problem

When `session_ended(...)` accepts finalize and finds pending input, it currently clears active session state to `no_active` in one transaction, then records restart intent/state in a later transaction. A concurrent dispatch can observe `no_active` in the gap and start a competing wake.

## Success Criteria

- Accepted finalize with pending input durably records the restart transition/state without exposing an intermediate externally dispatchable `no_active` gap.
- Durable outbox creation remains required for restart wake creation.
- Generation and pending input consumption semantics remain correct.
- Focused tests cover the race shape or at least assert the restart transition is recorded atomically with finalize decision.
