# Execute Entangled production Postgres cutover

## Problem

After implementation, staging validation, and preflight, execute the production Entangled cutover from `/opt/novaic/data/entangled.db` to Postgres `novaic_entangled` in a writer-free window, then verify runtime behavior and clean the active SQLite residue.

## Success Criteria

- Production Entangled SQLite files and runtime config are backed up before migration.
- Upstream writers are stopped or frozen before final export.
- Final migration into `novaic_entangled` completes with matching row counts, sync-version values, transition max IDs, and representative semantic checks.
- Entangled starts in Postgres mode with no active SQLite writer.
- Health/readiness, representative REST reads/writes, and WebSocket sync smoke checks pass after restart.
- No process holds `/opt/novaic/data/entangled.db*` after successful cutover.
- Old SQLite files are moved out of the active path only after verification succeeds.
- Rollback note and central SQLite classification note are updated.
