# PR-312 — Saga Old SQL Residue Cleanup

Status: Closed

## Goal

Delete old imperative saga lifecycle branches after Saga FSM cutover.

## Scope

- Remove direct `tq_sagas.status` decision SQL.
- Remove obsolete compatibility tests/comments.
- Add guard tests against reintroduced direct lifecycle mutation.

## Explicit Dependency Boundary Review

SQL may persist reducer decisions and projections only; it must not encode saga
business decisions.

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- Added static residue guards proving saga lifecycle methods do not embed direct
  `UPDATE tq_sagas` / `SET status` decision SQL.
- Removed the direct `UPDATE tq_sagas` race-loser cancellation in
  `session_observed_events.py`; it now calls the SagaRepository FSM projection
  path.
- Added static residue guards proving `SagaOrchestrator.mark_failed` does not
  directly publish compensation side effects.
- Left `SagaRepository.heartbeat` as the only direct saga heartbeat projection;
  this is intentionally tracked by PR-313 worker lease FSM.

## Verification

- `pytest tests/test_pr312_saga_old_sql_residue_cleanup.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_pr310_saga_repository_fsm_cutover.py`
- `pytest tests/test_pr288_session_observed_event_handler.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr312_saga_old_sql_residue_cleanup.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr233_active_inbox_dispatch.py`
- `pytest tests/test_pr312_saga_old_sql_residue_cleanup.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr288_session_observed_event_handler.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr307_taskqueue_old_sql_residue_cleanup.py tests/test_pr306_taskqueue_fsm_cutover.py tests/test_pr304_task_lifecycle_fsm.py tests/test_pr305_task_fsm_store_ledger.py tests/test_pr308_saga_lifecycle_fsm.py tests/test_pr309_saga_fsm_store_ledger.py tests/integration/test_saga_dag_refactor.py tests/integration/test_depends_on_prev_result.py tests/test_queue_explicit_dependencies.py tests/test_runtime_tool_path_contract.py`
- Guard checks in `tests/test_pr312_saga_old_sql_residue_cleanup.py`.

## Closure Notes

Closed. Active saga lifecycle decisions now have a grep-able guard against old
imperative status SQL and direct compensation publishers. Remaining direct
heartbeat mutation is not lifecycle business logic; it is assigned to PR-313.
