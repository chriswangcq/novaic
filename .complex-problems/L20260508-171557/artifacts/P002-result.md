# P002 Result

## Summary

Implemented the plan-first effect runner boundary. Action engines now invoke effects through `EffectPlanRunner`, while `execute_effect(...)` remains only as a compatibility substrate helper and is no longer imported or called by task/saga/scheduler/health engines.

## Changes

- Added `EffectPlanRunner` to `novaic-agent-runtime/queue_service/worker/effects.py`.
- Exported `EffectPlanRunner` from `novaic-agent-runtime/queue_service/worker/__init__.py`.
- Migrated these engines to `self.effect_runner.run_one(...)`:
  - `novaic-agent-runtime/task_queue/workers/task_execution.py`
  - `novaic-agent-runtime/task_queue/workers/saga_launch.py`
  - `novaic-agent-runtime/task_queue/workers/scheduled_wake.py`
  - `novaic-agent-runtime/task_queue/workers/health_recovery.py`
- Removed local `_effect(...)` helper methods and `self.effect_executor` ownership from those action engines.
- Updated boundary tests to assert action engines use `EffectPlanRunner` and contain no `execute_effect`, `_effect`, or `self.effect_executor` residue.
- Updated existing lifecycle tests to respect the P001 split between `worker_assemblies.py` and `assembly_factories.py`.

## Verification

Executed:

```bash
rg -n "execute_effect|def _effect|self\._effect|self\.effect_executor" \
  task_queue/workers/task_execution.py \
  task_queue/workers/saga_launch.py \
  task_queue/workers/scheduled_wake.py \
  task_queue/workers/health_recovery.py || true

pytest -q \
  tests/test_pr340_worker_effect_plan.py \
  tests/test_pr340_action_engine_effect_boundaries.py \
  tests/unit/task_queue/test_retry_policy_and_idempotency.py \
  tests/unit/task_queue/test_saga_worker_boundary.py \
  tests/test_health_dispatch.py \
  tests/test_scheduler_dispatch.py \
  tests/test_pr328_health_generic_worker.py \
  tests/test_pr329_scheduler_generic_worker.py \
  tests/test_pr333_saga_worker_handler_cutover.py

PYTHONDONTWRITEBYTECODE=1 python3 scripts/ci/lint_runtime_worker_supervision.py
```

Observed:

```text
44 passed in 0.18s
lint_runtime_worker_supervision OK
```

The direct effect-execution residue scan returned no matches in the four action engines.

## Residual Risk

Effect payload shapes are still handwritten at call sites. That is expected after P002; P003-P005 own policy/action-spec extraction for task, saga, scheduler, and health behavior.
