# P489: Finalize ownership cleanup

Status: done
Parent: P482
Root: P000
Source Ticket: T481 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P489
Body: problems/P000/children/P004/children/P279/children/P482/children/P489/README.md
Ticket(s): T483

## Problem
Finalize behavior must be owned by explicit event/FSM decisions with reason, generation, and remaining stack semantics. Any stale finalize compatibility branch that clears active state directly, tolerates missing generation, or hides dangling child skills creates the same class of bug the session FSM work was meant to eliminate. This belongs under P482 because finalize is the highest-risk compatibility surface.

## Success Criteria
- Finalize production code is inspected against the P482 inventory.
- High-confidence stale finalize branches are removed or tightened.
- Any retained compatibility-looking finalize branch has a documented reason and a focused guard test.
- Focused finalize ownership/session-end tests pass.

## Subproblems
- P493: Finalize producer remaining-stack contract audit
- P494: Wake finalize remaining-stack strictness
- P495: Finalize ownership final verification

## Results
- R482

## Latest Check
C511

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P489/README.md
- Ticket T483: problems/P000/children/P004/children/P279/children/P482/children/P489/tickets/T483.md
- Result R482: problems/P000/children/P004/children/P279/children/P482/children/P489/results/R482.md
- Check C511: problems/P000/children/P004/children/P279/children/P482/children/P489/checks/C511.md

## Follow-ups
- none
