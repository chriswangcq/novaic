# P003: Validate and publish controller-only release commit

Status: done
Parent: P002
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P002/children/P003
Body: problems/P000/children/P002/children/P003/README.md
Ticket(s): T003

## Problem
The repository has controller-only release changes that must be validated and published carefully. The code must be committed without unrelated dirty files, and the local test matrix should pass before pushing a commit that remote Release Controller will consume.

## Success Criteria
- Full relevant local test matrix passes, including release-controller tests and repository guard/lint matrix.
- Git diff is reviewed so unrelated dirty files are not staged.
- Controller-only changes are committed and pushed to `main`.
- Remote polling is paused before push or otherwise prevented from running the guarded deploy with the old controller image.

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
