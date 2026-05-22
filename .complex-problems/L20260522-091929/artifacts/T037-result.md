# Entangled Postgres adapter boundary result

## Summary

P038 added the first Entangled Postgres runtime boundary without switching production. Entangled now has explicit backend selection, Postgres DSN/DSN-file config, a lazy-import Postgres adapter with pool/advisory-lock/transaction primitives, and tests proving SQLite compatibility plus Postgres misconfiguration fail-fast behavior.

## Done

- Extended `ServiceConfig` with `db_backend`, `postgres_dsn`, and `postgres_dsn_file`.
- Added CLI flags `--db-backend`, `--postgres-dsn`, and `--postgres-dsn-file`.
- Updated app factory/state wiring to select SQLite or Postgres explicitly.
- Added `PostgresDatabase` behind the Entangled DB boundary with:
  - DSN and DSN-file loading;
  - lazy `psycopg`/`psycopg_pool` imports;
  - connection-pool lifecycle;
  - dict-like `fetchone`/`fetchall`;
  - placeholder conversion from `?` to `%s`;
  - transaction-scoped advisory locks;
  - commit/rollback, `executemany`, and `insert_returning_id` primitives.
- Exported `PostgresDatabase` and `create_database` from `entangled.sql`.
- Added Postgres runtime dependency to the app extra.
- Added focused tests in `tests/test_postgres_database_boundary.py`.

## Verification

- `python -m pytest` in `Entangled/packages/server-python` passed: `80 passed`.
- py_compile passed for touched Entangled modules.
- Focused P038 tests cover:
  - explicit backend factory selection;
  - Postgres DSN requirement fail-fast;
  - DSN-file loading through a fake pool;
  - transaction begin/advisory-lock/commit path;
  - rollback on exception;
  - failed Postgres init not poisoning the app singleton.

## Known Gaps

- Full Postgres DDL/entity-store SQL dialect conversion is intentionally deferred to P039.
- Migration tooling, staging validation, and production cutover are intentionally deferred to P040-P042.
- No production Entangled runtime or `/opt/novaic/start.sh` change was made in this child.

## Artifacts

- `Entangled/packages/server-python/entangled/sql/database.py`
- `Entangled/packages/server-python/entangled/app/config.py`
- `Entangled/packages/server-python/entangled/app/main.py`
- `Entangled/packages/server-python/entangled/app/factory.py`
- `Entangled/packages/server-python/entangled/app/state.py`
- `Entangled/packages/server-python/tests/test_postgres_database_boundary.py`
