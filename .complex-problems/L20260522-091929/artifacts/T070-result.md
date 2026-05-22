# Persist Entangled Postgres Startup Configuration Before SQLite Archival Result

## Summary

Updated `/opt/novaic/start.sh` so the persistent Entangled startup path uses Postgres mode with file-backed DSN and service-token arguments. The old SQLite `--db-path "$DATA_DIR/entangled.db"` and inline `--service-token "$JWT_SECRET"` arguments were removed from the Entangled startup block.

## Done

- Backed up `/opt/novaic/start.sh` to `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/start.sh.before-entangled-pg-20260522T121130Z`.
- Replaced the Entangled startup block with `--db-backend postgres`.
- Added `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_dsn`.
- Added `--service-token-file /opt/novaic/postgres/secrets/entangled_production_service_token`.
- Ran `bash -n /opt/novaic/start.sh`.
- Verified the currently running Entangled process still returns health/readiness HTTP 200.

## Verification

- Startup config report records `bash_n_ok: true`.
- Startup config report records `block_has_db_backend_postgres: true`.
- Startup config report records `block_has_postgres_dsn_file: true`.
- Startup config report records `block_has_service_token_file: true`.
- Startup config report records `block_has_sqlite_db_path: false`.
- Startup config report records `block_has_inline_service_token: false`.
- `/v1/health` and `/v1/ready` returned HTTP 200 with 22 entities after the file edit.

## Known Gaps

- This ticket did not restart all services from `start.sh`; it only made the persistent startup configuration safe for future restarts.
- SQLite active-path archival remains to be completed by parent P067.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-startup-pg-config-report.json`
- `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/entangled-startup-pg-config-report.json`
