# Result: Session Rebuild Read Models Ported To Postgres

## Summary

Added an explicit Postgres-safe session rebuild query boundary. Startup rebuild now uses deterministic active saga ordering and a Postgres-specific row-lock/advisory-lock shape while preserving SQLite-compatible behavior for local adapter tests.

## Done

- Added `_active_saga_contexts_sql(backend=...)` in `queue_service/session_rebuild.py`.
- Postgres rebuild query now orders by `ss.updated_at, ss.saga_id` and appends `FOR UPDATE OF ss SKIP LOCKED`.
- SQLite rebuild query keeps the same deterministic ordering without Postgres lock syntax.
- Added `_session_rebuild_lock_type(...)` so Postgres uses `session_rebuild` transaction lock type and SQLite stays on `global`.
- Added focused tests for Postgres SQL shape, SQLite SQL shape, and lock type selection.
- Existing rebuild behavior still marks stale active sessions no-active and reconstructs active sessions from running/launched saga state.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_pr279_session_rebuild_projector_boundary.py` -> 13 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_pr279_session_rebuild_projector_boundary.py tests/test_pr252_session_state_ssot.py tests/test_pr257_remove_active_sessions_table.py tests/test_pr318_projection_table_quarantine_guard.py::test_startup_session_rebuild_uses_saga_state_not_saga_projection_status tests/test_queue_postgres_boundary.py tests/test_queue_postgres_session_locking.py tests/test_queue_runtime_postgres_default.py` -> 42 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall -q queue_service/session_rebuild.py tests/test_pr279_session_rebuild_projector_boundary.py` -> passed.
- `rg -n "FOR UPDATE OF ss SKIP LOCKED|ORDER BY ss.updated_at|session_rebuild|json_extract|rowid" queue_service/session_rebuild.py tests/test_pr279_session_rebuild_projector_boundary.py` confirmed the intended Postgres lock/order tests and absence checks.

## Known Gaps

- None for `P097`.
- Non-blocking note: running the full `tests/test_pr318_projection_table_quarantine_guard.py` file also exercises unrelated TaskQueue/SagaRepository static guards that currently fail because task/saga query SQL has been moved behind helper functions. The rebuild-specific pr318 test passed.

## Artifacts

- `novaic-agent-runtime/queue_service/session_rebuild.py`
- `novaic-agent-runtime/tests/test_pr279_session_rebuild_projector_boundary.py`
