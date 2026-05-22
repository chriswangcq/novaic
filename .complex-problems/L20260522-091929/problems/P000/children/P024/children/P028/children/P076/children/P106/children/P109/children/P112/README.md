# Run Queue Service API Smokes

## Problem

With Queue Service running in Postgres mode, representative Queue APIs must be exercised against the real service runtime. This child belongs under T106 because API behavior failures should be diagnosed separately from startup and database target setup.

## Success Criteria

- Health/readiness smoke passes.
- Task publish/claim/complete/fail or safe retry equivalent passes.
- Saga create/claim/launch/complete/fail or safe equivalent passes.
- Session dispatch/finalize/rebuild or safe equivalent passes.
- Idempotency duplicate/in-progress/completed-result smoke passes.
- Each skipped operation has an explicit safety or environment reason.
