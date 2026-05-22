# P120: Fix Fresh Postgres Schema Init Transaction Handling

Status: done
Parent: P119
Root: P000
Source Ticket: none (none)
Source Check: C119
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/children/P120
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/children/P120/README.md
Ticket(s): T115

## Problem
Queue Service cannot initialize a fresh Postgres database because `init_postgres_schema` catches the expected missing `config` table error but does not roll back the failed transaction before running baseline DDL. Postgres then rejects subsequent DDL with `InFailedSqlTransaction`.

## Success Criteria
- `init_postgres_schema` rolls back after the initial version probe fails on a fresh Postgres database.
- A focused test covers fresh Postgres missing-`config` behavior or an equivalent fake connection that proves rollback happens before baseline DDL.
- Existing Queue Service schema tests still pass.
- The fix is deployed to the api staging checkout.
- Queue Service starts on `api.gradievo.com` using the staging DSN file.
- `/health` and `/ready` pass on `127.0.0.1:19987`.

## Subproblems
- none

## Results
- R110

## Latest Check
C120

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/children/P120/README.md
- Ticket T115: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/children/P120/tickets/T115.md
- Result R110: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/children/P120/results/R110.md
- Check C120: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P111/children/P115/children/P116/children/P118/children/P119/children/P120/checks/C120.md

## Follow-ups
- none
