# Check: Durable Outbox Drain Semantics Succeed

## Summary

`R087` satisfies `P094`. Postgres pending outbox selection now claims rows with `FOR UPDATE SKIP LOCKED` inside an explicit transaction, and session/saga drainers keep select, publish, and ack/failure updates inside Postgres-only outbox drain transactions. SQLite behavior remains compatible with existing outbox regressions.

## Evidence

- `FsmSqliteStore.list_pending_outbox(...)` appends `FOR UPDATE SKIP LOCKED` in Postgres and fails fast outside explicit transactions.
- `SessionOutboxDispatcher.drain_pending(...)` uses a Postgres-only `session_outbox` transaction before calling the inner drain loop.
- `SagaOrchestrator.drain_pending_effects(...)` uses a Postgres-only `saga_outbox` transaction before calling the inner drain loop.
- Tests verify deterministic ordering, transaction enforcement, claim SQL, idempotent publish ack SQL, failure/dead-letter SQL, and session/saga drain transaction boundaries.
- 110 related tests passed, including legacy SQLite outbox behavior.

## Criteria Map

- Pending selection claims rows or enforces a guard: satisfied by `FOR UPDATE SKIP LOCKED` inside explicit Postgres transactions.
- Deterministic ordering across affected ledgers: satisfied by generic FSM store ordering tests using `created_at, id` for Postgres.
- Publish success idempotently marks published/acked: satisfied by SQL tests for `COALESCE(published_at, ?)` and `COALESCE(acked_at, ?)`.
- Publish failure retries/dead-letters deterministically: satisfied by SQL tests and existing session/saga retry/dead-letter regressions.
- Focused tests cover claim SQL, deterministic ordering, publish-before-ack retry, and dead-letter behavior: satisfied by `R087` verification.
- Dialect SQL remains behind FSM store / adapter helpers: satisfied; session/saga drainers only choose Postgres transaction boundary, not table SQL.

## Execution Map

- Result: R087.
- Main code paths: generic FSM store, session outbox dispatcher, saga outbox drainer.

## Stress Test

- Claim SQL test covers the duplicate-drainer protection primitive.
- Legacy failure/retry tests cover retryable and dead-letter outcomes.
- No live multi-process Postgres stress test was run, but the problem criteria are met by focused claim SQL and transaction-boundary verification.

## Residual Risk

- Future high-throughput scaling may need persisted claim owner/timeout metadata instead of transaction-scoped row locks. That is a scalability improvement, not a blocker for this first Postgres runtime.

## Result IDs

- R087
