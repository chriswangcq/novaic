# R017: Task/Saga Handler Engine Injection Result

## Outcome

Task and saga handler modules now act as typed job DSL adapters over injected
engines.

- `TaskExecutionHandler` constructor accepts `topics`, `poll_interval`,
  `worker_id`, `TaskExecutionEngine`, and `TaskWorkerMetrics`.
- `SagaLaunchHandler` constructor accepts `saga_types`, `poll_interval`,
  `worker_id`, `SagaLaunchEngine`, and `SagaWorkerMetrics`.
- Task/saga client construction, retry policy construction, engine
  construction, logging closure, source wiring, and cleanup moved to
  `worker_assemblies.py`.
- Business handler modules no longer import or mention Queue/Business client
  classes, retry policy, runtime dependencies, service URLs, or timeout config.

## Files Changed

- `novaic-agent-runtime/task_queue/workers/task_worker.py`
- `novaic-agent-runtime/task_queue/workers/saga_worker.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- task/saga handler tests and boundary guard tests.
