# Removed stale saga optional-step residue

## Summary

Deleted the unimplemented saga optional-step API from `task_queue/saga.py` and removed the stale `optional=True` call from `wake_finalize.py`. The remaining `optional` hits in `task_queue` are docstrings or local artifact-manifest metadata, not saga lifecycle semantics.

## Done

- Removed `SagaStep.optional`.
- Removed the `optional` argument from `SagaDefinition.add_task_step()`.
- Removed the `optional` argument from `SagaDefinition.add_parallel_step()`.
- Removed `optional=True` from `WAKE_FINALIZE_SAGA.add_task_step(name="cortex_scope_end", ...)`.
- Re-ran a focused residue scan for `optional` in `task_queue`.
- Re-ran focused saga/wake_finalize tests.

## Verification

- Residue scan:
  - Command: `rg -n '\boptional\b|optional=' task_queue -g '*.py'`
  - Result: no `optional=True`, no `optional: bool`, no `optional=optional`, and no saga optional-step API remains.
  - Remaining hits are docstrings in handlers/retry/cortex_bridge and the local `optional` metadata map in `tool_output.py`.
- Focused pytest:
  - Working directory: `novaic-agent-runtime`
  - Command: `pytest -q tests/test_runtime_tool_path_contract.py tests/integration/test_saga_dag_refactor.py tests/test_pr340_saga_launch_plans.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py tests/test_pr254_finalize_ownership.py tests/test_pr43_last_scope_wiring.py`
  - Result: `50 passed in 0.46s`.

## Known Gaps

- None for this follow-up. Broader static-residue parent problems still need reconciliation after P540 closes.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p540/verification.log`
- Changed code:
  - `novaic-agent-runtime/task_queue/saga.py`
  - `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`
