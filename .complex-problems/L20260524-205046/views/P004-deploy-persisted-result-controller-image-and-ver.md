# P004: Deploy persisted-result controller image and verify remote run record

Status: done
Parent: P002
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P002/children/P004
Body: problems/P000/children/P002/children/P004/README.md
Ticket(s): T004

## Problem
The API-host controller must be upgraded to an immutable image built from the persistence commit, and a remote verification run must prove `/v1/runs/{run_id}` exposes persisted `execution_result.results` after the request completes.

## Success Criteria
- A new `novaic/release-controller` image is built and pushed on the API host from the persistence commit.
- The controller is deployed by immutable digest through the existing release-controller image path.
- A safe remote verification run creates or observes a persisted run with non-empty `execution_result.results` from `/v1/runs/{run_id}`.
- Polling is restored and `/v1/status` reports `polling.last_error=null`.
- Prod/staging release pointers are checked after deployment and any intentional staging movement is recorded.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P002/children/P004/README.md
- Ticket T004: problems/P000/children/P002/children/P004/tickets/T004.md
- Result R002: problems/P000/children/P002/children/P004/results/R002.md
- Check C002: problems/P000/children/P002/children/P004/checks/C002.md

## Follow-ups
- none
