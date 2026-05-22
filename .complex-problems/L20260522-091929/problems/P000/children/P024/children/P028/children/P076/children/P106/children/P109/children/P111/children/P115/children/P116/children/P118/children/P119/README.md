# Fix Queue Staging DSN And Restart Service

## Problem

Queue Service on `api.gradievo.com` cannot complete startup against the staging Postgres DSN file because the current DSN URI is not safely parseable when credentials contain reserved URL characters. The DSN source must remain a file, but its contents need to be regenerated without exposing the secret, then Queue Service must be restarted on the loopback staging port.

## Success Criteria

- `/opt/novaic/queue-staging-postgres/queue-postgres.dsn` is regenerated in a libpq-safe form without printing or committing the secret.
- The existing `novaic-queue-staging-postgres` Docker container remains healthy and reachable on its intended loopback port.
- Queue Service starts on `api.gradievo.com` using `NOVAIC_QUEUE_POSTGRES_DSN_FILE=/opt/novaic/queue-staging-postgres/queue-postgres.dsn`.
- `http://127.0.0.1:19987/health` passes and reports the Postgres backend.
- `http://127.0.0.1:19987/ready` passes.
- Production service configuration and public ports are not modified.
