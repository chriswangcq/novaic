# Child Problem: Session Finalize Diagnostics Binding

## Problem

Queue session finalized/rejected events and session state updates must bind finalize diagnostics to explicit scope/generation, not to stale active lookup after the generation changes.

## Success Criteria

- Verify or fix `queue_service/session_repo.py`, `queue_service/session_fsm.py`, and `queue_service/session_ledger.py` so `finalize_reason`, `remaining_stack`, and ended metadata are recorded only after explicit scope/generation decision.
- Add or update tests proving stale finalize does not record a newer wake's remaining stack.
- Add or update tests proving valid finalize records the intended reason and stack.
