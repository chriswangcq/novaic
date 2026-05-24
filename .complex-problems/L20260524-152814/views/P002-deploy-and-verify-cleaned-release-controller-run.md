# P002: Deploy and verify cleaned release-controller runtime

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
After the source contract is cleaned, the API host must run the cleaned controller and runtime config must not preserve the removed `dry_run_default` key.

## Success Criteria
- API-host `/opt/novaic/release-controller/config.json` has no `dry_run_default` key.
- A release-controller image from the cleaned source is built, pushed, deployed, and reported healthy.
- A trigger without `dry_run` performs real staging execution and records `dry_run=false`.
- A trigger with explicit `dry_run=true` remains simulation-only and does not update release pointers.
- Staging gateway, staging factory, and controller health checks pass after deployment.

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
