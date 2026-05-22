# Port Entangled schema registration and entity store semantics to Postgres

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
