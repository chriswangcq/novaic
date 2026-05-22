# Queue Migration CLI Result

## Summary

Added a testable Queue migration CLI module that supports dry-run planning, copy-plus-validation execution, redacted JSON report writing, and non-zero exit codes for blocked/error outcomes.

## Done

- Added `queue_service/db/migrate_sqlite_to_postgres.py`.
- Added parser options for `--sqlite-path`, `--postgres-dsn`, `--postgres-dsn-file`, `--report-path`, `--dry-run`, and `--allow-non-empty-target`.
- Added injectable `main(...)` dependencies for tests and a real DB factory for operator use.
- Dry-run path calls planner and writes report without copy execution.
- Execution path calls copy, validates copied reports, writes final report, and returns non-zero for blocked/error statuses.
- Added `tests/test_queue_migration_cli.py`.

## Verification

- `pytest tests/test_queue_migration_cli.py tests/test_queue_migration_validation.py tests/test_queue_migration_copy.py tests/test_queue_migration_planner.py` passed: 17 tests.
- `pytest tests/test_queue_migration_cli.py tests/test_queue_migration_validation.py tests/test_queue_migration_copy.py tests/test_queue_migration_planner.py tests/test_queue_postgres_boundary.py tests/test_queue_runtime_postgres_default.py tests/test_pr307_taskqueue_old_sql_residue_cleanup.py tests/test_pr315_queue_fsm_final_residue_guard.py` passed: 37 tests.
- `python -m compileall queue_service/db/migrate_sqlite_to_postgres.py queue_service/db/migration.py tests/test_queue_migration_cli.py` passed.
- `python -m queue_service.db.migrate_sqlite_to_postgres --help` displayed the expected CLI options.

## Known Gaps

- CLI execution is tested with injected fakes, not a live Postgres target. Live invocation remains a staging/cutover concern.

## Artifacts

- `novaic-agent-runtime/queue_service/db/migrate_sqlite_to_postgres.py`
- `novaic-agent-runtime/tests/test_queue_migration_cli.py`
