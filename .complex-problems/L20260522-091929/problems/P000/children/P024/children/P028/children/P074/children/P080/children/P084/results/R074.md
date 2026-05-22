# Task Queue Postgres Query Dialect Added

## Summary

Implemented the P084 query-dialect slice for TaskQueue. Claim, stale recovery, and cancel candidate SQL now flow through backend-aware helpers, preserving sqlite behavior while adding Postgres SQL forms for native timestamptz comparisons, JSONB dependency readiness, JSONB agent filtering, stable ordering, and `FOR UPDATE ... SKIP LOCKED` candidate locking.

## Done

- Added `_task_claim_candidate_sql`, `_task_recover_stale_candidate_sql`, `_task_cancel_query_sql`, and `_queue_backend_name` in `queue_service/queue_db.py`.
- Wired `TaskQueue.claim`, `TaskQueue.recover_stale`, and `TaskQueue.cancel_all` through those helpers.
- Added Postgres claim SQL using `ts.next_retry_at <= ?`, `jsonb_array_elements_text`, `COALESCE(ss.step_results, '{}'::jsonb) ? dep.step_name`, `ORDER BY t.created_at, t.id`, and `FOR UPDATE OF ts SKIP LOCKED`.
- Added Postgres stale recovery SQL using `ls.heartbeat_at < ?`, `ORDER BY ls.heartbeat_at, ts.task_id`, and `FOR UPDATE OF ts, ls SKIP LOCKED`.
- Added Postgres cancel-by-agent SQL using `t.payload ->> 'agent_id' = ?`.
- Preserved sqlite SQL forms for current fixtures.
- Extended `QueuePostgresDatabase._convert_placeholders` to preserve JSONB `?` operators with identifier right operands like `dep.step_name`.
- Added focused query dialect tests.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_boundary.py tests/test_pr316_taskqueue_state_candidate_cutover.py tests/test_queue_explicit_dependencies.py` -> 24 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_boundary.py tests/test_queue_postgres_fsm_store.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_explicit_dependencies.py tests/test_pr344_queue_claim_busy_handling.py tests/test_pr305_task_fsm_store_ledger.py tests/test_pr309_saga_fsm_store_ledger.py tests/test_pr313_worker_lease_ledger.py tests/test_pr235_session_ledger.py tests/test_pr315_queue_fsm_final_residue_guard.py tests/test_pr342_generic_fsm_transition_runner.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr316_taskqueue_state_candidate_cutover.py` -> 61 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/queue_db.py queue_service/db/postgres.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_boundary.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/queue_db.py queue_service/db/postgres.py tests/test_queue_postgres_task_query_dialect.py tests/test_queue_postgres_boundary.py` -> no whitespace errors.

## Known Gaps

- Task mutation row-lock/compare-update behavior remains P085.
- Task idempotency ledger Postgres behavior remains P086.
- No real Postgres integration test was run in this query dialect ticket.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-task-query-dialect-report.json`
