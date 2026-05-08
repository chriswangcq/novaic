# P012 Result - Task Engine Effect Adapter Migration

## Summary

Migrated `TaskExecutionEngine` to use the generic `EffectExecutor` boundary. Concrete task/saga/business clients and URL-backed handler context are now owned by `TaskExecutionEffectAdapter`, which is wired in worker assembly and test setup.

## Done

- Added `task_queue/workers/task_effects.py` with `TaskExecutionEffectAdapter`.
- Refactored `TaskExecutionEngine` constructor to accept `effect_executor` instead of `TaskQueueClient`, `SagaClient`, `BusinessClient`, `business_url`, and `queue_service_url`.
- Replaced direct task side effects with explicit effects:
  - `task.heartbeat`
  - `task.acquire_idempotency_execution`
  - `task.complete_idempotency_execution`
  - `task.release_idempotency_execution`
  - `task.complete`
  - `task.fail`
  - `task.publish`
  - `task.get`
  - `task.handler_context`
  - `saga.get`
- Updated `assemble_task_worker` to construct `TaskExecutionEffectAdapter` and inject its executor.
- Updated focused task worker unit tests to use explicit adapters.

## Verification

- `pytest -q tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/test_pr331_task_worker_handler_cutover.py` passed with 10 tests.
- `python -m compileall -q task_queue/workers/task_execution.py task_queue/workers/task_effects.py task_queue/workers/worker_assemblies.py` passed.
- `rg -n "TaskQueueClient|SagaClient|BusinessClient|self\\.client|self\\.saga_client|self\\.business_client|business_url|queue_service_url" task_queue/workers/task_execution.py` returned no matches.

## Known Gaps

- none for the task action engine migration.
- Automated boundary guard tests are left to P014 so the task and saga engine checks land together.

## Artifacts

- `novaic-agent-runtime/task_queue/workers/task_effects.py`
- `novaic-agent-runtime/task_queue/workers/task_execution.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_dedup_guard_failure_path.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_high_concurrency_retry_replay.py`
