# P003: Publish persistence commit with remote polling paused

Status: done
Parent: P002
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P002/children/P003
Body: problems/P000/children/P002/children/P003/README.md
Ticket(s): T003

## Problem
Before the API-host controller can run the persistence change, the local source must be committed and pushed without unrelated workspace residue, and remote polling must be paused so the old controller does not auto-process the new main commit.

## Success Criteria
- API-host controller status is captured before changes, including current prod/staging pointers and polling state.
- Remote polling is disabled and verified before the new commit is pushed.
- Only intended release-controller persistence files are staged and committed locally.
- The persistence commit is pushed to `origin/main` and its hash is recorded.
- Remote controller still reports healthy status with polling disabled after the push.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/children/P003/README.md
- Ticket T003: problems/P000/children/P002/children/P003/tickets/T003.md
- Result R001: problems/P000/children/P002/children/P003/results/R001.md
- Check C001: problems/P000/children/P002/children/P003/checks/C001.md

## Follow-ups
- none
