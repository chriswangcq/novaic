# R015: Explicit Worker Handler Configuration Result

## Outcome

Worker handler configuration is now explicit at the business/component boundary.

- `TaskExecutionHandler` requires explicit `queue_service_url`,
  `business_url`, `poll_interval`, `timeout`, `saga_step_timeout`,
  `WorkerRuntimeDependencies`, and `RetryPolicy`.
- `SagaLaunchHandler`, `HealthRecoveryHandler`, and `ScheduledWakeHandler`
  require explicit constructor inputs and no longer fall back to
  `ServiceConfig`.
- `TaskExecutionEngine` receives `saga_step_timeout` as constructor input
  and no longer reads process globals while executing saga parallel waits.
- `wake/assembler_factory.py` receives `business_url` and
  `queue_service_url` explicitly, making scheduler dispatch assembly
  reproducible from handler inputs.
- `worker_assemblies.py` remains the single process assembly boundary that
  reads `ServiceConfig` and injects concrete values into handlers.
- Retired handler names with `sync` suffixes were removed.

## Files Changed

- `novaic-agent-runtime/task_queue/workers/task_worker.py`
- `novaic-agent-runtime/task_queue/workers/saga_worker.py`
- `novaic-agent-runtime/task_queue/workers/health_worker.py`
- `novaic-agent-runtime/task_queue/workers/scheduler_worker.py`
- `novaic-agent-runtime/task_queue/workers/task_execution.py`
- `novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- worker boundary and handler tests.
