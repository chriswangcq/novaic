# P019: Map Entangled SQLite Semantics to Postgres Requirements

Status: done
Parent: P009
Root: P000
Source Ticket: T015 (split)
Source Check: none
Package: problems/P000/children/P004/children/P009/children/P019
Body: problems/P000/children/P004/children/P009/children/P019/README.md
Ticket(s): T017

## Problem
Entangled's SQLite usage is not a single static schema. Dynamic entity registration, generated DDL, schema-driven CRUD, JSON/boolean/timestamp serialization, scoped list queries, stream pagination, sync-version persistence, and append-only transition logs all encode runtime semantics that must survive a Postgres migration.

This belongs under P009 because the migration requirements cannot be trusted until the SQLite-era behaviors and their Postgres equivalents are explicit.

## Success Criteria
- `Database` connection, transaction, FIFO lock, PRAGMA, and row-return behavior is mapped to a Postgres adapter requirement.
- `SqlEntityDef`, `FieldDef`, and generated DDL/index behavior are mapped to Postgres type, constraint, index, and additive-migration rules.
- `SqlEntityStore` CRUD/list/list_stream/filter/order/pagination/upsert behavior is mapped to Postgres SQL patterns, placeholders, row conversion, and JSON/boolean/timestamp serialization rules.
- Schema registration ordering and idempotency are documented, including `ensure_schema_unlocked` column-before-index behavior.
- `entangled_sync_versions` load and upsert behavior is mapped to a monotonic Postgres design.
- Raw `subagent_state_transitions` DDL and append/list behavior is mapped to Postgres identity/index/JSONB/timestamp requirements.
- Sync/client compatibility risks are documented for schema push, full sync, delta sync, reconnect, and ordering semantics.

## Subproblems
- none

## Results
- R014

## Latest Check
C014

## Bodies
- Problem: problems/P000/children/P004/children/P009/children/P019/README.md
- Ticket T017: problems/P000/children/P004/children/P009/children/P019/tickets/T017.md
- Result R014: problems/P000/children/P004/children/P009/children/P019/results/R014.md
- Check C014: problems/P000/children/P004/children/P009/children/P019/checks/C014.md

## Follow-ups
- none
