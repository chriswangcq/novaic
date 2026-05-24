# P005: Deploy release-controller to API host and verify

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P005
Body: problems/P000/children/P005/README.md
Ticket(s): T014

## Problem
After implementation, deploy the controller to the API host and verify it can observe the configured branch and report status without disrupting prod/staging runtime.

## Success Criteria
- Release-controller container runs on the API host.
- `/health` and `/v1/status` return healthy JSON.
- Controller can see the configured git branch head.
- A dry-run trigger produces a recorded run plan without changing prod/staging service containers.
- Existing prod/staging backend health remains green after deployment.

## Subproblems
- none

## Results
- R013

## Latest Check
C014

## Bodies
- Problem: problems/P000/children/P005/README.md
- Ticket T014: problems/P000/children/P005/tickets/T014.md
- Result R013: problems/P000/children/P005/results/R013.md
- Check C014: problems/P000/children/P005/checks/C014.md

## Follow-ups
- none
