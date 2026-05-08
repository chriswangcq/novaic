# P013 Result - Saga Engine Effect Adapter Migration

## Summary

Migrated `SagaLaunchEngine` to explicit effect execution. Concrete saga/task clients are now owned by `SagaLaunchEffectAdapter`; the engine keeps DAG construction and launch decisions but performs heartbeat, publish, and saga state updates through named effects.

## Done

- Added `task_queue/workers/saga_effects.py` with `SagaLaunchEffectAdapter`.
- Refactored `SagaLaunchEngine` constructor to accept `effect_executor` instead of `saga_client` and `task_client`.
- Replaced direct saga side effects with explicit effects:
  - `saga.heartbeat`
  - `saga.task_publish`
  - `saga.mark_launched`
  - `saga.mark_failed`
- Updated `assemble_saga_worker` to construct the adapter and inject its executor.
- Updated saga worker tests and added a launch-path test proving publish/state updates go through the adapter.

## Verification

- `pytest -q tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py` passed with 8 tests.
- `python -m compileall -q task_queue/workers/saga_launch.py task_queue/workers/saga_effects.py task_queue/workers/worker_assemblies.py` passed.
- `rg -n "SagaClient|TaskQueueClient|self\\.saga_client|self\\.task_client|mark_launched\\(|mark_failed\\(|publish\\(" task_queue/workers/saga_launch.py` returned no matches.

## Known Gaps

- none for saga launch engine migration.
- Automated task/saga boundary guard tests are left to P014.

## Artifacts

- `novaic-agent-runtime/task_queue/workers/saga_effects.py`
- `novaic-agent-runtime/task_queue/workers/saga_launch.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/tests/test_pr333_saga_worker_handler_cutover.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_saga_worker_boundary.py`
