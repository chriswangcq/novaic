# Saga Lifecycle Mutation Locking Ported

## Summary

Implemented the P091 saga lifecycle mutation locking slice. `SagaRepository._get_saga_for_update` now uses backend-aware SQL and locks `tq_saga_state` with `FOR UPDATE OF ss` in Postgres mode. Saga create and row parsing now handle native JSONB-compatible values while preserving sqlite JSON text behavior. `append_step_result` and `check_saga_complete` were routed through `_get_saga_for_update`, so the single-row lifecycle paths share the same lock helper.

## Done

- Added `_saga_json_for_backend`.
- Added `_saga_json_from_db`.
- Added `_saga_for_update_sql`.
- Updated saga create context binding for Postgres/native JSONB and sqlite/JSON text.
- Updated `_row_to_dict` to preserve native `context` and `step_results` values.
- Updated `_get_saga_for_update` to use `FOR UPDATE OF ss` in Postgres mode.
- Updated `append_step_result` and `check_saga_complete` to use `_get_saga_for_update`.
- Added `tests/test_queue_postgres_saga_mutations.py`.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_saga_mutations.py` -> 13 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_saga_mutations.py tests/test_queue_postgres_saga_query_dialect.py tests/test_pr309_saga_fsm_store_ledger.py tests/test_pr313_worker_lease_ledger.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr308_saga_lifecycle_fsm.py tests/test_queue_postgres_boundary.py tests/test_queue_postgres_idempotency_diagnostics.py tests/test_queue_postgres_idempotency_complete_release.py tests/test_queue_postgres_idempotency_acquisition.py` -> 72 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/saga_repo.py tests/test_queue_postgres_saga_mutations.py tests/test_queue_postgres_saga_query_dialect.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/saga_repo.py tests/test_queue_postgres_saga_mutations.py tests/test_queue_postgres_saga_query_dialect.py` -> no whitespace errors.

## Known Gaps

- Worker lease ledger Postgres semantics remain P092.
- Live Postgres runtime validation remains a later Queue staging validation problem.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-saga-mutations-report.json`
