# C002: Business-Only DSL Worker Architecture Check

## Status

Success.

## Criteria Map

- Business worker modules no longer own lifecycle methods or construct generic
  workers:
  - Evidence: `test_pr338_business_handlers_lifecycle_free.py`; final scan for
    `GenericWorker`, `WorkerRuntimeConfig`, `SyntheticJobSource`, `run`, and
    shutdown tokens returned no matches in business handlers.
- Worker jobs and outcomes are typed/spec-shaped:
  - Evidence: P004, `WorkerJobSpec`, `WorkerJob`, `WorkerResult`, and handler
    tests for wrong/missing job contracts.
- Task execution protocol is infrastructure:
  - Evidence: `TaskExecutionEngine` owns heartbeat, idempotency, retry,
    complete/fail, and saga task payload adaptation; `TaskExecutionHandler`
    only decodes and delegates.
- Saga launch protocol is infrastructure:
  - Evidence: `SagaLaunchEngine` owns heartbeat, DAG publish, and
    mark-launched/failed protocol; `SagaLaunchHandler` only decodes and
    delegates.
- Scheduler and health handlers expose small action specs:
  - Evidence: `HealthRecoveryHandler` and `ScheduledWakeHandler` delegate to
    `HealthRecoveryEngine` and `ScheduledWakeEngine`.
- Registry is declarative WorkerSpec data:
  - Evidence: P006/P011-P013, `WorkerSpec`, `WorkerOption`, component assembly
    factories, and registry residue guards.
- Residue guards reject old lifecycle methods, class names, compatibility
  wrappers, and replaced raw job/protocol patterns:
  - Evidence: P014-P019 checks and `test_pr338_business_handlers_lifecycle_free.py`.
- Runtime tests pass:
  - Evidence: `pytest -q` in `novaic-agent-runtime` -> `508 passed`.

## Stress Check

- Hidden compromise found during P007: handlers were lifecycle-free but still
  constructed clients/action engines. P017/P018 removed that gap.
- Stale label residue found during P007: `task-sync`/`saga-sync` worker labels.
  P016 removed them.
- Current residual risk: new worker work can regress the boundary if it bypasses
  `worker_assemblies.py`; boundary tests now guard against that.
