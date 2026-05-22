# Entangled Postgres Cutover And SQLite Rollback Note

Timestamp: 2026-05-22 20:38 Asia/Shanghai
Host: api.gradievo.com

## Current State

Entangled current state owner is Postgres database `novaic_entangled`. The production runtime listens on `127.0.0.1:19900` and starts with:

- `--db-backend postgres`
- `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_dsn`
- `--service-token-file /opt/novaic/postgres/secrets/entangled_production_service_token`

`/v1/health` and `/v1/ready` returned HTTP 200 with 22 registered entities after the cutover and after SQLite active-path archival.

## SQLite Archive

Cutover archive: `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z`

Moved active-path files:

- `/opt/novaic/data/entangled.db` -> `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled.db.removed-from-active-path-20260522T121320Z` (7106560 bytes)
- `/opt/novaic/data/entangled.db-wal` -> `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled.db-wal.removed-from-active-path-20260522T121320Z` (4169472 bytes)
- `/opt/novaic/data/entangled.db-shm` -> `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled.db-shm.removed-from-active-path-20260522T121320Z` (32768 bytes)

Pre-cutover backups in the same archive include `entangled.db`, `entangled.db-wal`, `entangled.db-shm`, and `entangled.db.sqlite-backup` from the writer-frozen backup phase.

## Smoke Evidence

- Postgres runtime readiness repair report: `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled-production-readiness-repair-report.json`
- Production REST/WebSocket smoke report: `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled-production-smoke-report.json`
- Startup PG config report: `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled-startup-pg-config-report.json`

## Emergency Rollback Sketch

Rollback should only be used if Postgres-mode Entangled is judged unsafe.

1. Stop the Postgres-mode Entangled process on port `19900`.
2. Restore `/opt/novaic/start.sh` from `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/start.sh.before-entangled-pg-*` or edit the Entangled block back to the old SQLite command.
3. Restore a SQLite source to `/opt/novaic/data/entangled.db`; prefer the final moved active-path archive if present, otherwise use `entangled.db.sqlite-backup` from this archive.
4. Restore `entangled.db-wal` and `entangled.db-shm` only if explicitly rolling back to the original hot-copy set; the consistent `.sqlite-backup` file should normally be sufficient as the DB source.
5. Start Entangled with `--db-path /opt/novaic/data/entangled.db` and the service token restored from the operational secret source.
6. Verify `/v1/health`, `/v1/ready`, REST reads, and WebSocket sync before unfreezing writers.

## Notes

The active data path no longer contains `entangled.db*`. Treat all Entangled SQLite files under the cutover archive as rollback-only evidence, not current state.
