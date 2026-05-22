# Implement Gateway Postgres Auth Config Cutover

## Problem

Gateway still owns active auth/config state in `/opt/novaic/data/gateway.db`. It should be migrated to the existing `novaic_gateway` Postgres database without carrying retired zero-row Gateway tables or maintaining production SQLite fallback logic.

## Success Criteria

- Gateway has a Postgres-backed production storage path for `users`, `refresh_tokens`, and `config`.
- Retired zero-row Gateway tables are not recreated in Postgres.
- Existing Gateway SQLite state is backed up and migrated with row-count checks.
- Gateway runtime config is switched to Postgres and health/auth smoke checks pass.
- Gateway no longer writes active state to `/opt/novaic/data/gateway.db`.
- The old SQLite file is retained only as rollback evidence and documented in the central classification note.
