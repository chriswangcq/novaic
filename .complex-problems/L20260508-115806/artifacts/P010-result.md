# P010 Result - Health and Scheduler Engines Use Effect Adapters

## Summary

Closed the health/scheduler effect-adapter migration through three child problems. Both engines now use `EffectExecutor`; adapters own concrete HTTP, business-client, and assembler collaborators; guardrail tests prevent regression.

## Done

- P015 migrated `HealthRecoveryEngine` to `HealthRecoveryEffectAdapter`.
- P016 migrated `ScheduledWakeEngine` to `ScheduledWakeEffectAdapter`.
- P017 added health/scheduler boundary guards.

## Verification

- P015 health suite passed with 10 tests.
- P016 scheduler suite passed with 7 tests.
- P017 combined boundary/health/scheduler suite passed with 22 tests.
- Worker module compile checks passed during child verification.

## Known Gaps

- none for health/scheduler action engines.

## Artifacts

- `novaic-agent-runtime/task_queue/workers/health_effects.py`
- `novaic-agent-runtime/task_queue/workers/scheduler_effects.py`
- `novaic-agent-runtime/task_queue/workers/health_recovery.py`
- `novaic-agent-runtime/task_queue/workers/scheduled_wake.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/tests/test_pr340_action_engine_effect_boundaries.py`
