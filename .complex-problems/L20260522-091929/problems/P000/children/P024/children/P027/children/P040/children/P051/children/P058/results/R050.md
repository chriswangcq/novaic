# Entangled Postgres Mode REST Staging Runtime Result

## Summary

`T054` successfully started a non-production Entangled staging process in Postgres mode on `api.gradievo.com:19910`, registered a minimal REST-smoke schema, verified health/readiness, confirmed no active SQLite file handles, and wrote a redacted runtime report. The staging process is intentionally left running for the next REST smoke child.

## Done

- Backed up the remote Entangled package before syncing local Postgres-capable Entangled code.
- Synced the updated Entangled package to `/opt/novaic/services/Entangled/packages/server-python/entangled`.
- Added missing `psycopg_pool` into the remote venv by unpacking the official pure-Python wheel because remote pip is partially broken.
- Added local and remote support for `--service-token-file` so staging auth does not expose a token in process args.
- Started Entangled with:
  - `--db-backend postgres`
  - staging DSN file
  - staging service-token file
  - loopback port `19910`
- Registered `rest-smoke-events` schema through `/v1/schema/register`.
- Verified `/v1/health` and `/v1/ready` returned success.
- Verified no `/opt/novaic/data/entangled.db*` file handles for the staging process.
- Wrote `.complex-problems/L20260522-091929/artifacts/entangled-pg-mode-rest-staging-runtime-report.json`.

## Verification

- Remote `/v1/health`: HTTP 200, status `ok`, 1 entity.
- Remote `/v1/ready`: HTTP 200, status `ready`, no missing entities.
- Remote process args show Postgres mode and secret-file paths, not raw DSN/token values.
- Remote `lsof` check for active SQLite files returned empty.
- Remote log shows Postgres connection initialized, sync versions loaded, schema registered, and ready HTTP 200.
- Local full Entangled pytest after `--service-token-file` change: 124 passed.

## Known Gaps

- REST mutation smokes are not run in this ticket; `P059` owns them.
- The staging process is still running intentionally for `P059` and should be stopped afterward.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-pg-mode-rest-staging-runtime-report.json`
- `Entangled/packages/server-python/entangled/app/main.py`
