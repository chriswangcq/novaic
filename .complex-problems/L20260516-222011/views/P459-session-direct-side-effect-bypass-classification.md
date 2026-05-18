# P459: Session direct side-effect bypass classification

Status: done
Parent: P284
Root: P000
Source Ticket: T450 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P284/children/P459
Body: problems/P000/children/P004/children/P278/children/P284/children/P459/README.md
Ticket(s): T452

## Problem
Search for direct side effects that may bypass durable session outbox ownership and classify or fix them.

## Success Criteria
- Search for direct saga creation/publish, attach input publish, archive/recovery publish, and wake-created active-state mutation paths.
- Classify each hit as safe implementation detail, risky bypass, or removable residue.
- Fix risky bypasses or split concrete follow-up children with tests.
- Save guard artifacts under `.complex-problems/L20260516-222011/tmp/p459/`.

## Subproblems
- P461: Dispatcher direct call classification
- P462: Observed wake outbox residue cleanup
- P463: Side-effect bypass final guard

## Results
- R452

## Latest Check
C479

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P284/children/P459/README.md
- Ticket T452: problems/P000/children/P004/children/P278/children/P284/children/P459/tickets/T452.md
- Result R452: problems/P000/children/P004/children/P278/children/P284/children/P459/results/R452.md
- Check C479: problems/P000/children/P004/children/P278/children/P284/children/P459/checks/C479.md

## Follow-ups
- none
