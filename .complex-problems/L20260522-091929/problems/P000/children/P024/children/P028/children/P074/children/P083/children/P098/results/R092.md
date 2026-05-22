# Worker Startup And Recovery SQLite Boundary Result

## Summary

Worker startup retry and recovery transaction timeout handling now use explicit boundaries instead of leaking SQLite-specific exception classes or raw timeout kwargs through production-facing Queue code.

## Done

- Updated `task_queue/workers/assembly_factories.py` to remove direct `sqlite3` import/catch and use `classify_queue_transient_error(...)` for startup retry decisions.
- Added `queue_service/db/sqlite_boundary.py` as the named SQLite-only transaction kwarg boundary.
- Replaced raw `sqlite_busy_timeout_ms=250` kwargs in `queue_service/queue_db.py` and `queue_service/saga_repo.py` with `sqlite_lock_timeout_kwargs(self.db)`.
- Updated startup retry tests to cover both SQLite busy and Postgres connection transient retry behavior.
- Updated recovery/static guard tests to assert the boundary rather than raw SQLite timeout hint counts.
- Renamed the helper module from a `compat` path to `sqlite_boundary.py` after FSM residue guards rejected compatibility language in active queue coordinators.

## Verification

- `pytest tests/test_pr339_worker_startup_db_retry.py tests/test_pr345_recovery_background_defer.py tests/test_queue_transient_errors.py` passed: 13 tests.
- `pytest tests/test_pr339_worker_startup_db_retry.py tests/test_pr345_recovery_background_defer.py tests/test_queue_transient_errors.py tests/test_pr315_queue_fsm_final_residue_guard.py` passed: 17 tests.
- Broad Queue/worker/Postgres/static regression command passed: 167 tests.
- `python -m compileall queue_service task_queue tests/test_queue_transient_errors.py tests/test_pr339_worker_startup_db_retry.py tests/test_pr345_recovery_background_defer.py` passed.
- Residue search over worker assembly, queue/saga repos, routes, transient classifier, SQLite boundary, and Postgres adapter shows `sqlite_busy_timeout_ms` only in `sqlite_boundary.py` and the Postgres adapter ignore boundary, and direct `sqlite3.OperationalError` only in `transient_errors.py`.

## Known Gaps

- None for P098. SQLite behavior remains as an explicit boundary and test fixture, not as unbranched production-facing route/worker/repository residue.

## Artifacts

- `novaic-agent-runtime/queue_service/db/sqlite_boundary.py`
- `novaic-agent-runtime/queue_service/queue_db.py`
- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/task_queue/workers/assembly_factories.py`
- `novaic-agent-runtime/tests/test_pr339_worker_startup_db_retry.py`
- `novaic-agent-runtime/tests/test_pr345_recovery_background_defer.py`
- `novaic-agent-runtime/tests/test_queue_transient_errors.py`
