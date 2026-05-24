# P006: Make Release Controller image capable of running quality gates

Status: done
Parent: P005
Root: P000
Source Ticket: T005 (spawn)
Source Check: none
Package: problems/P000/children/P003/children/P005/children/P006
Body: problems/P000/children/P003/children/P005/children/P006/README.md
Ticket(s): T006

## Problem
The default `quality_gates` include pytest-based controller CI checks, but the Release Controller Docker image currently installs only the release-controller package and runtime tooling. Without pytest in the image, the API-host controller cannot execute the default gate list and staging admission would fail for an infrastructure reason rather than a code quality reason.

## Success Criteria
- Release Controller Docker image installs the minimal test tooling required by default `quality_gates`.
- Dockerfile invariant tests cover that the test tooling remains available.
- Sample quality gates remain executable inside the controller worktree.
- Local tests for release-controller and release-controller CI guards pass after the image change.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P003/children/P005/children/P006/README.md
- Ticket T006: problems/P000/children/P003/children/P005/children/P006/tickets/T006.md
- Result R003: problems/P000/children/P003/children/P005/children/P006/results/R003.md
- Check C003: problems/P000/children/P003/children/P005/children/P006/checks/C003.md

## Follow-ups
- none
