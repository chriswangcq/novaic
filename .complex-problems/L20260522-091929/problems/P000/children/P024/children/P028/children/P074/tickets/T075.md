# Port Queue Repository SQL And FSM Semantics To Postgres

## Problem Definition

Queue now has a Postgres schema and database boundary, but the repository/runtime layer still contains SQLite-specific SQL and semantics. The task queue, saga repo, session repo, FSM stores, worker lease ledgers, outbox workers, route exception handling, and idempotency ledger must be ported so Queue behavior is correct under Postgres transactions, JSONB, timestamptz, row locks, and transient PG errors.

## Proposed Solution

Split the repository port into focused implementation children instead of one risky edit. First introduce Queue dialect helpers and a Postgres FSM store boundary, then port task/saga claim/recovery/idempotency paths, then port session/outbox/worker-lease semantics, then replace SQLite busy handling with PG transient-error handling and focused concurrency tests. Keep production cutover and data migration out of this ticket; this ticket is the code/runtime semantics port needed before staging.

## Acceptance Criteria

- Task publish/claim/complete/fail/recover/release/cancel paths have Postgres-safe SQL and transaction behavior.
- Saga create/claim/heartbeat/recover/launch/complete/fail/cancel paths have Postgres-safe SQL and transaction behavior.
- Session dispatch/finalize/rebuild and outbox paths preserve no-input-loss and at-most-one-active-session semantics under Postgres.
- Worker lease state/event writes and recovery use explicit Postgres row locks or compare-and-update patterns.
- Idempotency duplicate, in-progress, completed-result, and lease behavior is preserved.
- SQLite `datetime`, `json_each`, `json_extract`, `rowid`, PRAGMA, and busy/locked exception assumptions are removed from the Postgres runtime path.
- Focused tests cover concurrency-sensitive, JSONB-sensitive, transient-error, and idempotency-sensitive paths without touching production.

## Verification Plan

Run targeted Queue unit tests for task/saga/session/FSM/outbox/idempotency behavior, add fake/fixture Postgres boundary tests for generated SQL and transient errors, and run grep/static guards for SQLite-only assumptions in PG-mode paths. Real Postgres integration belongs to the later staging-validation child after this port is complete.

## Risks

- This touches correctness paths for task claiming, saga launching, session dispatch, outbox delivery, and idempotency; splitting is safer than one large patch.
- SQLite row shapes and current JSON string storage can hide PG type mismatches unless repository boundaries explicitly encode/decode JSONB.
- Route-level busy handling may accidentally keep logging or classifying SQLite errors in PG mode if not tested.
- Concurrency behavior can appear correct in unit tests but still need real Postgres staging validation later.

## Assumptions

- P073/P078 provide the schema and database boundary needed for this work.
- Migration tooling, staging validation, production cutover, and old SQLite cleanup remain later children.
- SQLite may remain only as local/unit-test fixture during the transition, not as a second long-term production logic path.
