# P118: Start Queue Service On Api With Staging DSN

Status: done
Parent: P116
Root: P000
Source Ticket: none (none)
Source Check: C117
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/README.md
Ticket(s): T113

## Problem
The staging Queue Postgres DSN now exists on `api.gradievo.com`, but Queue Service still needs to be started against it and health/readiness verified. This follow-up should run the service on the api host or an equivalent safe remote runner using the staging DSN file.

## Success Criteria
- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
- Queue Service uses `/opt/novaic/queue-staging-postgres/queue-postgres.dsn`.
- Startup evidence proves the active backend is Postgres.
- Health/readiness endpoints pass.
- DSNs/secrets are redacted from artifacts.

## Subproblems
- P119: Fix Queue Staging DSN And Restart Service

## Results
- R108

## Latest Check
C122

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/README.md
- Ticket T113: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/tickets/T113.md
- Result R108: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/results/R108.md
- Check C118: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/checks/C118.md
- Check C122: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/checks/C122.md

## Follow-ups
- P119: Fix Queue Staging DSN And Restart Service
