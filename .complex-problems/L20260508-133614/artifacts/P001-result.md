# P001 Result - Generic FSM Runner 接入 Session/Task/Saga

## Done
- Added `queue_service.fsm.runner.FsmTransitionRunner` as a business-agnostic transition write runner.
- The runner writes event, materialized state, and outbox effects in one explicit-input flow.
- The runner does not read clocks, IDs, environment, random values, or global state.
- Wired `SessionLedgerRepository.record_transition()` through `FsmTransitionRunner`.
- Added `TaskLedgerRepository.record_transition()` and cut `TaskQueue._record_task_transition()` over to it.
- Added `SagaLedgerRepository.record_transition()` and cut `SagaRepository._record_saga_transition()` over to it.
- Removed active-path direct calls to `_task_ledger.append_event/upsert_state` and `_saga_ledger.append_event/upsert_state/append_outbox`.
- Added regression test `tests/test_pr342_generic_fsm_transition_runner.py`.

## Verification
- `python3 -m compileall -q queue_service/fsm/runner.py queue_service/fsm/__init__.py queue_service/task_ledger.py queue_service/saga_ledger.py queue_service/session_ledger.py queue_service/queue_db.py queue_service/saga_repo.py tests/test_pr342_generic_fsm_transition_runner.py`
- `pytest -q tests/test_pr342_generic_fsm_transition_runner.py`
- `pytest -q tests/test_pr258_generic_fsm_substrate.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr260_session_harness_generic_fsm_cutover.py tests/test_pr306_taskqueue_fsm_cutover.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr315_queue_fsm_final_residue_guard.py tests/test_pr342_generic_fsm_transition_runner.py`

All targeted checks passed: 23 tests.

## Artifacts
- `novaic-agent-runtime/queue_service/fsm/runner.py`
- `novaic-agent-runtime/queue_service/fsm/__init__.py`
- `novaic-agent-runtime/queue_service/session_ledger.py`
- `novaic-agent-runtime/queue_service/task_ledger.py`
- `novaic-agent-runtime/queue_service/saga_ledger.py`
- `novaic-agent-runtime/queue_service/queue_db.py`
- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/tests/test_pr342_generic_fsm_transition_runner.py`

## Remaining Gaps
- Lease transition code still uses its existing ledger mechanics. This ticket scoped the active Session/Task/Saga transition paths only.
