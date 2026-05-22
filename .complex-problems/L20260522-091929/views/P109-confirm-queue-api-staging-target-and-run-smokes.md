# P109: Confirm Queue API Staging Target And Run Smokes

Status: followup
Parent: P106
Root: P000
Source Ticket: none (none)
Source Check: C111
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/README.md
Ticket(s): T106

## Problem
P106 cannot be closed until Queue Service is started against a confirmed non-production Postgres target and representative API smokes are executed. The current environment has no `NOVAIC_QUEUE_POSTGRES_DSN_FILE` or `NOVAIC_QUEUE_POSTGRES_DSN`, so the follow-up must either acquire/confirm that target and run the smokes, or remain explicitly blocked without touching production.

## Success Criteria
- A non-production Queue Postgres target is confirmed before any service startup or database write.
- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres` against that target.
- Health/readiness endpoints pass.
- Task publish/claim/complete/fail or safe retry equivalent passes.
- Saga create/claim/launch/complete/fail or safe equivalent passes.
- Session dispatch/finalize/rebuild or safe equivalent passes.
- Idempotency duplicate/in-progress/completed-result smoke passes.
- Post-smoke DB counts are recorded with DSNs/secrets redacted.

## Subproblems
- P110: Confirm Non-Production Queue Postgres Target
- P111: Start Queue Service In Postgres Mode
- P112: Run Queue Service API Smokes
- P113: Record Queue Postgres Post-Smoke Counts

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/README.md
- Ticket T106: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/tickets/T106.md

## Follow-ups
- none
