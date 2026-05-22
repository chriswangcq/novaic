# Execute Cortex Production Operational Cutover

## Problem

After preflight succeeds, Cortex production operational state must be backed up, migrated to `novaic_cortex`, and Cortex must restart with Postgres operational backend.

## Success Criteria

- `operational.sqlite3` backup exists before migration.
- All five operational tables migrate with matching row counts.
- Cortex startup uses Postgres operational backend and DSN file path.
- Cortex `/health` and `/ready` pass after restart.
- Representative operational read smoke passes.
- Old SQLite active path is removed or documented rollback-only.
- Rollback notes and central classification note are updated.
