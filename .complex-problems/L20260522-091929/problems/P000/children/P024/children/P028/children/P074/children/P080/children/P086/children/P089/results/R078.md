# Idempotency Diagnostics Normalized

## Summary

Implemented the P089 diagnostics normalization slice. `get_idempotency_diagnostics` now reads public fields through `_row_value`, allowing sqlite tuple rows and Postgres dict-like rows to produce the same output shape. Existing filter, ordering, and limit clamping semantics were preserved.

## Done

- Replaced tuple-only diagnostics row reads with `_row_value`.
- Preserved public fields: `idempotency_key`, `status`, `owner_token`, `task_id`, `contention_count`, `last_contended_at`, `lease_until`, and `updated_at`.
- Preserved `contention_count` integer normalization.
- Preserved `only_contended` SQL filter.
- Preserved ordering by contention count descending and updated time descending.
- Preserved limit clamping to `1..200`.
- Added `tests/test_queue_postgres_idempotency_diagnostics.py`.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_idempotency_diagnostics.py` -> 5 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_idempotency_diagnostics.py tests/test_queue_postgres_idempotency_complete_release.py tests/test_queue_postgres_idempotency_acquisition.py tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_boundary.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/test_pr340_task_execution_policies.py` -> 66 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/queue_db.py tests/test_queue_postgres_idempotency_diagnostics.py tests/test_queue_postgres_idempotency_complete_release.py tests/test_queue_postgres_idempotency_acquisition.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/queue_db.py tests/test_queue_postgres_idempotency_diagnostics.py tests/test_queue_postgres_idempotency_complete_release.py tests/test_queue_postgres_idempotency_acquisition.py` -> no whitespace errors.

## Known Gaps

- Real Postgres runtime validation remains a later Queue staging validation problem.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-idempotency-diagnostics-report.json`
