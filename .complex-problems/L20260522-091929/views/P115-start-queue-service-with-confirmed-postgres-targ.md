# P115: Start Queue Service With Confirmed Postgres Target

Status: followup
Parent: P111
Root: P000
Source Ticket: T108 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/README.md
Ticket(s): T110

## Problem
After startup defaults are clean and a non-production Queue Postgres target is available, Queue Service must actually start in Postgres mode and pass health/readiness. This child belongs under P111 because runtime startup is blocked by environment/credential availability, unlike code cleanup.

## Success Criteria
- A confirmed non-production Queue Postgres target is available before startup.
- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
- Startup evidence proves Postgres mode.
- Health/readiness endpoints pass.
- Secrets and DSNs are redacted from artifacts.

## Subproblems
- P116: Start Queue Service After Staging DSN Is Supplied

## Results
- R105

## Latest Check
C114

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/README.md
- Ticket T110: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/tickets/T110.md
- Result R105: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/results/R105.md
- Check C114: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/checks/C114.md

## Follow-ups
- P116: Start Queue Service After Staging DSN Is Supplied
