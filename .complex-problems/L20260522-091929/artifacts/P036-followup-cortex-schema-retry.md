# Repair Cortex Postgres schema and complete production cutover

## Problem

The first Cortex production operational cutover attempt failed during migration because production generation values exceed the Postgres `INTEGER` range. Repair the Cortex Postgres operational schema and migration retry behavior, redeploy the fix, rerun the migration, switch Cortex to the Postgres backend, verify the runtime, and remove the active SQLite residue only after the Postgres-backed service is healthy.

## Success Criteria

- Cortex Postgres operational schema uses `BIGINT` for production-sized integer counters and timestamps.
- The migration script's `--replace` path can cleanly recover from a partially created incompatible target schema.
- Remote migration into `novaic_cortex` completes with matching counts for all five operational tables.
- `/opt/novaic/start.sh` starts Cortex with Postgres operational backend flags and a DSN file path.
- Cortex `/health` and `/ready` pass after restart.
- Representative operational read smoke passes after restart.
- No process holds `/opt/novaic/data/cortex/operational.sqlite3`, and the old SQLite file is moved out of the active path only after verification succeeds.
- Rollback note, central SQLite classification note, and local cutover artifact are updated.
