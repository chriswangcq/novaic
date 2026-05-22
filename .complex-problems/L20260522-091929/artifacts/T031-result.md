# T031 Result - Cortex Postgres Operational Store Implementation

## Summary

Implemented a Cortex Postgres operational store path without changing production data or runtime configuration. The implementation covers all five operational tables, adds runtime backend flags, and provides a migration script for the production cutover ticket.

## Files Changed

- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/novaic_cortex/registry.py`
- `novaic-cortex/novaic_cortex/main_cortex.py`
- `novaic-cortex/requirements.txt`
- `novaic-cortex/scripts/migrate_cortex_operational_sqlite_to_postgres.py`
- `novaic-cortex/tests/test_operational_postgres_store.py`

## Implementation Notes

- Added `OperationalPostgresStore` with a small connection wrapper that converts existing qmark placeholders to psycopg placeholders.
- Added Postgres DDL for all five operational tables:
  - `cortex_operational_meta`
  - `scope_events`
  - `scope_projection`
  - `active_stack_projection`
  - `payload_manifest`
- Kept JSON payload columns as text for first cutover to preserve existing string-based idempotency comparisons and API output behavior.
- Added `--operational-store-backend sqlite|postgres` and `--operational-postgres-dsn-file` runtime flags.
- Added migration script for P034.
- Added `psycopg[binary]` to Cortex requirements.

## Verification

- Ran targeted tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-common:../novaic-sandbox-sdk:. python -m pytest tests/test_operational_store.py tests/test_operational_postgres_store.py tests/test_workspace_registry_dependencies.py`
  - result: `15 passed`
- Ran compile check:
  - `python -m py_compile novaic_cortex/operational_store.py novaic_cortex/registry.py novaic_cortex/main_cortex.py scripts/migrate_cortex_operational_sqlite_to_postgres.py`
  - result: passed

## No-Production-Mutation Statement

This ticket did not deploy Cortex code, migrate production data, alter `/opt/novaic/data/cortex/operational.sqlite3`, restart Cortex, or switch runtime backend. Production cutover remains P034.
