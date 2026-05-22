# Queue Migration Semantic Validation Result

## Summary

Added semantic aggregate validation for Queue SQLite-to-Postgres migration reports. Validation now compares row counts and Queue-specific aggregate state between source and target and marks the report `validated` or `error`.

## Done

- Added `validate_queue_migration(...)` to `queue_service/db/migration.py`.
- Added row-count comparison for every active migration table.
- Added semantic aggregate collection for task/saga/session state histograms, outbox status counts, idempotency statuses, worker lease states, max event/outbox IDs, and config schema version.
- Added structured mismatch errors.
- Added `tests/test_queue_migration_validation.py` covering success, semantic mismatch, and row-count mismatch.

## Verification

- `pytest tests/test_queue_migration_validation.py tests/test_queue_migration_copy.py tests/test_queue_migration_planner.py` passed: 13 tests.
- `pytest tests/test_queue_migration_validation.py tests/test_queue_migration_copy.py tests/test_queue_migration_planner.py tests/test_queue_postgres_boundary.py tests/test_queue_runtime_postgres_default.py tests/test_pr307_taskqueue_old_sql_residue_cleanup.py tests/test_pr315_queue_fsm_final_residue_guard.py` passed: 33 tests.
- `python -m compileall queue_service/db/migration.py tests/test_queue_migration_validation.py tests/test_queue_migration_copy.py tests/test_queue_migration_planner.py` passed.

## Known Gaps

- CLI/report-file invocation remains in P103.

## Artifacts

- `novaic-agent-runtime/queue_service/db/migration.py`
- `novaic-agent-runtime/tests/test_queue_migration_validation.py`
