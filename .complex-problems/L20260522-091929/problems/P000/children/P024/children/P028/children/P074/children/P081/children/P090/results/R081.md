# Saga Query Dialect Ported

## Summary

Implemented the P090 saga candidate query dialect slice. `SagaRepository.claim`, `recover_stale`, and `cancel_all` now use backend-aware helpers. Postgres claim/recovery/cancel candidates use stable ordering, native timestamptz comparison, JSONB context filtering, and `FOR UPDATE ... SKIP LOCKED` where applicable; sqlite helper SQL preserves the existing shapes.

## Done

- Added `_saga_backend_name`.
- Added `_saga_claim_candidate_sql`.
- Added `_saga_recover_stale_candidate_sql`.
- Added `_saga_cancel_query_sql`.
- Wired `claim`, `recover_stale`, and `cancel_all` through those helpers.
- Added `tests/test_queue_postgres_saga_query_dialect.py`.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_saga_query_dialect.py` -> 9 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_saga_query_dialect.py tests/test_pr309_saga_fsm_store_ledger.py tests/test_pr313_worker_lease_ledger.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr308_saga_lifecycle_fsm.py tests/test_queue_postgres_boundary.py tests/test_queue_postgres_idempotency_diagnostics.py tests/test_queue_postgres_idempotency_complete_release.py tests/test_queue_postgres_idempotency_acquisition.py` -> 59 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/saga_repo.py tests/test_queue_postgres_saga_query_dialect.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/saga_repo.py tests/test_queue_postgres_saga_query_dialect.py` -> no whitespace errors.

## Known Gaps

- Saga single-row lifecycle mutation locking remains P091.
- Worker lease ledger Postgres semantics remain P092.
- Live Postgres runtime validation remains a later Queue staging validation problem.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-saga-query-dialect-report.json`
