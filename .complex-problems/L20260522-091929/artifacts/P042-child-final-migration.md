# Run Final Entangled SQLite To Postgres Migration

## Problem

With writers frozen and rollback files prepared, the final production SQLite snapshot must be imported into clean Postgres database `novaic_entangled` with counts and semantic checks recorded. This belongs under `P042` because production restart must only happen after data has been migrated and verified.

## Success Criteria

- `novaic_entangled` is confirmed clean or safely cleaned according to the migration tool guard.
- `entangled-migrate-postgres` runs against the production SQLite backup/source and production DSN file without printing secrets.
- Migration report shows source/target row counts for all planned tables.
- Sync-version values and subagent transition count/max ID match.
- `entangled_rowid` and sequence reset checks pass for migrated tables.
- The migration report is saved as a redacted ledger artifact.
- No production runtime restart occurs in this child.
