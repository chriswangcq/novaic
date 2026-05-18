# Generic Queue infrastructure generation classification result

## Summary

Completed the P408 classification pass over generic Queue infrastructure. No dangerous session-generation compatibility residue was found in this scope. Remaining hits are generic FSM/task/saga/lease generation mechanics, retry/version/counter fields, explicit validators, or already-patched session-adjacent suspected-dead handling.

## Done

- Ran a targeted guard over `queue_db.py`, `saga_repo.py`, `task_fsm.py`, and `fsm/sqlite_store.py`.
- Classified `task_fsm.py` hits as task lifecycle state:
  - default generation/retry/max_retries belong to task FSM state, not session active generation.
  - retry defaults are task retry metadata.
  - `generation=int(state.generation)+1` is task FSM version advancement.
- Classified `fsm/sqlite_store.py` hits as generic non-negative generation validation and bounded query/attempt integers.
- Classified `queue_db.py` hits as task/lease FSM state mechanics:
  - task and lease generations are generic queue FSM generations.
  - retry/max_retries/version/status-code style fields are not session-generation authority.
  - task/lease event IDs include generic generation for idempotency, not session finalize authority.
- Classified `saga_repo.py` hits:
  - saga/lease generation fields are generic saga/lease FSM generation mechanics.
  - `_positive_session_generation_from_context` fails closed by returning `None` for missing/bad session generation.
  - suspected-dead session event path already requires existing session state and validates positive session generation before writing.

## Verification

- Guard artifact: `.complex-problems/L20260516-222011/tmp/p408/generic-queue-infra-guard.txt`.
- Corrected focused test suite after noticing an initial nonexistent `tests/test_task_fsm.py` entry:
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr258_generic_fsm_substrate.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr305_task_fsm_store_ledger.py tests/test_pr306_taskqueue_fsm_cutover.py tests/test_pr309_saga_fsm_store_ledger.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr313_worker_lease_fsm.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr311_saga_compensation_outbox_cutover.py`
  - Result: `40 passed in 0.34s`.

## Known Gaps

- None for P408's generic Queue infrastructure scope.
- Task/saga handler contract hits remain under sibling `P409`.
- Worker/health counter hits remain under sibling `P410`.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p408/generic-queue-infra-guard.txt`
