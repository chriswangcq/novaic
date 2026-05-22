# Cortex production Postgres cutover

## Summary

Cortex production operational state is now running on Postgres database `novaic_cortex`. The previous active SQLite file was moved out of `/opt/novaic/data/cortex` after health/readiness, row-count, read-path, and no-open-file checks passed.

## Local Changes

- `novaic-cortex/novaic_cortex/operational_store.py`
  - Added Postgres operational-store support during P033.
  - Widened production-sized Postgres counters to `BIGINT`.
  - Added `backend_name` for accurate operational-read diagnostics.
- `novaic-cortex/novaic_cortex/api.py`
  - Deployed the matching API helper expected by `main_cortex.py`.
  - Updated `/v1/scope/history` to report the actual store backend instead of a stale SQLite label.
- `novaic-cortex/scripts/migrate_cortex_operational_sqlite_to_postgres.py`
  - Changed `--replace` to drop and recreate target operational tables before loading rows.
- `/opt/novaic/start.sh`
  - Added `--cortex-api-url "$CORTEX_URL"`.
  - Added `--operational-store-backend postgres`.
  - Added `--operational-postgres-dsn-file /opt/novaic/postgres/secrets/novaic_cortex_dsn`.

## Backup

- Backup archive: `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z`
- Backup files:
  - `operational.sqlite3`
  - `operational.sqlite3.sha256`
  - `source-counts.txt`
  - `start.sh.before`
  - `cortex-code-before.tar`

## Migration

The repaired migration completed with matching counts:

- `cortex_operational_meta=1`
- `scope_events=25`
- `scope_projection=26`
- `active_stack_projection=5`
- `payload_manifest=90`

Production-sized schema columns verified as `bigint`:

- `scope_events.generation`
- `scope_projection.generation`
- `scope_projection.stack_depth`
- `active_stack_projection.generation`

## Runtime Verification

- `systemctl restart novaic` completed and `systemctl is-active novaic` returned `active`.
- Cortex `/health` returned `{"status":"ok","service":"cortex"}`.
- Cortex `/ready` returned `status=ok` with registry, blob service, and Redis scope lock checks ok.
- Cortex process args include `--operational-store-backend postgres` and the Postgres DSN file flag.
- Representative `/v1/scope/history` smoke returned HTTP 200, `history_count=1`, and `history_backend=postgres`.
- `lsof /opt/novaic/data/cortex/operational.sqlite3` returned no holder before cleanup.

## Cleanup

- Moved active-path SQLite file to `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/operational.sqlite3.removed-from-data-dir`.
- Verified no `operational.sqlite3*` files remain under `/opt/novaic/data/cortex`.
- Appended the Cortex Postgres cutover note to `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`.
- Wrote rollback note `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/CORTEX_POSTGRES_CUTOVER.md`.

## Residual Risk

- The Cortex CLI still accepts `--operational-sqlite-path` because the same argument remains required for SQLite compatibility and existing parser shape; the runtime backend is Postgres.
- Queue and Entangled remain on SQLite and are separate pending cutovers.
