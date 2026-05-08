## Success Check: P001 Generic FSM Worker Substrate Boundaries

### Summary

The generic FSM and worker substrate audit is successful. The core substrate under `queue_service/worker` and `queue_service/fsm/core.py` is substantially business-agnostic and keeps lifecycle, polling, concurrency, metrics, shutdown, state transition, and persistence primitives outside task/saga/session business handlers. The key remaining gap is not in the substrate itself, but in the application composition root: `task_queue/workers/worker_assemblies.py` is still a thick imperative assembly layer rather than a compact declarative worker DSL.

### Evidence

- `queue_service/worker/contracts.py:1-5` explicitly declares the module business-agnostic and forbids task/saga/session business imports. The contracts expose generic `WorkerJob`, `WorkerResult`, `WorkerJobSpec`, `JobSource`, `JobHandler`, and `JobReporter`.
- `queue_service/worker/generic_worker.py:31-144` implements the lifecycle loop generically: fetch job, handle job, report result, sleep, report metrics, and emit error results.
- `queue_service/worker/concurrent_worker.py:20-170` implements bounded concurrency generically, with no task/saga/session-specific control flow.
- `queue_service/fsm/core.py:1-65` defines generic state, event, decision, reducer, and context primitives. The reducer boundary is explicit.
- `queue_service/fsm/sqlite_store.py:42-48` describes a business-agnostic SQLite table store configured by explicit table/column names, keeping business domain names out of the store class.
- `task_queue/workers/worker_assemblies.py` is 652 lines and imports/configures `BusinessClient`, `TaskQueueClient`, `SagaOrchestrator`, DB repositories, metrics servers, sources, handlers, and retry/startup policy. That makes it a valid composition root, but not yet the final "few-line declarative assembly DSL" form.

### Criteria Map

- `audit current runtime worker/FSM substrate`: satisfied for the core generic substrate.
- `evidence from local code/tests/docs, not memory`: satisfied with local `find`, `wc`, `rg`, and `nl` evidence.
- `identify achieved/not achieved/risk/next optimization tickets`: satisfied. Achieved: core substrate is generic. Not achieved: assembly layer is still thick. Risk: assembly thickness can slowly reintroduce hidden business policy into wiring.

### Execution Map

- `T001` inspected generic substrate file layout and line counts.
- `T001` searched for domain terms and service/config imports across `queue_service/worker`, `queue_service/fsm`, and worker assembly modules.
- `T001` read line-numbered evidence for generic contracts, generic worker loops, FSM primitives, SQLite store boundary, and thick assembly root.
- `R000` recorded the audit findings and gap analysis.

### Stress Test

If a new business worker is added today, it can reuse `GenericWorker` or `ConcurrentGenericWorker` without changing the substrate. However, the developer would probably still copy imperative assembly patterns into `worker_assemblies.py`. That shows the substrate boundary is good, but the assembly DSL is not yet strong enough to make the desired architecture self-enforcing.

### Residual Risk

The substrate is clean enough to proceed with the broader audit. The next optimization ticket should target assembly declarativity: shrink `worker_assemblies.py`, move generic DB startup/retry policy into reusable infrastructure, and make business worker assembly mostly data/spec driven.

### Result IDs

- `R000`
