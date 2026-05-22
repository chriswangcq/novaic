# Confirm Queue API Staging Target And Run Smokes

## Problem

P106 cannot be closed until Queue Service is started against a confirmed non-production Postgres target and representative API smokes are executed. The current environment has no `NOVAIC_QUEUE_POSTGRES_DSN_FILE` or `NOVAIC_QUEUE_POSTGRES_DSN`, so the follow-up must either acquire/confirm that target and run the smokes, or remain explicitly blocked without touching production.

## Success Criteria

- A non-production Queue Postgres target is confirmed before any service startup or database write.
- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres` against that target.
- Health/readiness endpoints pass.
- Task publish/claim/complete/fail or safe retry equivalent passes.
- Saga create/claim/launch/complete/fail or safe equivalent passes.
- Session dispatch/finalize/rebuild or safe equivalent passes.
- Idempotency duplicate/in-progress/completed-result smoke passes.
- Post-smoke DB counts are recorded with DSNs/secrets redacted.
