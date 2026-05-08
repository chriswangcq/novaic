# P014 Result - Task/Saga Engine Boundary Guards

## Summary

Added automated guardrails that enforce the task/saga action engine effect-adapter boundary. The tests reject concrete client imports, old constructor parameters, self-owned protocol clients, direct self-client protocol calls, and missing assembly adapter wiring.

## Done

- Added `tests/test_pr340_action_engine_effect_boundaries.py`.
- Guarded `TaskExecutionEngine` against concrete client imports, old constructor args, self-owned client attrs, and direct protocol calls.
- Guarded `SagaLaunchEngine` against concrete client imports, old constructor args, self-owned client attrs, and direct protocol calls.
- Guarded worker assembly wiring for `TaskExecutionEffectAdapter` and `SagaLaunchEffectAdapter`.

## Verification

- `pytest -q tests/test_pr340_action_engine_effect_boundaries.py tests/test_pr333_saga_worker_handler_cutover.py tests/unit/task_queue/test_saga_worker_boundary.py tests/unit/task_queue/test_retry_policy_and_idempotency.py tests/unit/task_queue/test_dedup_guard_failure_path.py tests/unit/task_queue/test_high_concurrency_retry_replay.py tests/test_pr331_task_worker_handler_cutover.py` passed with 21 tests.
- `python -m compileall -q task_queue/workers tests/test_pr340_action_engine_effect_boundaries.py` passed.

## Known Gaps

- none for task/saga engine boundary guards.

## Artifacts

- `novaic-agent-runtime/tests/test_pr340_action_engine_effect_boundaries.py`
