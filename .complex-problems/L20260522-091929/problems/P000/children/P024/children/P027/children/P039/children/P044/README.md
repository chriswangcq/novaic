# Port Entangled entity-store queries and rowid semantics to Postgres

## Problem

`SqlEntityStore` query construction is SQLite-specific across CRUD, upsert, list, stream pagination, cleanup, timestamp updates, and `rowid` tie-breaks. Add dialect-aware query paths for Postgres while preserving API row shapes and existing SQLite behavior.

## Success Criteria

- CRUD/create/get/update/delete/upsert/CAS/list/list_stream/update_where/delete_where/cleanup paths generate Postgres-safe SQL.
- SQLite `rowid` comparisons and orderings are replaced by `entangled_rowid` in Postgres.
- JSON, BOOL, BLOB, INTEGER, REAL, and TIMESTAMP input/output behavior matches current API row shapes.
- Parent/user/key-param scoping, `filters`, `in_filters`, `not_in_filters`, defaults, hidden fields, and `has_<hidden>` behavior are preserved.
- Auto-integer IDs use `RETURNING` in Postgres.
- Existing SQLite behavior remains covered and passing.
- Focused tests cover duplicate cursor values, rowid tie-break migration semantics, JSON/BOOL round trip, and rowcount-driven updates/deletes.
