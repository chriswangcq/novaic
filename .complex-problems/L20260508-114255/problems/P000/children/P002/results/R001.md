## Result: P002 Business DSL Worker Layer Audit

### Done Items

- Inspected business worker handler file sizes:
  - `task_queue/workers/task_worker.py`: 93 lines
  - `task_queue/workers/saga_worker.py`: 81 lines
  - `task_queue/workers/health_worker.py`: 49 lines
  - `task_queue/workers/scheduler_worker.py`: 59 lines
- Inspected action engine file sizes:
  - `task_queue/workers/task_execution.py`: 414 lines
  - `task_queue/workers/saga_launch.py`: 110 lines
  - `task_queue/workers/health_recovery.py`: 127 lines
  - `task_queue/workers/scheduled_wake.py`: 215 lines
- Checked for lifecycle residue and direct infrastructure construction in business handler modules.
- Read line-numbered evidence for task, saga, health, and scheduler handlers plus key action engines.
- Ran targeted guard tests.

### Achieved State

The four top-level business worker handlers have largely reached the intended DSL boundary:

- `task_queue/workers/task_worker.py:16-25` declares `WorkerJobSpec` values for task job kinds.
- `task_queue/workers/task_worker.py:28-93` is a typed handler that decodes a job, delegates actual protocol execution to `TaskExecutionEngine`, and returns `WorkerResult`.
- `task_queue/workers/saga_worker.py:16-20` declares the saga claimed job spec, and `task_queue/workers/saga_worker.py:23-80` delegates launch protocol to `SagaLaunchEngine`.
- `task_queue/workers/health_worker.py:7-49` is a small tick handler around `HealthRecoveryEngine`.
- `task_queue/workers/scheduler_worker.py:7-59` is a small tick handler around `ScheduledWakeEngine`.
- These handler modules do not own worker lifecycle loops, process startup, worker runtime construction, or client construction.

This means the first "business DSL" layer exists: job-kind declarations plus typed handler boundaries are small and explicit.

### Remaining Gap

The deeper business execution layer is not yet "business only DSL" in the strict sense:

- `task_queue/workers/task_execution.py:62-199` owns heartbeat, idempotency acquire/complete/release, retry/fail/complete, metric mutation, and direct task client effects.
- `task_queue/workers/task_execution.py:291-379` directly publishes saga parallel tasks and then waits/polls with `self._deps.sleeper(0.1)`. The dependency is explicit, but the code is still imperative orchestration rather than an effect-plan DSL.
- `task_queue/workers/saga_launch.py:64-110` builds a DAG and directly publishes tasks and marks saga launched/failed.
- `task_queue/workers/health_recovery.py:84-116` owns HTTP client creation and calls `/api/queue/recover/all` directly.
- `task_queue/workers/scheduled_wake.py:78-204` scans due agents, dispatches scheduled wake through the assembler, and records metrics/log outcomes directly.

These are acceptable as explicit action engines, but they are not the final "business code is only declarative decision/effect spec" shape.

### Verification

Targeted tests passed:

```text
pytest -q tests/test_pr338_business_handlers_lifecycle_free.py \
  tests/test_pr331_task_worker_handler_cutover.py \
  tests/test_pr333_saga_worker_handler_cutover.py \
  tests/test_pr328_health_generic_worker.py \
  tests/test_pr329_scheduler_generic_worker.py

22 passed in 0.21s
```

Relevant guard evidence:

- `tests/test_pr338_business_handlers_lifecycle_free.py:57-68` forbids worker lifecycle and execution protocol tokens in the four business handler modules.
- `tests/test_pr338_business_handlers_lifecycle_free.py:85-132` forbids task/saga/health/scheduler handlers from constructing protocol clients, runtime dependencies, HTTP clients, dispatch assemblers, or action clients.
- `tests/test_pr338_business_handlers_lifecycle_free.py:149-167` verifies registry delegates concrete worker construction to `worker_assemblies.py`.

### Artifacts

- `P002-ticket.md`
- This result file.

### Gaps To Carry Forward

- The handler layer is small, but the action engines are still imperative protocol adapters.
- If the desired target is "business only DSL", a later ticket should introduce a declarative action/effect-plan layer so engines produce explicit decisions/effects and infrastructure adapters execute them.
- Current tests enforce handler thinness, but do not yet enforce action-engine declarativity.
