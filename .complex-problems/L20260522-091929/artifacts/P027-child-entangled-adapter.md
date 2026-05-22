# Implement Entangled Postgres adapter and runtime boundary

## Problem

Entangled currently relies on the SQLite `Database` implementation and `--db-path` runtime wiring. Add an explicit Postgres runtime boundary for Entangled so the rest of the service can use a Postgres-backed DB interface without scattered SQLite assumptions or a silent production fallback.

## Success Criteria

- Entangled has explicit config/runtime selection for Postgres using the existing `novaic_entangled` database.
- Postgres driver dependency and connection-pool adapter are added behind the existing database boundary.
- Adapter preserves dict-like rows, `execute`, `executemany`, `fetchone`, `fetchall`, `fetch_all`, `rowcount`, commit/rollback, transaction context, and `RETURNING` behavior where needed.
- Transaction locking maps existing global/resource lock semantics to Postgres-safe advisory or row locks.
- Production Postgres mode does not silently fall back to SQLite.
- Focused adapter/config tests and compile checks pass.
