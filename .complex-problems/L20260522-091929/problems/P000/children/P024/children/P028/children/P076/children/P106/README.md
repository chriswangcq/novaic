# Run Queue Service Postgres API Staging Smokes

## Problem

After the staging Postgres target exists, Queue Service must start in Postgres mode and representative Queue APIs must work against the real service runtime, not only unit tests.

## Success Criteria

- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres` against the staging target.
- Health/readiness endpoints pass.
- Task publish/claim/complete/fail or safe retry equivalent passes.
- Saga create/claim/launch/complete/fail or safe equivalent passes.
- Session dispatch/finalize/rebuild or safe equivalent smoke passes.
- Idempotency duplicate/in-progress/completed-result smoke passes.
- DB counts after smokes are recorded with secrets redacted.
