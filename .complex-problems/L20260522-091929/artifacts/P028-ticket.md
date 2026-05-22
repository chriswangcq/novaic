# Implement Queue Postgres Cutover

## Problem Definition

Queue still owns high-risk active state in `/opt/novaic/data/queue.db`: task FSM, saga FSM, session coordination, worker leases, outboxes, idempotency ledger, JSON predicates, timestamp comparisons, and concurrency behavior. It must move to `novaic_queue` Postgres without maintaining a SQLite fallback and without losing or replaying effects incorrectly.

## Proposed Solution

Split the Queue migration into implementation and production phases:

1. Implement a Postgres queue database boundary and schema that preserves the SQLite queue schema semantics with Postgres-native transactions, row locks, JSONB, timestamptz, indexes, and transient-error behavior.
2. Port task/saga/session/lease repositories and the generic FSM store from SQLite SQL to explicit Postgres SQL while preserving claim/recover/idempotency/outbox behavior.
3. Build a SQLite-to-Postgres migration tool with row-count and semantic invariant checks for task/saga/session/lease/outbox/idempotency state.
4. Validate in a staging/test database with queue service, workers, outbox workers, and representative API/worker smokes.
5. Execute production cutover in a writer-free window: stop queue writers/workers, back up SQLite, migrate to `novaic_queue`, restart queue service/workers in Postgres mode, run health/worker/API/outbox smokes, then archive old `queue.db` as rollback-only after no-holder checks.

## Acceptance Criteria

- Queue has a Postgres-backed store for all active queue tables.
- Task, saga, session, worker lease, outbox, and idempotency semantics are preserved under Postgres transactions/concurrency.
- SQLite JSON/timestamp/index/busy/locking assumptions are replaced with explicit Postgres behavior.
- Existing production queue state is backed up and migrated with row-count and semantic invariant checks.
- Queue service and all workers start in Postgres mode and pass health/API/worker/outbox smokes.
- No active queue writer holds or writes `/opt/novaic/data/queue.db` after cutover.
- Old `queue.db` is retained only as rollback evidence and documented in the central SQLite classification note.

## Verification Plan

Use focused unit tests for SQL generation and repository behavior, integration tests against Postgres, migration fixture tests, staging queue service/worker smokes, production row-count/invariant reports, process/file-holder inspection, and central classification/rollback notes.

## Risks

- Queue has live pending outbox rows; incorrect migration can lose or duplicate side effects.
- Claim/recover flows require real Postgres concurrency semantics, not process-local locks.
- JSONB and timestamptz conversion can subtly change eligibility and ordering behavior.
- Production cutover must stop all direct SQLite queue writers, not only the HTTP queue service.

## Assumptions

- Existing design artifacts P012-P017 remain the source of truth for Queue semantics.
- `novaic_queue` exists from the Postgres foundation work.
- No SQLite fallback should remain in production after cutover; rollback uses archived SQLite evidence and restored startup config only if needed.
