# P013: Package release-controller Docker image

Status: done
Parent: P003
Root: P000
Source Ticket: T009 (split)
Source Check: none
Package: problems/P000/children/P003/children/P013
Body: problems/P000/children/P003/children/P013/README.md
Ticket(s): T010

## Problem
Create Docker image packaging for the release-controller service so it can run from an immutable image instead of source on the host.

## Success Criteria
- A release-controller Dockerfile exists in the repository.
- The image installs the `novaic-release-controller` package and runtime dependencies.
- The container starts the FastAPI app through an explicit entrypoint.
- `NOVAIC_RELEASE_CONTROLLER_CONFIG` is required at runtime.
- Local build or syntax validation proves the Dockerfile is usable.

## Subproblems
- none

## Results
- R008

## Latest Check
C009

## Bodies
- Problem: problems/P000/children/P003/children/P013/README.md
- Ticket T010: problems/P000/children/P003/children/P013/tickets/T010.md
- Result R008: problems/P000/children/P003/children/P013/results/R008.md
- Check C009: problems/P000/children/P003/children/P013/checks/C009.md

## Follow-ups
- none
