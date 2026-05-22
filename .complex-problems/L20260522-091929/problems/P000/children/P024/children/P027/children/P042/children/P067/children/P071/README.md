# Persist Entangled Postgres Startup Configuration Before SQLite Archival

## Problem

During P067 execution, `/opt/novaic/start.sh` was found to still start Entangled with `--db-path "$DATA_DIR/entangled.db"` and an inline service token. Archiving `/opt/novaic/data/entangled.db*` while this startup path remains would create reboot ambiguity and could relaunch Entangled in SQLite mode or create a fresh SQLite database.

Before moving active-path SQLite files, update the persistent startup configuration so Entangled starts in Postgres mode with file-backed DSN and service-token arguments.

## Success Criteria

- `/opt/novaic/start.sh` starts Entangled with `--db-backend postgres`, `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_dsn`, and `--service-token-file /opt/novaic/postgres/secrets/entangled_production_service_token`.
- `/opt/novaic/start.sh` no longer starts Entangled with `--db-path "$DATA_DIR/entangled.db"` or an inline service token argument.
- The updated startup file is backed up before modification.
- A syntax check or equivalent shell validation passes.
- The currently running Entangled process remains healthy/ready in Postgres mode after the startup-file change.
- The change is recorded in a local ledger artifact without exposing secret values.
