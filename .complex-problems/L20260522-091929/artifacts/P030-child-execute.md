# Execute Gateway Production Cutover

## Problem

After preflight succeeds, Gateway production must be backed up, migrated to `novaic_gateway`, deployed with the new storage code/dependency, restarted with the Postgres backend, and verified.

## Success Criteria

- `/opt/novaic/data/gateway.db` backup is created before migration.
- Gateway code/dependencies supporting Postgres are deployed.
- `users`, `refresh_tokens`, and `config` are migrated with row-count checks.
- Gateway startup uses `--db-backend postgres --postgres-dsn-file <path>`.
- Gateway health and representative auth/config smoke checks pass after restart.
- No active process writes to `gateway.db` after cutover.
- Central classification note and rollback notes are updated.
