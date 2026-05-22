# P036: Execute Cortex Production Operational Cutover

Status: done
Parent: P034
Root: P000
Source Ticket: T032 (split)
Source Check: none
Package: problems/P000/children/P024/children/P026/children/P034/children/P036
Body: problems/P000/children/P024/children/P026/children/P034/children/P036/README.md
Ticket(s): T034

## Problem
After preflight succeeds, Cortex production operational state must be backed up, migrated to `novaic_cortex`, and Cortex must restart with Postgres operational backend.

## Success Criteria
- `operational.sqlite3` backup exists before migration.
- All five operational tables migrate with matching row counts.
- Cortex startup uses Postgres operational backend and DSN file path.
- Cortex `/health` and `/ready` pass after restart.
- Representative operational read smoke passes.
- Old SQLite active path is removed or documented rollback-only.
- Rollback notes and central classification note are updated.

## Subproblems
- P037: Repair Cortex Postgres schema and complete production cutover

## Results
- R031

## Latest Check
C033

## Bodies
- Problem: problems/P000/children/P024/children/P026/children/P034/children/P036/README.md
- Ticket T034: problems/P000/children/P024/children/P026/children/P034/children/P036/tickets/T034.md
- Result R031: problems/P000/children/P024/children/P026/children/P034/children/P036/results/R031.md
- Check C031: problems/P000/children/P024/children/P026/children/P034/children/P036/checks/C031.md
- Check C033: problems/P000/children/P024/children/P026/children/P034/children/P036/checks/C033.md

## Follow-ups
- P037: Repair Cortex Postgres schema and complete production cutover
