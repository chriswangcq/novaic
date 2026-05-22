# T029 Result - Gateway Production Cutover

## Summary

Gateway production auth/config state was cut over from SQLite to Postgres. Gateway now starts with the Postgres backend, `novaic_gateway` has the expected row counts, Gateway health and auth smoke checks pass, and the old active-path SQLite file has been moved into the rollback archive.

## Artifact

- `.complex-problems/L20260522-091929/artifacts/gateway-production-cutover.md`

## Production Changes

- Deployed Gateway Postgres storage code and migration script to `/opt/novaic/services/novaic-gateway`.
- Migrated `users`, `refresh_tokens`, and `config` from `/opt/novaic/data/gateway.db` to `novaic_gateway`.
- Patched `/opt/novaic/start.sh` so Gateway starts with:
  - `--db-backend postgres`
  - `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_gateway_dsn`
- Restarted `novaic`.
- Moved `/opt/novaic/data/gateway.db` out of the active data path after verifying no process held it.
- Updated central SQLite classification and rollback notes.

## Verification

- Migration counts matched:
  - source `users=1`, `refresh_tokens=26`, `config=5`
  - target `users=1`, `refresh_tokens=26`, `config=5`
- `systemctl is-active novaic`: `active`
- Gateway process includes Postgres backend flags.
- Gateway `/api/health`: healthy.
- Negative auth login smoke returned `401`, not a DB/server error.
- No active `gateway.db*` file remains under `/opt/novaic/data`.
- Other restarted services reported healthy/ready.

## Rollback

Rollback archive:

- `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z`

Rollback note:

- `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z/GATEWAY_POSTGRES_CUTOVER.md`

## Residual Risk

- Remote Gateway venv `pip` remains incomplete, though `psycopg` is importable and Gateway is running. Future dependency hygiene should repair/recreate that venv rather than relying on `--target` installs.
