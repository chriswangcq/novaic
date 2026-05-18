# P497: Attach generation contract hardening

Status: done
Parent: P490
Root: P000
Source Ticket: T487 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497
Body: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/README.md
Ticket(s): T489

## Problem
If the inventory finds missing guard coverage or stale no-generation behavior, tighten the attach code/tests so active input delivery is generation-checked end to end. This belongs under P490 because attach must not deliver user input to the wrong wake.

## Success Criteria
- Missing no-generation/stale-generation behavior is removed or converted to strict validation/buffering.
- Focused tests cover the hardened boundary.
- Existing attach-race buffering behavior remains intact.

## Subproblems
- P499: Attach effect builder strict generation boundary
- P500: Attach generation hardening verification

## Results
- R486

## Latest Check
C515

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/README.md
- Ticket T489: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/tickets/T489.md
- Result R486: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/results/R486.md
- Check C515: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/checks/C515.md

## Follow-ups
- none
