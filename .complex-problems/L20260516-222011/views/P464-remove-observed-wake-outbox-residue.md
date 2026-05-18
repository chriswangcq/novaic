# P464: Remove observed wake outbox residue

Status: done
Parent: P462
Root: P000
Source Ticket: none (none)
Source Check: C475
Package: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P462/children/P464
Body: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P462/children/P464/README.md
Ticket(s): T455

## Problem
Production source still exposes `SessionOutboxDispatcher.OBSERVE_CREATE_WAKE_SAGA` even though observed wake-created is no longer a supported durable outbox effect.

## Success Criteria
- Remove `OBSERVE_CREATE_WAKE_SAGA` from production `SessionOutboxDispatcher`.
- Update negative guard tests to use the literal obsolete effect string or another test-local marker instead of importing a production constant.
- `rg "OBSERVE_CREATE_WAKE_SAGA|observe_create_wake_saga"` has no production source hits and only intentional test/documentation guard hits.
- Focused tests pass:
- `tests/test_pr249_observed_wake_outbox_cleanup.py`
- `tests/test_pr250_observed_wake_effect_rename.py`
- `tests/test_pr251_wake_creation_outbox_cutover.py`

## Subproblems
- none

## Results
- R450

## Latest Check
C476

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P462/children/P464/README.md
- Ticket T455: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P462/children/P464/tickets/T455.md
- Result R450: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P462/children/P464/results/R450.md
- Check C476: problems/P000/children/P004/children/P278/children/P284/children/P459/children/P462/children/P464/checks/C476.md

## Follow-ups
- none
