# Idempotency Completion And Release Ported

## Summary

Implemented the P088 completion/release slice for the task idempotency ledger. Completion now binds results through the backend-aware JSON helper, so Postgres receives native JSONB-compatible values and sqlite keeps JSON text. The completion fallback no longer overwrites conflicting existing rows; it only inserts a completed row when the idempotency key is absent. Release remains scoped to matching in-progress owner/task rows and now has focused tests.

## Done

- Updated `complete_idempotency_execution` to use `_json_for_backend`.
- Kept the guarded completion update requiring `idempotency_key`, `status = 'in_progress'`, `owner_token`, and `task_id`.
- Replaced fallback `ON CONFLICT ... DO UPDATE` with `ON CONFLICT(idempotency_key) DO NOTHING`.
- Made completion return false when a guarded update misses and the key already exists.
- Added `tests/test_queue_postgres_idempotency_complete_release.py`.
- Covered release success/nonmatch and empty-key no-op behavior.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_idempotency_complete_release.py` -> 8 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_idempotency_complete_release.py tests/test_queue_postgres_idempotency_acquisition.py tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_boundary.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/test_pr340_task_execution_policies.py` -> 61 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/queue_db.py tests/test_queue_postgres_idempotency_complete_release.py tests/test_queue_postgres_idempotency_acquisition.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/queue_db.py tests/test_queue_postgres_idempotency_complete_release.py tests/test_queue_postgres_idempotency_acquisition.py` -> no whitespace errors.

## Known Gaps

- Diagnostics row-shape normalization remains P089.
- Real Postgres concurrent completion/release validation remains a later staging validation problem.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-idempotency-complete-release-report.json`
