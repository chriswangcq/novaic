# P024: Implement Remaining Service Postgres Cutovers

Status: done
Parent: P000
Root: P000
Source Ticket: none (none)
Source Check: C023
Package: problems/P000/children/P024
Body: problems/P000/children/P024/README.md
Ticket(s): T024

## Problem
The first safe phase is complete: Postgres is provisioned, LLM Factory is on Postgres, SQLite owners are classified, high-risk semantics are mapped, and stale residue is cleaned. The remaining user goal is to migrate all remaining service-side persistent state off SQLite and onto the existing per-service Postgres databases without maintaining production SQLite fallback logic.

Remaining active SQLite owners:

- `/opt/novaic/data/queue.db`
- `/opt/novaic/data/entangled.db`
- `/opt/novaic/data/gateway.db`
- `/opt/novaic/data/cortex/operational.sqlite3`

## Success Criteria
- Each remaining service has a production Postgres-backed code path and deployed runtime configuration.
- No production service keeps SQLite fallback logic for the migrated state path.
- Existing SQLite state is backed up before mutation and migrated with row-count/referential checks.
- Service-specific behavior is preserved according to the artifacts produced in P008, P009, P010, and P011.
- Live health/readiness checks pass after each cutover.
- Rollback instructions and retained snapshots are recorded for each service.
- Final SQLite classification note identifies remaining SQLite files as rollback-only snapshots or separately justified non-service data.

## Subproblems
- P025: Implement Gateway Postgres Auth Config Cutover
- P026: Implement Cortex Operational Postgres Cutover
- P027: Implement Entangled Postgres Cutover
- P028: Implement Queue Postgres Cutover
- P136: Repair Final SQLite Classification Rows For Gateway And Cortex

## Results
- R135

## Latest Check
C153

## Bodies
- Problem: problems/P000/children/P024/README.md
- Ticket T024: problems/P000/children/P024/tickets/T024.md
- Result R135: problems/P000/children/P024/results/R135.md
- Check C151: problems/P000/children/P024/checks/C151.md
- Check C153: problems/P000/children/P024/checks/C153.md

## Follow-ups
- P136: Repair Final SQLite Classification Rows For Gateway And Cortex
