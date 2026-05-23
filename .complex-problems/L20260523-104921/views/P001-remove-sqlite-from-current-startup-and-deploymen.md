# P001: Remove SQLite from current startup and deployment entry points

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Current root startup scripts and service launch arguments still pass server SQLite database paths after the Postgres cutover, including Entangled and Cortex paths. These entry points are the highest-risk residue because they define how future deployments are copied or restarted.

## Success Criteria
- Current startup scripts launch migrated services with Postgres backend arguments or explicit Postgres DSN files.
- Current startup scripts no longer pass `entangled.db`, `operational.sqlite3`, `gateway.db`, `device.db`, `business.db`, or `queue.db` paths as server persistence.
- Existing unrelated root worktree edits are preserved.
- A focused residue scan over current startup/deployment paths confirms no server SQLite DB launch arguments remain.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
