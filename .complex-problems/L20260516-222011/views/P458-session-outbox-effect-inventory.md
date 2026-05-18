# P458: Session outbox effect inventory

Status: done
Parent: P284
Root: P000
Source Ticket: T450 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P284/children/P458
Body: problems/P000/children/P004/children/P278/children/P284/children/P458/README.md
Ticket(s): T451

## Problem
Map session outbox effect types, creation points, persistence points, workers, and downstream handlers with file references.

## Success Criteria
- List every session outbox effect type and payload identity fields.
- Map where effects are recorded and where they are delivered.
- Identify downstream handler boundaries for wake saga creation, attach input, session-ended/finalize, recovery/archive, and observed wake-created updates.
- Save source guard artifacts under `.complex-problems/L20260516-222011/tmp/p458/`.

## Subproblems
- none

## Results
- R447

## Latest Check
C473

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P284/children/P458/README.md
- Ticket T451: problems/P000/children/P004/children/P278/children/P284/children/P458/tickets/T451.md
- Result R447: problems/P000/children/P004/children/P278/children/P284/children/P458/results/R447.md
- Check C473: problems/P000/children/P004/children/P278/children/P284/children/P458/checks/C473.md

## Follow-ups
- none
