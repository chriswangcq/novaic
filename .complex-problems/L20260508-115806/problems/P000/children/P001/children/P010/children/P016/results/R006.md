# P016 Result - Scheduler Engine Effect Adapter Migration

## Summary

Migrated `ScheduledWakeEngine` to explicit effects. Business due-agent scans and dispatch assembler calls now live in `ScheduledWakeEffectAdapter`; the engine keeps wake metadata/idempotency calculation, metrics, and dispatch-result interpretation.

## Done

- Added `task_queue/workers/scheduler_effects.py` with `ScheduledWakeEffectAdapter`.
- Refactored `ScheduledWakeEngine` to accept `effect_executor`.
- Replaced direct collaborator calls with:
  - `scheduler.get_due_for_wake`
  - `scheduler.dispatch_wake`
- Updated `assemble_scheduler_worker` to wire the scheduler adapter.
- Updated scheduler dispatch/generic worker tests to use adapter-based setup.

## Verification

- `pytest -q tests/test_scheduler_dispatch.py tests/test_pr329_scheduler_generic_worker.py` passed with 7 tests.
- `python -m compileall -q task_queue/workers/scheduled_wake.py task_queue/workers/scheduler_effects.py task_queue/workers/worker_assemblies.py` passed.
- `rg -n "self\\.business_client|self\\.assembler|business_client:|assembler:|assemble_and_dispatch_sync\\(|\\.get_due_for_wake\\(" task_queue/workers/scheduled_wake.py` returned no matches.

## Known Gaps

- none for scheduler action engine migration.
- Automated health/scheduler boundary guards are covered by P017.

## Artifacts

- `novaic-agent-runtime/task_queue/workers/scheduler_effects.py`
- `novaic-agent-runtime/task_queue/workers/scheduled_wake.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/tests/test_scheduler_dispatch.py`
- `novaic-agent-runtime/tests/test_pr329_scheduler_generic_worker.py`
