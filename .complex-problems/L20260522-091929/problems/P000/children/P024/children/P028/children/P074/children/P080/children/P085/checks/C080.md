# Task Mutations And State Locking Verified

## Summary

P085 is successful. Result `R075` ports the task mutation slice to backend-aware Postgres behavior: task JSON values bind as native JSONB values on the Postgres path, task lifecycle reads use explicit row locking before decisions, cancel candidates lock task-state rows, and sqlite behavior remains covered by selected existing tests.

## Evidence

- `novaic-agent-runtime/queue_service/queue_db.py` now has `_json_for_backend`, `_is_unique_violation_for_backend`, and `_task_for_update_sql`.
- `TaskQueue.publish` binds payload and dependency values through `_json_for_backend`, preserving JSON text for sqlite and native objects for Postgres.
- `TaskQueue.complete`, `fail`, `heartbeat`, and `release_task` still funnel lifecycle decisions through `_get_task_for_update`.
- `_get_task_for_update` uses `_task_for_update_sql`, whose Postgres form includes `FOR UPDATE OF ts`.
- `_task_cancel_query_sql` adds `FOR UPDATE OF ts SKIP LOCKED` for Postgres cancel candidates.
- `QueuePostgresDatabase.transaction` ignores sqlite busy-timeout hints and uses a real Postgres transaction with advisory locks.
- Focused and selected regression verification passed: 24 task-focused tests, 72 selected queue/FSM tests, compileall, and diff whitespace check.

## Criteria Map

- Postgres publish writes JSONB-compatible payload/dependency/result values and preserves duplicate idempotency-key behavior -> `R075` added backend-aware JSON binding and Postgres unique-violation detection.
- Postgres complete/fail/heartbeat/release/cancel lock or compare/update task-state rows before lifecycle decisions -> complete/fail/heartbeat/release use `_get_task_for_update`; cancel uses `FOR UPDATE OF ts SKIP LOCKED`.
- `_get_task_for_update` uses `FOR UPDATE` or a reviewed equivalent -> Postgres SQL includes `FOR UPDATE OF ts`.
- Mutation paths do not depend on `sqlite_busy_timeout_ms` for Postgres correctness -> Postgres transaction wrapper drops sqlite busy hints, and correctness is carried by database transaction/advisory locks plus row locks.
- Focused tests cover loser/no-op behavior, race shape proxy, JSONB result binding, and sqlite compatibility -> `tests/test_queue_postgres_task_mutations.py` plus selected existing sqlite/FSM suites passed.

## Execution Map

- T079 / R075 -> implemented backend-aware task mutation helpers, wired publish/projection/read-before-mutate/cancel paths, added tests, and recorded verification.

## Stress Test

- Failure mode: Postgres result/payload values are double-encoded as JSON strings instead of JSONB-native parameters. Covered by fake Postgres binding tests for publish/projection.
- Failure mode: duplicate workers mutate stale task state without locking. Covered by SQL shape tests and no-op mutation path tests asserting `FOR UPDATE OF ts` is used before lifecycle decisions.
- Failure mode: cancel races with claim/recovery. Covered by Postgres cancel candidate SQL requiring `FOR UPDATE OF ts SKIP LOCKED`.
- Failure mode: sqlite task behavior regresses from helper extraction. Covered by selected existing sqlite task lifecycle and FSM regression tests.

## Residual Risk

- Real PostgreSQL concurrency validation is still required in staging, but that belongs to the later Queue staging validation problem rather than this code-level mutation slice.
- The task idempotency execution ledger remains a separate child problem, P086; P085 only preserves publish duplicate key behavior.

## Result IDs

- R075
