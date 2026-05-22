# Add Entangled Postgres adapter and explicit runtime selection

## Problem Definition

Entangled currently constructs a SQLite-only `Database` from `config.db_path` and `--db-path`. Before schema/entity-store migration work can proceed, the service needs an explicit Postgres runtime boundary: config, CLI args, adapter class, transaction behavior, and tests that prove callers can use the same minimal DB interface without silent SQLite fallback.

## Proposed Solution

1. Extend `ServiceConfig` and `entangled.app.main` with explicit backend selection and a Postgres DSN/DSN-file option.
2. Keep SQLite mode explicit for current rollback/development use, but make Postgres mode require a real DSN and fail fast if misconfigured.
3. Add a Postgres adapter module behind the existing database interface with connection-pool lifecycle, dict-like rows, `execute`, `executemany`, `fetchone`, `fetchall`, `fetch_all`, `commit`, `rollback`, `transaction`, and `get_connection`.
4. Map existing `transaction(lock_type, resource_id=...)` calls to transaction-scoped advisory locks in Postgres for compatibility.
5. Provide `RETURNING`/last-insert support primitives needed by the later entity-store port.
6. Update `app.state.init_database` and factory wiring to select the backend without touching schema/entity-store SQL conversion in this child.
7. Add focused adapter/config tests and compile checks.

## Acceptance Criteria

- Entangled can be configured for `sqlite` or `postgres` explicitly.
- Postgres mode can read a DSN from a file path suitable for `/opt/novaic/postgres/secrets/novaic_entangled_dsn`.
- Misconfigured Postgres mode fails before startup rather than falling back to SQLite.
- The Postgres adapter implements the existing DB surface used by Entangled callers.
- Adapter rows are dict-like and `fetchone`/`fetchall` return plain dictionaries/lists of dictionaries.
- Transaction commit/rollback and advisory locking behavior are covered by tests or adapter-level fakes.
- Existing SQLite mode tests still pass.

## Verification Plan

Run targeted Entangled unit tests for config parsing, backend selection, SQLite compatibility, and Postgres adapter contract behavior. Run py_compile across the touched Entangled modules. Do not cut over production or modify `/opt/novaic/start.sh` in this child.

## Risks

- Adding Postgres adapter primitives before full SQL dialect conversion can tempt accidental production use too early.
- Advisory lock key hashing must be deterministic and collision-resistant enough for compatibility.
- psycopg connection/row behavior differs from sqlite3 cursor behavior and may need small compatibility wrappers.

## Assumptions

- Full DDL/query conversion is handled by the next child problem, not by this adapter-boundary child.
- Production Entangled remains SQLite until later preflight and cutover children.
- Test-only fakes are acceptable where a real Postgres instance is unavailable locally.
