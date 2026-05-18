# P293: Problem: Session direct SQL and mutation residue scan

Status: done
Parent: P287
Root: P000
Source Ticket: T280 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/README.md
Ticket(s): T307

## Problem
Search for direct session table SQL, old repository wrappers, compatibility branches, and mutation shortcuts outside the intended ledger/repository/outbox boundary.

## Success Criteria
- List searched patterns and matches.
- Classify matches as legitimate adapter SQL, test guard, documentation, risky active path, or removable residue.
- If risky/removable production residue exists, create a cleanup follow-up.

## Subproblems
- P318: Scan direct session SQL table access
- P319: Scan old session wrappers and compatibility branches
- P320: Consolidate session residue scan classification

## Results
- R306

## Latest Check
C326

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/README.md
- Ticket T307: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/tickets/T307.md
- Result R306: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/results/R306.md
- Check C326: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/checks/C326.md

## Follow-ups
- none
