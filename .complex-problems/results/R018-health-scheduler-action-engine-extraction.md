# R018: Health/Scheduler Action Engine Extraction Result

## Outcome

Health and scheduler handlers now act as tick-job DSL adapters over injected
action engines.

- `HealthRecoveryEngine` owns Queue recovery HTTP client construction,
  `X-Internal-Key` injection, recover-all calls, metrics updates, logging, and
  cleanup.
- `ScheduledWakeEngine` owns due-agent scanning, scheduled wake metadata and
  idempotency key derivation, DispatchAssembler calls, dispatch metrics, and
  dispatch error classification.
- `HealthRecoveryHandler` and `ScheduledWakeHandler` now only decode typed tick
  jobs and delegate to injected engines.
- `worker_assemblies.py` owns BusinessClient, DispatchAssembler, recovery
  engine, scheduled wake engine, and cleanup construction.

## Files Changed

- `novaic-agent-runtime/task_queue/workers/health_recovery.py`
- `novaic-agent-runtime/task_queue/workers/scheduled_wake.py`
- `novaic-agent-runtime/task_queue/workers/health_worker.py`
- `novaic-agent-runtime/task_queue/workers/scheduler_worker.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- health/scheduler tests and residue guards.
