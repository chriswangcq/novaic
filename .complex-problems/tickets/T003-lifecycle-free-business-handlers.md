# T003: Lifecycle-Free Business Handlers

Status: done
Problem: P003

## Objective

Move worker lifecycle construction out of business worker classes and into
`WorkerRegistry`/component assembly.

## Scope

- `task_queue/workers/task_worker.py`
- `task_queue/workers/saga_worker.py`
- `task_queue/workers/health_worker.py`
- `task_queue/workers/scheduler_worker.py`
- `task_queue/workers/registry.py`
- worker boundary tests

## Expected Result

Business modules contain sources and handlers, not worker process/lifecycle
assembly.

## Verification

- Static tests reject business module imports/usages of `GenericWorker`,
  `ConcurrentGenericWorker`, `WorkerRuntime`, `WorkerRuntimeConfig`,
  `SyntheticJobSource`, `NoopReporter`, and `ShutdownController`.
- Existing targeted worker tests pass.
- Full runtime pytest passes.

## Execution Notes

- Renamed business entrypoints to handler names:
  `TaskExecutionHandler`, `SagaLaunchHandler`, `HealthRecoveryHandler`, and
  `ScheduledWakeHandler`.
- Deleted business-owned `run()` / `shutdown()` lifecycle wrappers.
- Moved GenericWorker/ConcurrentGenericWorker assembly for task, saga, health,
  and scheduler into `task_queue/workers/registry.py`.
- Added `tests/test_pr338_business_handlers_lifecycle_free.py` to lock the
  physical boundary.
- Verification: `python -m compileall -q task_queue/workers queue_service/worker tests`
  and targeted pytest suite passed (`36 passed`).
