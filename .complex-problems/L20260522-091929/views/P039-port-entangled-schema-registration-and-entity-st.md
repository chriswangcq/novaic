# P039: Port Entangled schema registration and entity store semantics to Postgres

Status: done
Parent: P027
Root: P000
Source Ticket: T036 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P039
Body: problems/P000/children/P024/children/P027/children/P039/README.md
Ticket(s): T038

## Problem
Entangled dynamically generates SQL for entity schemas, CRUD, list/stream pagination, sync versions, transition logs, and JSON/BOOL/TIMESTAMP fields. Port these semantics to Postgres while preserving client-visible row shapes and sync behavior.

## Success Criteria
- `FieldDef` and `SqlEntityDef` have a Postgres DDL dialect with safe identifiers, catalog inspection, table creation, additive columns, and indexes.
- Live entity schemas can be generated for Postgres with expected columns, primary keys, unique constraints, and indexes.
- Entity store CRUD/upsert/update/delete/CAS/list/list_stream/cleanup paths are Postgres-safe.
- SQLite `rowid` tie-break behavior is replaced by migrated `entangled_rowid`.
- JSON, BOOL, BLOB, INTEGER, REAL, and TIMESTAMP wire shapes match existing API behavior.
- `entangled_sync_versions` monotonic upsert and `subagent_state_transitions` atomicity are preserved.
- Focused behavior tests pass for schema registration, REST row shapes, stream ordering, sync versions, and transition rollback.

## Subproblems
- P043: Add Entangled Postgres DDL dialect and schema inspection
- P044: Port Entangled entity-store queries and rowid semantics to Postgres
- P045: Port Entangled sync-version and transition-log persistence to Postgres

## Results
- R042

## Latest Check
C043

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P039/README.md
- Ticket T038: problems/P000/children/P024/children/P027/children/P039/tickets/T038.md
- Result R042: problems/P000/children/P024/children/P027/children/P039/results/R042.md
- Check C043: problems/P000/children/P024/children/P027/children/P039/checks/C043.md

## Follow-ups
- none
