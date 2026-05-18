# Wake finalize status gating order result

## Summary

Implemented generation-safe wake-finalize status gating. `session_ended` now runs before terminal subagent status tasks, both terminal status tasks explicitly depend on `session_ended`, and a `finalize_rejected` session result now fails the task gate instead of satisfying downstream dependencies.

## Done

- Updated `novaic-agent-runtime/task_queue/saga.py` with explicit `depends_on` support for task steps.
- Updated `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`:
  - documented the new flow as Cortex archive -> Session Coordinator -> terminal subagent status.
  - moved `session_ended` before terminal status tasks.
  - made `set_subagent_sleeping` and `set_subagent_completed` explicitly depend on `session_ended`.
  - preserved `cortex_scope_end` as the first step.
- Updated `novaic-agent-runtime/task_queue/handlers/session_handlers.py` so `finalize_rejected` raises `BusinessError`, preventing saga dependency completion for stale finalizes.
- Updated tests:
  - `tests/test_runtime_tool_path_contract.py` asserts wake-finalize order and terminal status dependencies.
  - `tests/integration/test_saga_dag_refactor.py` covers explicit `depends_on` propagation through `to_dag()` and `dag_builder.build()`.
  - `tests/test_pr254_finalize_ownership.py` asserts rejected finalize action fails the task gate.

## Verification

- `python3 -m py_compile task_queue/sagas/wake_finalize.py task_queue/saga.py task_queue/dag_builder.py task_queue/workers/task_sources.py task_queue/handlers/session_handlers.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_runtime_tool_path_contract.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/integration/test_saga_dag_refactor.py` passed: 28 tests.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_runtime_tool_path_contract.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/integration/test_saga_dag_refactor.py` passed: 41 tests.
- Manual DAG spec print confirmed:
  - `cortex_scope_end -> []`
  - `session_ended -> ['cortex_scope_end']`
  - `set_subagent_sleeping -> ['session_ended']`
  - `set_subagent_completed -> ['session_ended']`

## Known Gaps

- Aggregate P360 still needs to verify all P354 subpaths together and scan for remaining residue.

## Artifacts

- Code: `novaic-agent-runtime/task_queue/saga.py`
- Code: `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`
- Code: `novaic-agent-runtime/task_queue/handlers/session_handlers.py`
- Tests: `novaic-agent-runtime/tests/test_runtime_tool_path_contract.py`
- Tests: `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`
- Tests: `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
