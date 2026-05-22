# T026 Result - Gateway Postgres Storage Implementation

## Summary

Implemented the Gateway Postgres storage path for auth/config state without changing production data, runtime config, or service state. Gateway can now be started with `--db-backend postgres --postgres-dsn-file <path>` and will initialize only the current `users`, `refresh_tokens`, and `config` tables.

## Files Changed

- `novaic-gateway/main_gateway.py`
- `novaic-gateway/gateway/db/access.py`
- `novaic-gateway/gateway/db/postgres.py`
- `novaic-gateway/gateway/db/schema.py`
- `novaic-gateway/gateway/entity/store.py`
- `novaic-gateway/requirements.txt`
- `novaic-gateway/tests/test_gateway_postgres_storage.py`

## Implementation Notes

- Added `PostgresGatewayDatabase`, a small synchronous adapter matching the DB methods used by Gateway auth/config storage.
- Added Postgres DDL for only `users`, `refresh_tokens`, and `config`.
- Added CLI switches:
  - `--db-backend sqlite|postgres`
  - `--postgres-dsn-file <path>`
- Kept DSN material out of process args by using a DSN file path.
- Left production default as SQLite until P030 performs the production migration/cutover.
- Removed SQLite-specific wording from Gateway auth store comments.
- Added `psycopg[binary]` to Gateway requirements.

## Verification

- Ran Gateway tests:
  - `PYTHONPATH=../novaic-common:. python -m pytest tests`
  - result: `33 passed`
- Ran compile/import check:
  - `PYTHONPATH=../novaic-common:. python -m py_compile main_gateway.py gateway/db/access.py gateway/db/postgres.py gateway/db/schema.py gateway/entity/store.py`
  - result: passed

## No-Production-Mutation Statement

This ticket did not change production data, deploy code, switch Gateway runtime config, restart Gateway, or touch `/opt/novaic/data/gateway.db`. Production migration remains P030.
