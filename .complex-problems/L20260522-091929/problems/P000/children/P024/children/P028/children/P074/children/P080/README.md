# Port Task Queue And Idempotency Paths To Postgres

## Problem

`queue_service/queue_db.py` still uses SQLite `datetime(...)`, `json_each`, `json_extract`, local busy-timeout hints, and SQLite-flavored idempotency SQL. Task publish/claim/complete/fail/recover/release/cancel and idempotency duplicate handling must work under Postgres row locks, JSONB predicates, native timestamptz comparisons, and explicit transaction semantics. This belongs under P074 because task correctness and idempotency are one tightly coupled repository slice.

## Success Criteria

- Task claim uses Postgres-safe candidate selection and locking, including `FOR UPDATE SKIP LOCKED` or an equivalent explicit compare-and-update pattern.
- Task single-row mutations use explicit task-state locking or compare-and-update semantics instead of process-local SQLite locks.
- Task retry/stale recovery uses native timestamptz comparisons rather than SQLite `datetime(...)`.
- Task dependency readiness and cancel-by-agent use JSONB predicates rather than `json_each`/`json_extract`.
- Idempotency in-progress/completed/duplicate-result behavior is preserved under Postgres transactions.
- Focused tests cover duplicate claim losers, completion/recovery races, JSONB dependency readiness, cancel-by-agent, and idempotency completed/in-progress cases without production access.
