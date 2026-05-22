# P035: Cortex Production Cutover Preflight

Status: done
Parent: P034
Root: P000
Source Ticket: T032 (split)
Source Check: none
Package: problems/P000/children/P024/children/P026/children/P034/children/P035
Body: problems/P000/children/P024/children/P026/children/P034/children/P035/README.md
Ticket(s): T033

## Problem
Before switching production Cortex to Postgres, remote runtime, source counts, target DB readiness, DSN file, dependency readiness, and migration mechanics must be verified without restart/backend switch.

## Success Criteria
- Current Cortex runtime and readiness are captured.
- Source SQLite row counts for all five operational tables are captured.
- `novaic_cortex` target DB is reachable and target table state is known.
- DSN file exists with restrictive permissions and is connection-tested without printing credentials.
- Remote Cortex venv can import `psycopg`.
- Migration script is ready for execution.
- Cortex remains on SQLite during preflight.

## Subproblems
- none

## Results
- R030

## Latest Check
C030

## Bodies
- Problem: problems/P000/children/P024/children/P026/children/P034/children/P035/README.md
- Ticket T033: problems/P000/children/P024/children/P026/children/P034/children/P035/tickets/T033.md
- Result R030: problems/P000/children/P024/children/P026/children/P034/children/P035/results/R030.md
- Check C030: problems/P000/children/P024/children/P026/children/P034/children/P035/checks/C030.md

## Follow-ups
- none
