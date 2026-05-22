# Queue Postgres JSON Expression Indexes Added

## Summary

Closed the P073 follow-up gap by adding the two required JSONB expression indexes to the Queue Postgres schema and protecting the adapter placeholder conversion so Postgres JSONB `?` operators survive schema execution.

## Done

- Added `idx_tq_tasks_payload_agent` on `tq_tasks ((payload ->> 'agent_id')) WHERE payload ? 'agent_id'`.
- Added `idx_tq_saga_state_context_agent` on `tq_saga_state ((context ->> 'agent_id')) WHERE context ? 'agent_id'`.
- Updated `QueuePostgresDatabase._convert_placeholders` to preserve JSONB question operators while still converting qmark bind placeholders to `%s`.
- Extended `tests/test_queue_postgres_boundary.py` to assert the required expression index names, expressions, predicates, and adapter conversion behavior during schema initialization.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_boundary.py` -> 11 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_boundary.py tests/test_queue_explicit_dependencies.py tests/test_pr344_queue_claim_busy_handling.py tests/test_pr305_task_fsm_store_ledger.py tests/test_pr309_saga_fsm_store_ledger.py tests/test_pr313_worker_lease_ledger.py tests/test_pr235_session_ledger.py tests/test_pr315_queue_fsm_final_residue_guard.py` -> 35 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/db/postgres.py queue_service/db/schema.py tests/test_queue_postgres_boundary.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/db/postgres.py queue_service/db/schema.py tests/test_queue_postgres_boundary.py` -> no whitespace errors.

## Known Gaps

- None for this P078 follow-up.
- Broader Queue repository SQL porting and production cutover remain separate planned tickets.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-json-expression-indexes-report.json`
