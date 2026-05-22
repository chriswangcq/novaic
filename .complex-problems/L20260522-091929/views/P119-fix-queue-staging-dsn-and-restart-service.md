# P119: Fix Queue Staging DSN And Restart Service

Status: done
Parent: P118
Root: P000
Source Ticket: none (none)
Source Check: C118
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/README.md
Ticket(s): T114

## Problem
Queue Service on `api.gradievo.com` cannot complete startup against the staging Postgres DSN file because the current DSN URI is not safely parseable when credentials contain reserved URL characters. The DSN source must remain a file, but its contents need to be regenerated without exposing the secret, then Queue Service must be restarted on the loopback staging port.

## Success Criteria
- `/opt/novaic/queue-staging-postgres/queue-postgres.dsn` is regenerated in a libpq-safe form without printing or committing the secret.
- The existing `novaic-queue-staging-postgres` Docker container remains healthy and reachable on its intended loopback port.
- Queue Service starts on `api.gradievo.com` using `NOVAIC_QUEUE_POSTGRES_DSN_FILE=/opt/novaic/queue-staging-postgres/queue-postgres.dsn`.
- `http://127.0.0.1:19987/health` passes and reports the Postgres backend.
- `http://127.0.0.1:19987/ready` passes.
- Production service configuration and public ports are not modified.

## Subproblems
- P120: Fix Fresh Postgres Schema Init Transaction Handling

## Results
- R109

## Latest Check
C121

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/README.md
- Ticket T114: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/tickets/T114.md
- Result R109: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/results/R109.md
- Check C119: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/checks/C119.md
- Check C121: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/checks/C121.md

## Follow-ups
- P120: Fix Fresh Postgres Schema Init Transaction Handling
