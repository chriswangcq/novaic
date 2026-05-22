# T033 Result - Cortex Production Cutover Preflight

## Summary

Completed Cortex production cutover preflight. Cortex remains on SQLite, but the Postgres target is reachable, the DSN file is prepared with restrictive permissions, `psycopg` is available in the Cortex remote venv, source counts are captured, and a migration script is prepared for P036.

## Artifact

- `.complex-problems/L20260522-091929/artifacts/cortex-production-preflight.md`

## Preflight Evidence

- Current Cortex process still uses `--operational-sqlite-path`.
- Cortex readiness is ok.
- Source SQLite counts:
  - `cortex_operational_meta=1`
  - `scope_events=25`
  - `scope_projection=26`
  - `active_stack_projection=5`
  - `payload_manifest=90`
- Target Postgres connectivity:
  - `cortex_dsn=ok db=novaic_cortex user=novaic_cortex`
- Target public tables:
  - `<none>`
- DSN file:
  - `/opt/novaic/postgres/secrets/novaic_cortex_dsn`
  - mode `600`, owner `root:root`
- Remote Cortex venv dependency:
  - `cortex_venv_psycopg=ok:3.3.4`
- Migration script prepared:
  - `novaic-cortex/scripts/migrate_cortex_operational_sqlite_to_postgres.py`

## No-Cutover Statement

This ticket did not restart Cortex, deploy the new code, copy production rows, or switch runtime backend. P036 remains the production execution step.
