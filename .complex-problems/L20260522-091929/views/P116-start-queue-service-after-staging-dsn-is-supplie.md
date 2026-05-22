# P116: Start Queue Service After Staging DSN Is Supplied

Status: followup
Parent: P115
Root: P000
Source Ticket: none (none)
Source Check: C114
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/README.md
Ticket(s): T111

## Problem
P115 cannot close until a confirmed non-production Queue Postgres target is supplied to the runner and Queue Service starts in Postgres mode. The startup default code path is now clean, but the environment prerequisite is still missing.

## Success Criteria
- A confirmed non-production Queue Postgres DSN or DSN file is supplied.
- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
- Startup evidence proves the active backend is Postgres.
- Health/readiness endpoints pass.
- DSNs/secrets are redacted from all artifacts.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/README.md
- Ticket T111: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/tickets/T111.md

## Follow-ups
- none
