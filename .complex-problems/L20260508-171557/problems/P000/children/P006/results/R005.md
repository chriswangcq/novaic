# P006 Result

## Summary

Added declarative handler registry metadata and boundary tests. Handler registration now records topic, pool, module, and handler name while keeping existing lookup and pool behavior compatible.

## Changes

- Added `HandlerSpec` metadata in `novaic-agent-runtime/task_queue/handlers/__init__.py`.
- Added `get_handler_spec(...)` and `get_all_handler_specs(...)`.
- Updated pool lookup to use registered handler metadata.
- Added `novaic-agent-runtime/tests/test_pr340_handler_registry_metadata.py`.

## Verification

Executed:

```bash
pytest -q \
  tests/test_pr340_handler_registry_metadata.py \
  tests/test_pr340_scheduler_health_action_specs.py \
  tests/test_pr340_saga_launch_plans.py \
  tests/test_pr340_task_execution_policies.py \
  tests/test_pr340_worker_effect_plan.py \
  tests/test_pr340_action_engine_effect_boundaries.py \
  tests/test_scheduler_dispatch.py \
  tests/test_health_dispatch.py \
  tests/test_pr328_health_generic_worker.py \
  tests/test_pr329_scheduler_generic_worker.py \
  tests/test_pr333_saga_worker_handler_cutover.py \
  tests/unit/task_queue/test_retry_policy_and_idempotency.py \
  tests/unit/task_queue/test_saga_worker_boundary.py

PYTHONDONTWRITEBYTECODE=1 python3 ../scripts/ci/lint_runtime_worker_supervision.py
```

Observed:

```text
70 passed in 0.28s
lint_runtime_worker_supervision OK
```

## Residual Risk

Handler functions remain Python business functions. This ticket makes their registry surface inspectable and guardable; it does not attempt to replace handler bodies with data-only DSL.
