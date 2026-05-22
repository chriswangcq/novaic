# P037: Repair Cortex Postgres schema and complete production cutover

Status: done
Parent: P036
Root: P000
Source Ticket: none (none)
Source Check: C031
Package: problems/P000/children/P024/children/P026/children/P034/children/P036/children/P037
Body: problems/P000/children/P024/children/P026/children/P034/children/P036/children/P037/README.md
Ticket(s): T035

## Problem
The first Cortex production operational cutover attempt failed during migration because production generation values exceed the Postgres `INTEGER` range. Repair the Cortex Postgres operational schema and migration retry behavior, redeploy the fix, rerun the migration, switch Cortex to the Postgres backend, verify the runtime, and remove the active SQLite residue only after the Postgres-backed service is healthy.

## Success Criteria
- Cortex Postgres operational schema uses `BIGINT` for production-sized integer counters and timestamps.
- The migration script's `--replace` path can cleanly recover from a partially created incompatible target schema.
- Remote migration into `novaic_cortex` completes with matching counts for all five operational tables.
- `/opt/novaic/start.sh` starts Cortex with Postgres operational backend flags and a DSN file path.
- Cortex `/health` and `/ready` pass after restart.
- Representative operational read smoke passes after restart.
- No process holds `/opt/novaic/data/cortex/operational.sqlite3`, and the old SQLite file is moved out of the active path only after verification succeeds.
- Rollback note, central SQLite classification note, and local cutover artifact are updated.

## Subproblems
- none

## Results
- R032

## Latest Check
C032

## Bodies
- Problem: problems/P000/children/P024/children/P026/children/P034/children/P036/children/P037/README.md
- Ticket T035: problems/P000/children/P024/children/P026/children/P034/children/P036/children/P037/tickets/T035.md
- Result R032: problems/P000/children/P024/children/P026/children/P034/children/P036/children/P037/results/R032.md
- Check C032: problems/P000/children/P024/children/P026/children/P034/children/P036/children/P037/checks/C032.md

## Follow-ups
- none
