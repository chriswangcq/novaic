# Plan core database migrations and close legacy residue

## Problem

The high-risk state owners (`queue.db`, `entangled.db`, and gateway/cortex local stores) require explicit semantic mapping before migrating to Postgres. At the same time, stale empty DB files and obsolete comments/code paths should be removed or quarantined once proven non-current.

## Success Criteria

- `queue.db` FSM/outbox/lease semantics are mapped to Postgres transactions, JSONB, indexes, and row-locking/advisory-lock behavior before any cutover.
- `entangled.db` entity-store migration requirements are documented, including schema registration and sync-version behavior.
- `gateway.db` and `cortex/operational.sqlite3` are classified as migrate/defer/projection with reasons.
- Empty `business.db` and unused `device.db` residue is archived or removed after verifying restart behavior, or code is updated to stop recreating misleading files.
- Remaining non-migrated SQLite files have explicit owner notes and backup coverage.
