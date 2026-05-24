# P004: Publish quality-gate controller code safely

Status: done
Parent: P003
Root: P000
Source Ticket: T003 (split)
Source Check: none
Package: problems/P000/children/P003/children/P004
Body: problems/P000/children/P003/children/P004/README.md
Ticket(s): T004

## Problem
The quality-gate implementation must be committed and pushed without accidentally including unrelated dirty workspace changes. Polling must be paused first so the old API-host controller cannot process the new commit before it is upgraded.

## Success Criteria
- API-host Release Controller polling is paused before pushing the quality-gate commit.
- Local release-controller/deploy guard tests pass before commit.
- Only intended source/config/docs/test files and the active ledger are staged, with unrelated pre-existing dirty files left untouched.
- The parent commit is pushed to `origin/main` and its commit id is recorded.
- If any submodule changed intentionally, its commit/push is recorded; otherwise no submodule churn is introduced.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/children/P004/README.md
- Ticket T004: problems/P000/children/P003/children/P004/tickets/T004.md
- Result R002: problems/P000/children/P003/children/P004/results/R002.md
- Check C002: problems/P000/children/P003/children/P004/checks/C002.md

## Follow-ups
- none
