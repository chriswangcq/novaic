# Queue Service Staging Startup Attempt Result

## Summary

The api host staging Queue Service startup attempt used the real `novaic-agent-runtime` `main` checkout, the staging Postgres DSN file path, and a loopback-only port. The first import failure was resolved by adding a clean `novaic-common` checkout to the staging layout and starting with the same sibling `PYTHONPATH` boundary used by the project start script.

The service still did not reach `/health` or `/ready`: the Postgres client could not parse/connect with the current staging DSN file because the URI credentials are not safely encoded. The log shows the client trying to resolve `novaic_queue_staging` as a host instead of connecting to the loopback Postgres container endpoint.

## Done

- Confirmed `T113` should use the staging DSN file at `/opt/novaic/queue-staging-postgres/queue-postgres.dsn` without printing its secret contents.
- Reused the clean staging runtime checkout under `/opt/novaic/queue-service-staging/runtime`.
- Added a clean staging `novaic-common` checkout under `/opt/novaic/queue-service-staging/novaic-common`.
- Started Queue Service on `127.0.0.1:19987` with:
  - `NOVAIC_QUEUE_DB_BACKEND=postgres`
  - `NOVAIC_QUEUE_POSTGRES_DSN_FILE=/opt/novaic/queue-staging-postgres/queue-postgres.dsn`
  - `PYTHONPATH=/opt/novaic/queue-service-staging/runtime:/opt/novaic/queue-service-staging/novaic-common`
- Avoided changing production service configuration or public ports.

## Verification

- Runtime checkout evidence: `novaic-agent-runtime` commit `9af254c`.
- Common checkout evidence: `novaic-common` commit `e0cc9df`.
- Import boundary verification: the second startup passed the earlier `ModuleNotFoundError: No module named 'common'` failure and reached Queue Service initialization.
- Startup failure evidence from `/opt/novaic/queue-service-staging/queue-service.log`:
  - Queue Service recognized `backend=postgres`.
  - Queue Service recognized DSN source file `/opt/novaic/queue-staging-postgres/queue-postgres.dsn`.
  - Postgres connection failed with `failed to resolve host 'novaic_queue_staging': [Errno -8] Servname not supported for ai_socktype`.
- `/health` on `http://127.0.0.1:19987/health` did not become reachable during the startup probe.

## Known Gaps

- The DSN file needs to be regenerated in a libpq-safe form, either with URL-encoded credentials or a keyword connection string.
- Queue Service must be restarted after the DSN fix and verified through `/health` and `/ready`.

## Artifacts

- Remote log: `/opt/novaic/queue-service-staging/queue-service.log`.
- Remote pidfile path used for the smoke process: `/opt/novaic/queue-service-staging/queue-service.pid`.
- Staging DSN file path: `/opt/novaic/queue-staging-postgres/queue-postgres.dsn`.
