# P034: Cut Over Cortex Production Operational Store to Postgres

Status: done
Parent: P026
Root: P000
Source Ticket: T030 (split)
Source Check: none
Package: problems/P000/children/P024/children/P026/children/P034
Body: problems/P000/children/P024/children/P026/children/P034/README.md
Ticket(s): T032

## Problem
After Cortex has a Postgres operational store, production operational state must be backed up, migrated from SQLite to `novaic_cortex`, and Cortex must restart with the Postgres backend.

## Success Criteria
- `/opt/novaic/data/cortex/operational.sqlite3` is backed up before migration.
- All five operational tables are migrated with row-count checks.
- Cortex runtime starts with the Postgres operational backend.
- Cortex `/health` and `/ready` pass after restart.
- Representative operational reads pass after cutover.
- Old operational SQLite is moved or labeled rollback-only.
- Rollback notes and central classification note are updated.

## Subproblems
- P035: Cortex Production Cutover Preflight
- P036: Execute Cortex Production Operational Cutover

## Results
- R033

## Latest Check
C034

## Bodies
- Problem: problems/P000/children/P024/children/P026/children/P034/README.md
- Ticket T032: problems/P000/children/P024/children/P026/children/P034/tickets/T032.md
- Result R033: problems/P000/children/P024/children/P026/children/P034/results/R033.md
- Check C034: problems/P000/children/P024/children/P026/children/P034/checks/C034.md

## Follow-ups
- none
