# Repair and retry Cortex production Postgres cutover

## Problem Definition

The Cortex production operational-store migration failed because the first Postgres schema used `INTEGER` for generation counters that production SQLite already stores as millisecond-scale values. Cortex was not restarted and remains healthy on SQLite. The repair must adjust the schema and migration retry path, then complete the cutover and clean the old active SQLite store only after verification succeeds.

## Proposed Solution

1. Patch the local Cortex Postgres operational schema so all production-sized integer counters and timestamps use `BIGINT`.
2. Patch the Cortex migration script so `--replace` drops and recreates target operational tables before loading rows, allowing recovery from the incompatible partial schema.
3. Run focused local Cortex tests and compile checks.
4. Redeploy the repaired Cortex files and migration script to `/opt/novaic/services/novaic-cortex`.
5. Compile-check the remote files.
6. Rerun the production migration into `novaic_cortex` with `--replace`.
7. Patch `/opt/novaic/start.sh` to start Cortex with the Postgres operational backend and DSN file.
8. Restart `novaic` and verify Cortex health, readiness, process args, Postgres row counts, and representative operational reads.
9. Confirm the old SQLite file is no longer open, then move it out of `/opt/novaic/data/cortex`.
10. Update the rollback note, central SQLite classification note, and local cutover artifact.

## Acceptance Criteria

- Cortex Postgres schema is safe for production-sized generation/timestamp values.
- `--replace` can recover from the previous failed target schema.
- Local tests and py_compile pass for the touched Cortex files.
- Remote migration completes and target counts match source counts for all five operational tables.
- Cortex restarts with Postgres operational backend flags.
- Cortex `/health` and `/ready` pass after restart.
- Representative operational read smoke passes after restart.
- No active `operational.sqlite3*` remains under `/opt/novaic/data/cortex` after safe cleanup.
- Rollback and classification notes describe the completed cutover and cleanup.

## Verification Plan

Use local pytest and py_compile before redeploying. On the server, compile-check deployed files, run the migration, compare row counts, restart `novaic`, inspect redacted process args, call `/health` and `/ready`, run an operational read smoke, check `lsof` for the old SQLite path, verify active-path cleanup, and record the final evidence in a local artifact.

## Risks

- Restarting `novaic` restarts multiple backend services.
- A malformed `/opt/novaic/start.sh` patch could prevent Cortex startup.
- Removing the old SQLite file before proving the Postgres runtime would weaken rollback.

## Assumptions

- The P035 preflight remains valid except for the now-known schema width issue.
- The backup archive from the first P036 attempt remains the rollback anchor.
- JSON text preservation from P033 remains the desired first-cutover behavior.
