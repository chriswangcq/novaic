# P002: Deploy execution-result persistence to API-host controller

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
After local implementation is pushed, the API-host Release Controller must run the new code and prove historical run inspection exposes persisted execution results.

## Success Criteria
- API-host polling is paused before publishing the new controller persistence commit.
- New Release Controller image is built/pushed/deployed from the persistence commit.
- A remote verification run creates a persisted run record with `execution_result.results` visible from `/v1/runs/{run_id}` after the response.
- Polling is restored with `last_error=null`.
- Staging/prod pointers remain in the intended state unless explicitly changed.

## Subproblems
- P003: Publish persistence commit with remote polling paused
- P004: Deploy persisted-result controller image and verify remote run record

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R003: problems/P000/children/P002/results/R003.md
- Check C003: problems/P000/children/P002/checks/C003.md

## Follow-ups
- none
