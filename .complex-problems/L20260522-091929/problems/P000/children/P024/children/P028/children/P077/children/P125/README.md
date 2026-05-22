# Restart Production Queue Services In Postgres Mode

## Problem

After migration, Queue Service and related worker/outbox processes must be restarted in Postgres mode with the production credential source, and must not resume using `/opt/novaic/data/queue.db`.

## Success Criteria

- Queue Service is restarted with `NOVAIC_QUEUE_DB_BACKEND=postgres` and redacted production credential configuration.
- Task worker, saga worker, session outbox worker, saga outbox worker, and relevant scheduler/health processes are restarted or explicitly declared out of scope.
- `/health` and `/ready` pass after restart.
- Runtime process commands show Postgres mode or Queue Service URL usage as appropriate.
- No process opens `/opt/novaic/data/queue.db` after restart.
