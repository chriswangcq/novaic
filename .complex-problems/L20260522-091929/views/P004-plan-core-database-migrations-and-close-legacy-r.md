# P004: Plan core database migrations and close legacy residue

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T007

## Problem
The high-risk state owners (`queue.db`, `entangled.db`, and gateway/cortex local stores) require explicit semantic mapping before migrating to Postgres. At the same time, stale empty DB files and obsolete comments/code paths should be removed or quarantined once proven non-current.

## Success Criteria
- `queue.db` FSM/outbox/lease semantics are mapped to Postgres transactions, JSONB, indexes, and row-locking/advisory-lock behavior before any cutover.
- `entangled.db` entity-store migration requirements are documented, including schema registration and sync-version behavior.
- `gateway.db` and `cortex/operational.sqlite3` are classified as migrate/defer/projection with reasons.
- Empty `business.db` and unused `device.db` residue is archived or removed after verifying restart behavior, or code is updated to stop recreating misleading files.
- Remaining non-migrated SQLite files have explicit owner notes and backup coverage.

## Subproblems
- P008: Map Queue SQLite Semantics to Postgres
- P009: Design Entangled Postgres Migration Requirements
- P010: Classify Gateway and Cortex Postgres Boundaries
- P011: Close Device DB Live-Empty Residue

## Results
- R022

## Latest Check
C022

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T007: problems/P000/children/P004/tickets/T007.md
- Result R022: problems/P000/children/P004/results/R022.md
- Check C022: problems/P000/children/P004/checks/C022.md

## Follow-ups
- none
