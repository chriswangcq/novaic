# Cut Over Gateway Production Auth Config to Postgres

## Problem

After Gateway has a Postgres storage path, production Gateway data must be backed up, migrated from `/opt/novaic/data/gateway.db` to `novaic_gateway`, and the runtime must be switched so active auth/config state no longer uses SQLite.

## Success Criteria

- `/opt/novaic/data/gateway.db` is backed up before mutation.
- `users`, `refresh_tokens`, and `config` are migrated to `novaic_gateway` with row-count checks.
- Gateway runtime is switched to Postgres and service health passes.
- Representative auth/config smoke checks pass after cutover.
- No active SQLite writes to `gateway.db` occur after cutover.
- The central SQLite classification note marks `gateway.db` rollback-only/non-current.
- Rollback steps and snapshot location are recorded.
