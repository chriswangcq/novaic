# Start Queue Service After Staging DSN Is Supplied

## Problem

P115 cannot close until a confirmed non-production Queue Postgres target is supplied to the runner and Queue Service starts in Postgres mode. The startup default code path is now clean, but the environment prerequisite is still missing.

## Success Criteria

- A confirmed non-production Queue Postgres DSN or DSN file is supplied.
- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
- Startup evidence proves the active backend is Postgres.
- Health/readiness endpoints pass.
- DSNs/secrets are redacted from all artifacts.
