# Cortex Production Operational Store Cutover

## Problem Definition

Cortex has a Postgres operational store implementation, but production still uses `/opt/novaic/data/cortex/operational.sqlite3`. Production must be backed up, migrated to `novaic_cortex`, restarted with the Postgres backend, and verified.

## Proposed Solution

1. Preflight remote Cortex runtime, health/readiness, source row counts, target DB connectivity, DSN file, and dependency readiness.
2. Back up `operational.sqlite3`, `start.sh`, and changed Cortex code files.
3. Deploy Cortex Postgres store code and migration script.
4. Compile-check deployed Cortex files.
5. Run migration script with `--replace`.
6. Patch `/opt/novaic/start.sh` to pass:
   - `--operational-store-backend postgres`
   - `--operational-postgres-dsn-file /opt/novaic/postgres/secrets/novaic_cortex_dsn`
7. Restart `novaic`.
8. Verify Cortex `/health`, `/ready`, row counts, process args, representative operational endpoints, and old SQLite active-path cleanup.
9. Update rollback notes and central classification.

## Acceptance Criteria

- Cortex process starts with Postgres operational backend flags.
- `novaic_cortex` contains all five operational tables with matching row counts.
- Cortex `/health` and `/ready` pass after restart.
- Representative operational read endpoint passes.
- Old `operational.sqlite3` is not active and is moved or labeled rollback-only.
- Rollback archive and central classification note are updated.

## Verification Plan

- Compare source and target counts for all five tables.
- Check process args with secret paths redacted.
- Check Cortex health/readiness.
- Check operational read endpoint such as scope events or active-stack status.
- Check no active process holds the SQLite file before active-path cleanup.

## Risks

- Restarting `novaic` restarts all backend services.
- Cortex control-plane projections affect active runtime behavior.
- If Postgres dependency or DSN is wrong, Cortex may fail at startup.

## Assumptions

- P033 code has been locally tested.
- `novaic_cortex` DB/user exists in the local Postgres container.
