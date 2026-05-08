# Result: Current Runtime Is Not Pure DSL Yet

## Summary

Current code is not “pure DSL”. It is a mixed but much cleaner shape: generic worker substrate + declarative command/roster specs + explicit effect adapters + imperative Python action engines and hand-written worker assemblies. The important boundary improvement is real, but business/process behavior is not reduced to only DSL rows.

## Done

- Audited worker command specs, runtime roster, worker assemblies, generic worker helpers, action engines, effect contracts, saga definitions, and task handlers.
- Classified the current shape into DSL-like areas, acceptable component substrate, and remaining imperative business/process logic.
- Ran targeted tests that enforce effect boundary and assembly helper constraints.

## Verification

- Size snapshot for the relevant worker/action/effect layer:
  - `worker_assemblies.py`: 557 lines.
  - `assembly_helpers.py`: 232 lines.
  - `task_execution.py`: 432 lines.
  - `saga_launch.py`: 121 lines.
  - `health_recovery.py`: 103 lines.
  - `scheduled_wake.py`: 218 lines.
  - Effect adapters: `task_effects.py` 108 lines, `saga_effects.py` 55 lines, `health_effects.py` 66 lines, `scheduler_effects.py` 38 lines.
  - Generic effect substrate: `queue_service/worker/effects.py` 122 lines.
- DSL-like/spec evidence:
  - `task_queue/workers/command_specs.py:32-63` defines `WorkerOption` and `WorkerSpec`.
  - `task_queue/workers/registry.py:34-108` declares worker command specs and maps them to build functions.
  - `task_queue/workers/runtime_roster.py:22-29` and `:32-133` declare worker modes and process roster.
  - `task_queue/saga.py:45-75` and `:94-173` define `SagaStep` / `SagaDefinition` as a fluent saga DSL, but callbacks are still Python callables.
  - `queue_service/worker/effects.py:10-32` defines `WorkerEffect` / `EffectPlan`.
- Component substrate evidence:
  - `task_queue/workers/assembly_helpers.py:107-232` owns generic worker construction helpers (`build_generic_worker`, `build_concurrent_worker`, synthetic worker builders).
  - `queue_service/worker/effects.py:74-118` owns generic effect execution contracts.
- Imperative/business process evidence:
  - `task_queue/workers/worker_assemblies.py:49-557` still manually instantiates clients, adapters, engines, handlers, DBs, and cleanup functions per worker.
  - `task_queue/workers/task_execution.py:28-425` still owns heartbeat, idempotency branching, retry/failure/completion sequencing, saga step adaptation, loops, and direct `_effect(...)` calls.
  - `task_queue/workers/saga_launch.py:17-121` still owns heartbeat, DAG publish loop, state advancement, and direct `_effect(...)` calls.
  - `task_queue/workers/scheduled_wake.py:39-218` still owns due-wake scanning, dispatch classification, metrics mutation, and direct `_effect(...)` calls.
  - `task_queue/workers/health_recovery.py:32-72` still owns recovery orchestration and direct effect execution.
  - `task_queue/handlers/*.py` still uses Python handler registration and concrete handler functions; it is not a pure declarative behavior table.
- Effect-plan state:
  - `EffectPlan` exists and is tested.
  - Action engines still call `execute_effect(...)` directly (`task_execution.py:424-425`, `saga_launch.py:120-121`, `scheduled_wake.py:217-218`, `health_recovery.py:72`), so behavior is not uniformly “decision/plan first, execution outside”.
- Test evidence:
  - `pytest -q tests/test_pr340_worker_effect_plan.py tests/test_pr340_assembly_helpers.py tests/test_pr340_action_engine_effect_boundaries.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/test_pr338_business_handlers_lifecycle_free.py`
  - Result: `34 passed in 0.24s`.

## Known Gaps

- Not pure DSL: worker assembly is still hand-written Python.
- Not plan-first: action engines still directly execute effects instead of emitting `EffectPlan`/decision objects for an outer runner.
- Not pure business DSL: saga definitions use DSL classes but rely on Python callback functions for payload building, decisions, conditions, and parallel task construction.
- Task handlers remain Python registry functions, not generated/spec-derived behavior tables.
- Current tests prove explicit dependency boundaries and generic substrate separation; they do not assert “business code only DSL”.

## Artifacts

- `.complex-problems/L20260508-165336/artifacts/P002-ticket.md`
- Static inspections over worker assembly, action engines, effect contracts, saga definitions, and handler registry.
