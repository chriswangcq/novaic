# P125: Restart Production Queue Services In Postgres Mode

Status: done
Parent: P077
Root: P000
Source Ticket: T120 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P077/children/P125
Body: problems/P000/children/P024/children/P028/children/P077/children/P125/README.md
Ticket(s): T132

## Problem
After migration, Queue Service and related worker/outbox processes must be restarted in Postgres mode with the production credential source, and must not resume using `/opt/novaic/data/queue.db`.

## Success Criteria
- Queue Service is restarted with `NOVAIC_QUEUE_DB_BACKEND=postgres` and redacted production credential configuration.
- Task worker, saga worker, session outbox worker, saga outbox worker, and relevant scheduler/health processes are restarted or explicitly declared out of scope.
- `/health` and `/ready` pass after restart.
- Runtime process commands show Postgres mode or Queue Service URL usage as appropriate.
- No process opens `/opt/novaic/data/queue.db` after restart.

## Subproblems
- none

## Results
- R129

## Latest Check
C144

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P077/children/P125/README.md
- Ticket T132: problems/P000/children/P024/children/P028/children/P077/children/P125/tickets/T132.md
- Result R129: problems/P000/children/P024/children/P028/children/P077/children/P125/results/R129.md
- Check C144: problems/P000/children/P024/children/P028/children/P077/children/P125/checks/C144.md

## Follow-ups
- none
