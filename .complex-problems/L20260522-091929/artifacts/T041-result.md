# Entangled basic Postgres write-query result

## Summary

P046 added dialect-aware basic write-query behavior for Entangled. Postgres write paths now avoid SQLite timestamp expressions and use `RETURNING` for auto-integer creates/appends, while the current SQLite behavior remains passing.

## Done

- Added `SqlEntityStore` dialect helpers for backend detection, timestamp update expressions, insert SQL, and auto-ID insert handling.
- Changed `_sql_create` and `append` to use `RETURNING` through `insert_returning_id` in Postgres mode.
- Replaced hard-coded write-path `updated_at = datetime('now')` with a dialect-specific timestamp expression.
- Kept rowcount-driven update/delete/CAS behavior intact.
- Updated Postgres integer primary key DDL to use identity when rendered as a single primary key.
- Added fake-Postgres SQL-capture tests for auto-ID create, update, upsert, delete, and CAS write paths.

## Verification

- Targeted tests passed: `15 passed`.
- Full Entangled test suite passed: `90 passed`.
- py_compile passed for touched write-query modules.

## Known Gaps

- Stream/list pagination and cleanup `rowid` conversion is intentionally deferred to P047.
- Output-shape cross-checks are intentionally deferred to P048.
- Real Postgres execution is deferred to the staging validation problem.

## Artifacts

- `Entangled/packages/server-python/entangled/sql/entity_store.py`
- `Entangled/packages/server-python/entangled/sql/field_def.py`
- `Entangled/packages/server-python/tests/test_postgres_entity_write_queries.py`
- `Entangled/packages/server-python/tests/test_postgres_ddl_dialect.py`
