# P004 Result

## Summary

Implemented an explicit saga launch plan boundary. Saga launch now compiles DAG task publish effects plus mark-launched into a pure `SagaLaunchPlan`, and the engine executes that plan through `EffectPlanRunner`.

## Changes

- Added `novaic-agent-runtime/task_queue/workers/saga_launch_plans.py` with:
  - `SagaLaunchPlan`
  - `normalize_saga_context(...)`
  - `compile_saga_launch_plan(...)`
  - `mark_saga_failed_plan(...)`
- Updated `novaic-agent-runtime/task_queue/workers/saga_launch.py` to:
  - normalize saga context through the plan helper
  - execute compiled launch plans through `EffectPlanRunner`
  - execute explicit mark-failed plans for unknown saga type and launch failure
  - remove direct task publish / mark-launched effect construction from the engine
- Added `SAGA_CALLBACK_EXTENSION_POINTS` and documentation to `novaic-agent-runtime/task_queue/saga.py`.
- Added `novaic-agent-runtime/tests/test_pr340_saga_launch_plans.py`.
- Updated boundary/cutover tests to assert saga effect strings live in the plan compiler, not the engine.

## Verification

Executed:

```bash
pytest -q \
  tests/test_pr340_saga_launch_plans.py \
  tests/test_pr340_task_execution_policies.py \
  tests/test_pr340_worker_effect_plan.py \
  tests/test_pr340_action_engine_effect_boundaries.py \
  tests/test_pr333_saga_worker_handler_cutover.py \
  tests/unit/task_queue/test_saga_worker_boundary.py \
  tests/unit/task_queue/test_retry_policy_and_idempotency.py \
  tests/test_health_dispatch.py \
  tests/test_scheduler_dispatch.py

PYTHONDONTWRITEBYTECODE=1 python3 ../scripts/ci/lint_runtime_worker_supervision.py
```

Observed:

```text
51 passed in 0.18s
lint_runtime_worker_supervision OK
```

## Residual Risk

Saga step callback bodies are still user-defined Python callables. This ticket names and documents them as explicit computation hooks; fully replacing callback callables with data-only DSL is a larger design step beyond P004.
