# P323: Audit rebuild and pending projection writers

Status: done
Parent: P288
Root: P000
Source Ticket: T312 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P323
Body: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P323/README.md
Ticket(s): T314

## Problem
Map session rebuild and pending-input projection writers to verify they update the intended session ledger/state model and cannot drift as independent authoritative state.

## Success Criteria
- Rebuild/projection functions are listed with file references.
- Their source tables/events and target state/projection are identified.
- Any independent cache/view that can drift from session ledger authority is flagged.

## Subproblems
- none

## Results
- R309

## Latest Check
C329

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P323/README.md
- Ticket T314: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P323/tickets/T314.md
- Result R309: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P323/results/R309.md
- Check C329: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P323/checks/C329.md

## Follow-ups
- none
