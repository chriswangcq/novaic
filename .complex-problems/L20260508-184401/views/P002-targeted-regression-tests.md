# P002: Targeted regression tests

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Add and run targeted tests proving the code repair guards the production regression: dispatch uses configured timeout, and saga claim/FSM ledger writes tolerate normal SQLite contention rather than surfacing a 500/database locked failure.

## Success Criteria
- Tests exist in the appropriate repo(s).
- Targeted tests pass locally.
- Any failing unrelated test is documented rather than hidden.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
