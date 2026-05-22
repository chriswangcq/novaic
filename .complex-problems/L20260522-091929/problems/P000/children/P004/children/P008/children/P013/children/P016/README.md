# Map Session Outbox and Idempotency Postgres Replay Semantics

## Problem

Session coordination, durable outboxes, and idempotency ledgers are the replay-safety layer for Queue. The current SQLite implementation relies on one local transaction to append input/session events, upsert session state, create outbox rows, publish effects, mark outbox rows, and guard idempotent task side effects. Before implementation, these guarantees must be translated into Postgres behavior without losing inputs, double-publishing effects, or changing duplicate idempotency-key behavior.

This belongs under T010 because outbox/idempotency correctness is independent from task/saga candidate claiming and needs separate replay-focused validation.

## Success Criteria

- Session dispatch, buffering, attach, suspected-dead observation, session-ended, pending projection, event consumption, and rebuild semantics are mapped to concrete Postgres transaction patterns.
- Session, saga, task, and worker lease outbox pending selection, publish/ack, failure retry, and dead-letter behavior are mapped to Postgres-safe row selection and update rules.
- Idempotency acquire, completed-result return, in-progress contention, lease expiry, complete, and release behavior are mapped with unique constraints and API-compatible conflict handling.
- Pending live outbox rows identified in P012 have a stated migration/replay requirement that P014 can use.
- Crash windows are explicitly covered: publish succeeds before ack, ack races with worker retry, duplicate idempotency key arrives during in-progress work, and session input arrives during finalization.
- Any ambiguous replay behavior is listed as an implementation blocker.
