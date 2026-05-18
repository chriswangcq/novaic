# Ticket: Session Finalize Diagnostics Binding

## Problem Definition

Queue session finalized/rejected events and restart/closed transition metadata must bind `finalize_reason`, `remaining_stack`, and `finalize_generation` to the explicit scope/generation decision.

## Proposed Solution

Audit and test `SessionRepository.session_ended`, `decide_session_finalize`, and `SessionLedgerRepository` finalize recorders. Add focused tests if stale finalize diagnostics can be recorded ambiguously.

## Acceptance Criteria

- Stale generation finalize is rejected and does not close or restart the active session.
- Stale finalize rejection payload records the stale finalize's reason/stack as rejected metadata, not as a valid close.
- Valid finalize records the intended reason, generation, scope, and remaining stack.
- Closed/restart transition metadata uses the same finalize metadata produced before mutation.

## Verification Plan

- Inspect existing `tests/test_pr254_finalize_ownership.py`.
- Add missing tests if needed.
- Run focused session finalize and pending restart tests.
- Search for direct `remaining_stack`/`finalize_reason` writes outside the explicit finalize metadata path.
