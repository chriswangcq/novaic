# Persist Entangled Postgres Startup Configuration Before SQLite Archival

## Problem Definition

The live Entangled process is running in Postgres mode, but `/opt/novaic/start.sh` still contains the old SQLite startup command with `--db-path "$DATA_DIR/entangled.db"` and an inline token argument. This must be corrected before active SQLite residue is archived so a future restart does not revert Entangled to SQLite.

## Proposed Solution

Back up `/opt/novaic/start.sh`, replace the Entangled startup block with a Postgres-mode command that uses `/opt/novaic/postgres/secrets/novaic_entangled_dsn` and `/opt/novaic/postgres/secrets/entangled_production_service_token` file arguments, run `bash -n`, and verify the running Entangled process remains healthy/ready. Record a redacted diff/report locally.

## Acceptance Criteria

- `/opt/novaic/start.sh` has a timestamped backup.
- The Entangled startup block uses `--db-backend postgres`.
- The block uses `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_dsn`.
- The block uses `--service-token-file /opt/novaic/postgres/secrets/entangled_production_service_token`.
- The block no longer contains `--db-path "$DATA_DIR/entangled.db"` for Entangled.
- The block no longer passes an inline service token to Entangled.
- `bash -n /opt/novaic/start.sh` passes.
- The currently running Entangled process still reports health/readiness HTTP 200 after the file edit.

## Verification Plan

Use a remote Python text replacement with exact old/new block matching, `bash -n`, grep-based startup block inspection, and final curl checks. Do not print secret contents.

## Risks

- A broad text replacement could affect another service block in `start.sh`.
- Editing startup config does not restart services immediately, so verification must distinguish persistent config from current runtime health.

## Assumptions

- The current direct PG-mode Entangled process should remain running while the startup file is edited.
- The secret files already exist and are root-readable.
