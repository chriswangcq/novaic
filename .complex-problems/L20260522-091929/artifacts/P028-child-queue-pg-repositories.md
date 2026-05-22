# Port Queue Repositories And FSM Semantics To Postgres

## Problem

Queue repository code currently relies on SQLite SQL, process-local locks, `json_each`/`json_extract`, busy/locked exception strings, and SQLite transaction behavior. The task queue, saga repo, session repo, worker lease ledgers, generic FSM store, outbox workers, and idempotency ledger need Postgres-specific SQL and concurrency semantics.

## Success Criteria

- Task publish/claim/complete/fail/recover/release/cancel paths work under Postgres transactions.
- Saga create/claim/heartbeat/recover/launch/complete/fail/cancel paths work under Postgres transactions.
- Session dispatch/finalize/rebuild and outbox paths preserve no-input-loss and at-most-one-active-session semantics.
- Worker lease state/event writes and recovery use explicit Postgres row locks or compare-and-update patterns.
- Idempotency duplicate/in-progress/completed-result behavior is preserved.
- SQLite JSON and busy/locked assumptions are replaced by explicit Postgres JSONB and transient-error handling.
- Focused tests cover concurrency-sensitive and idempotency-sensitive paths.
