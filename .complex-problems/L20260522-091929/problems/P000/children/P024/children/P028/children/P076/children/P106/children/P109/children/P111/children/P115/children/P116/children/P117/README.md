# Supply Non-Production Queue Postgres DSN

## Problem

Queue Service runtime smoke validation cannot proceed until a confirmed non-production Queue Postgres DSN or DSN file is available to the runner. This follow-up should close the external test-environment prerequisite before attempting service startup again.

## Success Criteria

- A non-production Queue Postgres target is supplied via `NOVAIC_QUEUE_POSTGRES_DSN_FILE` or `NOVAIC_QUEUE_POSTGRES_DSN`.
- The target is confirmed staging/test/non-production before any write.
- DSNs/secrets are not printed into artifacts.
- Queue Service startup can be retried with `NOVAIC_QUEUE_DB_BACKEND=postgres`.
