# P111: Start Queue Service In Postgres Mode

Status: todo
Parent: P109
Root: P000
Source Ticket: T106 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/README.md
Ticket(s): T108

## Problem
After a safe target is confirmed, Queue Service must start as a real runtime in Postgres mode without silently falling back to SQLite. This child belongs under T106 because service startup failure is distinct from both credential discovery and endpoint behavior.

## Success Criteria
- Queue Service is started with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
- Startup logs or runtime public info prove the Postgres backend is active.
- Required auth/bind settings are recorded without secrets.
- Health/readiness endpoints are reachable.
- No SQLite database path is used for the smoke runtime.

## Subproblems
- P114: Clean Queue Startup Postgres Default
- P115: Start Queue Service With Confirmed Postgres Target

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/README.md
- Ticket T108: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/tickets/T108.md

## Follow-ups
- none
