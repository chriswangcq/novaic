# Persist Entangled Postgres Startup Configuration Before SQLite Archival Check

## Summary

P071 is successful. Result `R066` backed up and updated `/opt/novaic/start.sh` so future Entangled starts use Postgres mode with file-backed secret arguments instead of the old SQLite `entangled.db` path.

## Evidence

- Backup exists at `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/start.sh.before-entangled-pg-20260522T121130Z`.
- Startup config report records `block_has_db_backend_postgres: true`.
- Startup config report records `block_has_postgres_dsn_file: true`.
- Startup config report records `block_has_service_token_file: true`.
- Startup config report records `block_has_sqlite_db_path: false`.
- Startup config report records `block_has_inline_service_token: false`.
- `bash -n /opt/novaic/start.sh` passed.
- Current Entangled health/readiness remained HTTP 200 with 22 entities after the edit.

## Criteria Map

- Start with `--db-backend postgres`: satisfied.
- Use `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_dsn`: satisfied.
- Use `--service-token-file /opt/novaic/postgres/secrets/entangled_production_service_token`: satisfied.
- No `--db-path "$DATA_DIR/entangled.db"` in Entangled block: satisfied.
- No inline service token argument in Entangled block: satisfied.
- Backup before modification: satisfied.
- Shell syntax validation passes: satisfied.
- Running Entangled remains healthy/ready: satisfied.

## Execution Map

- T070 executed one remote startup-file edit.
- R066 recorded backup path, config diff evidence, syntax check, and runtime health evidence.
- No runtime child problem was needed.

## Stress Test

- The exact reboot ambiguity was checked by inspecting the Entangled startup block after edit, not only the currently running process.
- `bash -n` guards against syntax breakage in the service launcher.

## Residual Risk

- P071 did not run a full stop/start cycle from `start.sh`. That is acceptable here because the purpose was to remove the known SQLite startup path before archival; full multi-service restart remains a separate operational choice.

## Result IDs

- R066
