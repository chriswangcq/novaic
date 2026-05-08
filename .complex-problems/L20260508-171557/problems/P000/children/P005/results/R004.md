# P005 Result

## Summary

Extracted scheduler and health action specs into pure helper modules. Scheduler scan/dispatch payloads and dispatch result/error classifications are now explicit; health recover-all payload and response normalization are also explicit.

## Changes

- Added `novaic-agent-runtime/task_queue/workers/scheduler_action_specs.py` with:
  - `due_wake_scan_effect(...)`
  - `scheduled_wake_dispatch_effect(...)`
  - `wake_metadata(...)`
  - `wake_idempotency_key(...)`
  - `classify_dispatch_result(...)`
  - `classify_dispatch_error(...)`
- Added `novaic-agent-runtime/task_queue/workers/health_action_specs.py` with:
  - `recover_all_effect(...)`
  - `normalize_recovery_snapshot(...)`
  - `HealthRecoverySnapshot`
- Updated `ScheduledWakeEngine` to consume scheduler specs and apply a `SchedulerDispatchDecision`.
- Updated `HealthRecoveryEngine` to consume health specs and normalize recovery snapshots.
- Added `novaic-agent-runtime/tests/test_pr340_scheduler_health_action_specs.py`.

## Verification

Executed:

```bash
pytest -q \
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
66 passed in 0.21s
lint_runtime_worker_supervision OK
```

## Residual Risk

Scheduler and health engines still own metrics/log application. That is intentional: the specs produce decisions and normalized payloads; the engine remains the runtime adapter for counters and log sinks.
