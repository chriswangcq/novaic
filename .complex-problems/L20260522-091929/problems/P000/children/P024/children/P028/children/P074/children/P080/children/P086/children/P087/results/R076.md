# Idempotency Acquisition Ported

## Summary

Implemented the P087 Postgres acquisition slice for `TaskQueue.acquire_idempotency_execution`. The Postgres path now selects the target idempotency ledger row with `FOR UPDATE`, evaluates active leases using a native timestamptz SQL predicate, and normalizes completed results from either native JSONB values or legacy sqlite JSON text. The sqlite path keeps its existing Python ISO lease parsing behavior.

## Done

- Added `_idempotency_acquire_select_sql` with backend-specific SQL.
- Added `_idempotency_result_from_db` to handle native JSONB dict/list/scalar values and legacy JSON strings.
- Added `_row_value` so acquisition can read sqlite tuple rows and Postgres dict-like rows.
- Updated `acquire_idempotency_execution` to use Postgres row locking and SQL-side lease activity when `backend_name == "postgres"`.
- Preserved missing-key behavior, missing-row insert behavior, active duplicate contention updates, expired lease reacquire, and same-owner renewal behavior.
- Added `tests/test_queue_postgres_idempotency_acquisition.py`.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_idempotency_acquisition.py` -> 10 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_idempotency_acquisition.py tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_boundary.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/test_pr340_task_execution_policies.py` -> 53 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/queue_db.py tests/test_queue_postgres_idempotency_acquisition.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/queue_db.py tests/test_queue_postgres_idempotency_acquisition.py` -> no whitespace errors.

## Known Gaps

- Completion and release ownership semantics remain P088.
- Diagnostics row-shape normalization remains P089.
- Real Postgres concurrency validation remains a later staging validation problem.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-idempotency-acquisition-report.json`
