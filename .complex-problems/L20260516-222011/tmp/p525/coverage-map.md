# P525 Coverage Map

## Selected Coverage Areas

- Generic FSM substrate: `test_pr258_generic_fsm_substrate.py`, `test_pr259_generic_fsm_store_outbox.py`, `test_pr261_generic_fsm_residue_cleanup.py`, `test_pr342_generic_fsm_transition_runner.py`
- Task queue FSM: `test_pr304_task_lifecycle_fsm.py`, `test_pr305_task_fsm_store_ledger.py`, `test_pr306_taskqueue_fsm_cutover.py`, `test_pr307_taskqueue_old_sql_residue_cleanup.py`, `test_pr316_taskqueue_state_candidate_cutover.py`
- Saga FSM: `integration/test_saga_dag_refactor.py`, `test_pr308_saga_lifecycle_fsm.py`, `test_pr309_saga_fsm_store_ledger.py`, `test_pr310_saga_repository_fsm_cutover.py`, `test_pr311_saga_compensation_outbox_cutover.py`, `test_pr312_saga_old_sql_residue_cleanup.py`, `test_pr317_sagarepository_state_candidate_cutover.py`, `test_pr333_saga_worker_handler_cutover.py`, `test_pr340_saga_launch_plans.py`, `test_saga_creation_policy_boundary.py`
- Worker lease/generic worker: `test_pr313_worker_lease_fsm.py`, `test_pr326_session_outbox_generic_worker.py`, `test_pr327_saga_outbox_generic_worker.py`, `test_pr333_saga_worker_handler_cutover.py`
- Queue control plane: `test_pr314_queue_control_plane_audit_replay.py`, `test_pr315_queue_fsm_final_residue_guard.py`
- Busy/recovery behavior: `test_pr344_queue_claim_busy_handling.py`, `test_pr345_recovery_background_defer.py`

## Broad Candidates Deliberately Not Selected

`broad-candidates-not-selected.txt` includes session-focused and unit/tool-output tests that match generic words like `fsm`, `recovery`, or `queue`. Those are covered by P517 or reserved for P519.
