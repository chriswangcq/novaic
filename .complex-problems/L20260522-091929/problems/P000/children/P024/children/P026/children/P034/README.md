# Cut Over Cortex Production Operational Store to Postgres

## Problem

After Cortex has a Postgres operational store, production operational state must be backed up, migrated from SQLite to `novaic_cortex`, and Cortex must restart with the Postgres backend.

## Success Criteria

- `/opt/novaic/data/cortex/operational.sqlite3` is backed up before migration.
- All five operational tables are migrated with row-count checks.
- Cortex runtime starts with the Postgres operational backend.
- Cortex `/health` and `/ready` pass after restart.
- Representative operational reads pass after cutover.
- Old operational SQLite is moved or labeled rollback-only.
- Rollback notes and central classification note are updated.
