# P032 Success Check

## Summary

P032 is solved. `R026` cut Gateway production auth/config state over to Postgres, verified health and row counts, and moved the old SQLite file out of the active data path into rollback-only archive.

## Evidence

- `R026` records the production cutover result.
- `.complex-problems/L20260522-091929/artifacts/gateway-production-cutover.md` exists.
- Gateway process includes `--db-backend postgres`.
- Postgres `novaic_gateway` counts are `users=1`, `refresh_tokens=26`, `config=5`.
- Gateway `/api/health` is healthy.
- Auth negative-login smoke returns `401`, proving the auth route reaches storage without DB/server error.
- `/opt/novaic/data` has no `gateway.db*` files after active-path cleanup.
- Rollback archive exists at `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z`.
- Central SQLite classification note includes the Gateway Postgres cutover and active-path cleanup addendum.

## Criteria Map

- Gateway process starts with Postgres backend flags: satisfied.
- Target row counts match expected migration counts: satisfied.
- Gateway health passes after restart: satisfied.
- Non-mutating auth smoke passes: satisfied.
- No active process writes to `gateway.db`: satisfied; no active file remains under `/opt/novaic/data`.
- Backup and rollback paths recorded: satisfied.
- Central classification note updated: satisfied.

## Execution Map

- Ticket `T029` was classified as `one_go`.
- Result `R026` produced one durable cutover artifact.
- No child problem was needed for P032.

## Stress Test

- A bad DSN format and missing dependency were caught in P031 before restart.
- Migration failed-safe by checking source and target row counts before runtime switch.
- The active-path SQLite file was moved only after Gateway was healthy on Postgres and `lsof` showed no holder.
- Other services were checked after the shared `novaic` restart.

## Residual Risk

- Remote Gateway venv dependency management should be cleaned later because venv `pip` is incomplete, though `psycopg` is currently importable and Gateway is healthy.

## Result IDs

- R026
