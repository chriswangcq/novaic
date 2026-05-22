# Result: Queue Runtime SQLite Residue Isolated

## Summary

Made Queue Service runtime Postgres-first and isolated the remaining SQLite path to explicit adapter/test mode. The runtime no longer silently defaults to `queue.db`; `queue.db` is now named and documented as `SQLITE_DB_PATH` for explicit SQLite mode only.

## Done

- Changed `QUEUE_DB_BACKEND` default in `queue_service/main.py` from `sqlite` to `postgres`.
- Renamed runtime `DB_PATH` to `SQLITE_DB_PATH` to make local SQLite path usage explicit.
- Updated Queue Service module/header text so `queue.db` is no longer presented as the normal service database.
- Kept SQLite path logging and readiness `sqlite_path` output inside explicit `QUEUE_DB_BACKEND == "sqlite"` branches.
- Added `tests/test_queue_runtime_postgres_default.py` static guards for Postgres default and explicit SQLite path boundaries.
- Added audit artifact `P095-sqlite-runtime-residue-audit.md` classifying retained SQLite references as adapter/test/migration boundaries.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_runtime_postgres_default.py tests/test_queue_postgres_boundary.py tests/test_queue_postgres_session_locking.py tests/test_queue_postgres_outbox_drain_semantics.py tests/test_queue_postgres_fsm_store.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr247_recovery_outbox_cutover.py` -> 52 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_runtime_postgres_default.py tests/test_queue_postgres_boundary.py tests/test_queue_postgres_session_locking.py tests/test_queue_postgres_outbox_drain_semantics.py tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_saga_query_dialect.py tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_saga_mutations.py tests/test_queue_postgres_worker_lease_ledger.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr311_saga_compensation_outbox_cutover.py` -> 113 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall -q queue_service/main.py queue_service/__init__.py tests/test_queue_runtime_postgres_default.py` -> passed.
- Audit command captured remaining SQLite references and categorized them in `P095-sqlite-runtime-residue-audit.md`.

## Known Gaps

- The generic FSM store class is still named `FsmSqliteStore`; renaming it would be a broad API cleanup and is outside this runtime-path isolation ticket.
- Explicit SQLite adapter/test support remains in the codebase by design, but it is no longer the Queue Service runtime default.

## Artifacts

- `novaic-agent-runtime/queue_service/main.py`
- `novaic-agent-runtime/queue_service/__init__.py`
- `novaic-agent-runtime/tests/test_queue_runtime_postgres_default.py`
- `.complex-problems/L20260522-091929/artifacts/P095-sqlite-runtime-residue-audit.md`
