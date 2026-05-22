# Task Mutations And State Locking Ported

## Summary

Implemented the P085 task mutation slice for Postgres. Task JSON payload/result/dependency values now have backend-aware binding, task single-row reads use `FOR UPDATE OF ts` in Postgres mode, cancel candidates lock task-state rows in Postgres mode, and publish idempotency-key duplicate handling can recognize Postgres unique violations.

## Done

- Added `_json_for_backend` to keep Postgres JSONB values native and sqlite values JSON text.
- Added `_is_unique_violation_for_backend` for Postgres SQLSTATE/class-name unique detection and sqlite unique-string compatibility.
- Added `_task_for_update_sql` with `FOR UPDATE OF ts` for Postgres.
- Wired `_get_task_for_update` through `_task_for_update_sql`, covering complete/fail/heartbeat/release paths that read task state before deciding lifecycle mutations.
- Added `FOR UPDATE OF ts SKIP LOCKED` to Postgres cancel candidate SQL.
- Updated task publish payload/dependency values and task result projection to use backend-aware JSON values.
- Added tests for JSON binding, task-state lock SQL, cancel lock SQL, no-row mutation paths, and Postgres unique violation detection.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_task_query_dialect.py tests/test_pr316_taskqueue_state_candidate_cutover.py tests/test_queue_explicit_dependencies.py` -> 24 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_boundary.py tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_task_mutations.py tests/test_queue_explicit_dependencies.py tests/test_pr344_queue_claim_busy_handling.py tests/test_pr305_task_fsm_store_ledger.py tests/test_pr309_saga_fsm_store_ledger.py tests/test_pr313_worker_lease_ledger.py tests/test_pr235_session_ledger.py tests/test_pr315_queue_fsm_final_residue_guard.py tests/test_pr342_generic_fsm_transition_runner.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr316_taskqueue_state_candidate_cutover.py` -> 72 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/queue_db.py tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_task_query_dialect.py queue_service/db/postgres.py tests/test_queue_postgres_boundary.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/queue_db.py tests/test_queue_postgres_task_mutations.py tests/test_queue_postgres_task_query_dialect.py queue_service/db/postgres.py tests/test_queue_postgres_boundary.py` -> no whitespace errors.

## Known Gaps

- Task idempotency ledger acquisition/completion/release remains P086.
- Real Postgres concurrency validation remains a later staging ticket.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-task-mutations-report.json`
