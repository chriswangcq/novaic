# FSM Worker DSL Boundary Audited

## Summary

Audited the runtime FSM/worker/DSL boundary against live code and the status documentation. The documented spec/plan-driven shape matches the implementation, with accepted Python computation hooks named explicitly rather than hidden as fallback paths.

## Done

- Verified every live path named in `docs/architecture/runtime-fsm-worker-dsl-status.md` exists.
- Scanned for usage of `EffectPlanRunner`, `WorkerAssemblySpec`, `SAGA_CALLBACK_EXTENSION_POINTS`, handler metadata, and policy/spec/plan helper functions.
- Inspected representative action engines:
  - `task_execution.py`
  - `saga_launch.py`
  - `scheduled_wake.py`
  - `health_recovery.py`
- Ran targeted documentation and effect-boundary tests.

## Verification

- Path existence check returned `MISSING=[]`.
- Usage scan confirmed:
  - `EffectPlanRunner` is imported/used by task, saga, scheduler, and health engines.
  - `WorkerAssemblySpec` is used by `worker_assemblies.py`.
  - `SAGA_CALLBACK_EXTENSION_POINTS` is declared in `task_queue/saga.py` and referenced in docs.
  - Policy/spec/plan helper functions are used by the expected engines.
- Inspected action engine slices show engines using pure policy/spec/plan helpers and `EffectPlanRunner`.
- `cd novaic-agent-runtime && PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/test_pr340_runtime_dsl_status_doc.py tests/test_pr340_action_engine_effect_boundaries.py`
  - Passed: 13 tests.

## Known Gaps

None for the documented current architecture. The architecture remains intentionally spec/plan-driven with explicit Python computation hooks, not a future data-only DSL.

## Artifacts

- `docs/architecture/runtime-fsm-worker-dsl-status.md`
- `novaic-agent-runtime/task_queue/workers/task_execution.py`
- `novaic-agent-runtime/task_queue/workers/saga_launch.py`
- `novaic-agent-runtime/task_queue/workers/scheduled_wake.py`
- `novaic-agent-runtime/task_queue/workers/health_recovery.py`
- `novaic-agent-runtime/tests/test_pr340_runtime_dsl_status_doc.py`
- `novaic-agent-runtime/tests/test_pr340_action_engine_effect_boundaries.py`
