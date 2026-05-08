# P009 Result - Task and Saga Engines Use Effect Adapters

## Summary

Closed the task/saga action-engine effect-adapter migration through three child problems. Both action engines now depend on the generic `EffectExecutor`, adapters own concrete clients, worker assembly wires adapters explicitly, and boundary tests prevent old direct-client patterns from returning.

## Done

- P012 migrated `TaskExecutionEngine` to `TaskExecutionEffectAdapter`.
- P013 migrated `SagaLaunchEngine` to `SagaLaunchEffectAdapter`.
- P014 added automated task/saga action-engine boundary guards.

## Verification

- P012 focused task worker tests passed with 10 tests.
- P013 focused saga worker tests passed with 8 tests.
- P014 combined boundary/task/saga suite passed with 21 tests.
- Worker module compile checks passed during child verification.

## Known Gaps

- none for task/saga action engines.
- Health/scheduler action engines remain under P010.

## Artifacts

- `novaic-agent-runtime/task_queue/workers/task_effects.py`
- `novaic-agent-runtime/task_queue/workers/saga_effects.py`
- `novaic-agent-runtime/task_queue/workers/task_execution.py`
- `novaic-agent-runtime/task_queue/workers/saga_launch.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/tests/test_pr340_action_engine_effect_boundaries.py`
