# Start Queue Service On Api With Staging DSN

## Problem

The staging Queue Postgres DSN now exists on `api.gradievo.com`, but Queue Service still needs to be started against it and health/readiness verified. This follow-up should run the service on the api host or an equivalent safe remote runner using the staging DSN file.

## Success Criteria

- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
- Queue Service uses `/opt/novaic/queue-staging-postgres/queue-postgres.dsn`.
- Startup evidence proves the active backend is Postgres.
- Health/readiness endpoints pass.
- DSNs/secrets are redacted from artifacts.
