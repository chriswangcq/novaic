# Queue Postgres FSM Store Foundation Added

## Summary

Implemented the Queue FSM store foundation needed before repository-specific Postgres ports. The existing sqlite behavior remains the default, while the Postgres path now has explicit JSONB-friendly values, deterministic non-rowid ordering, transaction requirements for mutations, SQLSTATE-based unique violation handling, and no SQLite busy retry behavior.

## Done

- Added backend-aware FSM store behavior via `db.backend_name`, defaulting to sqlite when absent.
- Kept sqlite payload serialization and standalone commit behavior intact.
- Added Postgres behavior that keeps JSON payload values as native dict/list-compatible values for JSONB binding.
- Added Postgres mutation guard requiring explicit transaction scope.
- Replaced Postgres event/outbox ordering that would otherwise use `rowid` with deterministic `created_at, id` or `created_at DESC, id DESC`.
- Added Postgres unique-violation detection via SQLSTATE `23505` or `UniqueViolation` class name.
- Added tests proving PG path does not retry SQLite busy-looking errors.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_fsm_store.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr342_generic_fsm_transition_runner.py` -> 15 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_boundary.py tests/test_queue_postgres_fsm_store.py tests/test_queue_explicit_dependencies.py tests/test_pr344_queue_claim_busy_handling.py tests/test_pr305_task_fsm_store_ledger.py tests/test_pr309_saga_fsm_store_ledger.py tests/test_pr313_worker_lease_ledger.py tests/test_pr235_session_ledger.py tests/test_pr315_queue_fsm_final_residue_guard.py tests/test_pr342_generic_fsm_transition_runner.py tests/test_pr259_generic_fsm_store_outbox.py` -> 50 passed.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/fsm/sqlite_store.py tests/test_queue_postgres_fsm_store.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/fsm/sqlite_store.py tests/test_queue_postgres_fsm_store.py` -> no whitespace errors.

## Known Gaps

- Task, saga, session, worker-lease, outbox claim, and route-level Postgres repository ports remain separate P080-P083 children.
- No real Postgres integration test was run in this foundation ticket.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-fsm-store-foundation-report.json`
