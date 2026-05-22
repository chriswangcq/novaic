# Port Entangled entity-store query semantics to Postgres

## Problem Definition

`SqlEntityStore` still emits SQLite-specific SQL for entity CRUD, upsert, update/delete/CAS, list, list_stream, cleanup, timestamp updates, auto-integer IDs, and `rowid` tie-breaks. P044 must introduce Postgres-safe query semantics while preserving API-visible row shapes and current SQLite behavior.

## Proposed Solution

1. Add a small dialect abstraction inside `SqlEntityStore` for backend-specific expressions:
   - placeholder style through the adapter boundary;
   - current timestamp update expression;
   - rowid/tie-break column (`rowid` vs `entangled_rowid`);
   - upsert conflict/update fragments;
   - auto-integer `RETURNING` behavior.
2. Convert CRUD/create/get/update/delete/upsert/CAS/list/list_stream/update_where/delete_where/cleanup paths to use the dialect abstraction.
3. Preserve `_scope_where`, parent subqueries, filters, `in_filters`, `not_in_filters`, default-not-in filters, hidden-field masking, `has_<hidden>`, JSON/BOOL/TIMESTAMP serialization/deserialization, and rowcount-driven return behavior.
4. Add tests for duplicate cursor field values, `entangled_rowid` query generation, JSON/BOOL output, timestamp update expressions, auto-integer returning, and existing SQLite behavior.
5. Keep production runtime unchanged; no migration or cutover in this child.

## Acceptance Criteria

- SQLite behavior remains compatible and existing tests pass.
- Postgres query paths do not emit SQLite-only `rowid` or `datetime('now')`.
- Postgres stream/list tie-breaks use `entangled_rowid`.
- Postgres auto-integer creates use `RETURNING`.
- Upsert/update/delete/CAS/list/list_stream semantics preserve rowcount and output shape.
- JSON, BOOL, hidden fields, and timestamp-like output remain client-compatible.
- Focused tests and full Entangled tests pass.

## Verification Plan

Use fake Postgres DB captures for generated SQL and existing SQLite tests for runtime compatibility. Run full Entangled pytest and py_compile. Defer real Postgres staging execution to P040.

## Risks

- `list_stream` cursor logic can skip or duplicate rows if tie-break conversion is incomplete.
- Timestamp expression differences can leak into API responses.
- Auto-integer ID handling can diverge between SQLite `lastrowid` and Postgres `RETURNING`.

## Assumptions

- P043's `entangled_rowid` DDL exists for Postgres dynamic entity tables.
- P045 will handle support tables that are not dynamic entity tables.
- P040 will run real Postgres integration/staging validation.
