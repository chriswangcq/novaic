# Execute Gateway Production Cutover

## Problem Definition

Gateway production is ready for cutover from SQLite to Postgres. P031 verified the target DB, DSN file, dependency readiness, and source row counts. This ticket performs the actual backup, deploy, data migration, runtime switch, restart, smoke tests, and documentation update.

## Proposed Solution

1. Back up `/opt/novaic/data/gateway.db`, `start.sh`, and changed Gateway code files.
2. Deploy the Gateway Postgres storage code and migration script.
3. Compile-check deployed Gateway files.
4. Run the migration script with `--replace` into `novaic_gateway`.
5. Patch `/opt/novaic/start.sh` to pass:
   - `--db-backend postgres`
   - `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_gateway_dsn`
6. Restart the `novaic` service.
7. Verify Gateway health, auth negative-login smoke, Postgres counts, process args, and no active SQLite writes.
8. Append central classification and rollback notes.

## Acceptance Criteria

- Gateway process starts with Postgres backend flags.
- `novaic_gateway` contains `users=1`, `refresh_tokens=26`, and `config=5`.
- Gateway `/api/health` passes after restart.
- A non-mutating auth smoke returns expected unauthorized status rather than a DB/server error.
- `/opt/novaic/data/gateway.db` is no longer held by the running Gateway process.
- Backup and rollback paths are recorded.
- Central SQLite classification note marks Gateway SQLite as rollback-only/non-current.

## Verification Plan

- Compare source and target counts.
- Check `systemctl is-active novaic`.
- Check Gateway process args with secrets redacted.
- Run `/api/health`.
- Run negative `/auth/login` smoke.
- Run `lsof` against `gateway.db`.
- Check central note tail after documentation append.

## Risks

- Restarting `novaic` restarts all backend services, not only Gateway.
- Bad startup patch can prevent Gateway from binding.
- If the migration script fails mid-run, target DB should roll back and old SQLite runtime remains available until startup is patched/restarted.

## Assumptions

- P031 preflight evidence is still current enough for execution.
- The old SQLite file remains available for rollback.
