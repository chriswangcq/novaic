# P367: Child Problem: Session Finalize Diagnostics Binding

Status: done
Parent: P338
Root: P000
Source Ticket: T355 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P367
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P367/README.md
Ticket(s): T357

## Problem
Queue session finalized/rejected events and session state updates must bind finalize diagnostics to explicit scope/generation, not to stale active lookup after the generation changes.

## Success Criteria
- Verify or fix `queue_service/session_repo.py`, `queue_service/session_fsm.py`, and `queue_service/session_ledger.py` so `finalize_reason`, `remaining_stack`, and ended metadata are recorded only after explicit scope/generation decision.
- Add or update tests proving stale finalize does not record a newer wake's remaining stack.
- Add or update tests proving valid finalize records the intended reason and stack.

## Subproblems
- P370: Finalize Diagnostics Assertion Hardening

## Results
- R351

## Latest Check
C375

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P367/README.md
- Ticket T357: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P367/tickets/T357.md
- Result R351: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P367/results/R351.md
- Check C373: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P367/checks/C373.md
- Check C375: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P367/checks/C375.md

## Follow-ups
- P370: Finalize Diagnostics Assertion Hardening
