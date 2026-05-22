# Validate Queue Postgres Mode In Staging

## Problem

Before production cutover, Queue Postgres mode must be exercised with the queue service, workers, outbox workers, and representative APIs against a non-production Postgres target. Unit tests alone cannot prove worker claim/recover/outbox/idempotency behavior under an actual service runtime.

## Success Criteria

- A staging/test Queue Postgres database is prepared without touching production queue data.
- Queue service starts in Postgres mode and reports healthy/ready.
- Representative task publish/claim/complete/retry or safe equivalents pass.
- Representative saga/session/outbox/idempotency smokes pass.
- Worker/outbox processes can run against Postgres mode without SQLite file holders.
- Staging report records commands, checks, counts, and secret redaction.
