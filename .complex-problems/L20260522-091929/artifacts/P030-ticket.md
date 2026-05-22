# Gateway Production Cutover to Postgres

## Problem Definition

Gateway now has a local Postgres storage implementation, but production still runs on `/opt/novaic/data/gateway.db`. Production must be backed up, migrated to `novaic_gateway`, deployed with the new code/dependencies, and restarted with Postgres runtime config.

## Proposed Solution

Split production cutover into preflight/rehearsal and execution:

1. Preflight/rehearsal
   - Inspect remote Gateway runtime, dependency environment, and Postgres secret file layout.
   - Prepare a Gateway DSN file with restricted permissions.
   - Prepare an idempotent migration script or SQL path for `users`, `refresh_tokens`, and `config`.
   - Verify row counts and dry-run behavior without switching Gateway.
2. Production execution
   - Back up `/opt/novaic/data/gateway.db`.
   - Deploy the Gateway code changes and install `psycopg`.
   - Migrate data to `novaic_gateway`.
   - Update runtime startup flags to `--db-backend postgres --postgres-dsn-file <path>`.
   - Restart Gateway stack and verify health/auth/config behavior.
   - Update central SQLite classification and rollback notes.

## Acceptance Criteria

- Gateway production starts with Postgres backend.
- `users`, `refresh_tokens`, and `config` row counts match expected migration counts.
- Gateway health passes after restart.
- Representative auth/config smoke checks pass without exposing secrets.
- `/opt/novaic/data/gateway.db` is retained only as rollback evidence.
- Rollback path and central classification note are updated.

## Verification Plan

- Run remote preflight commands before mutation.
- Capture backup and row counts before data copy.
- Verify Postgres row counts after data copy.
- Verify Gateway process args show Postgres backend with DSN file path only.
- Verify no active process holds or writes `gateway.db` after cutover.
- Verify Gateway `/api/health` after restart.

## Risks

- Missing `psycopg` in the remote venv can prevent Gateway startup.
- Bad DSN file permissions can leak DB credentials.
- Refresh-token row copy must preserve token strings and expiration text exactly.
- Restarting the shared stack can briefly interrupt user traffic.

## Assumptions

- The current remote deployment path is `/opt/novaic/services/novaic-gateway`.
- The `novaic_gateway` database/user already exists in the local Postgres container.
- If a blocking preflight issue appears, execution should stop before restart/cutover.
