# P001 Result - Generic FSM Worker Substrate Boundary Audit

## Summary

The reusable substrate is substantially clean. `queue_service/worker` and `queue_service/fsm/core.py` are business-agnostic and use explicit ports/state/event inputs. The main remaining gap is not inside the generic substrate but in the application assembly layer: `task_queue/workers/worker_assemblies.py` is large and directly constructs service clients, DB repositories, metrics servers, and business engines. This is acceptable as an application composition root, but it is not yet the "tiny declarative assembly DSL" ideal.

## Done

- Inspected generic worker contracts and lifecycle loops.
- Inspected generic FSM primitives and SQLite store.
- Inspected worker command registry and assembly layer.
- Searched substrate files for task/saga/session/business/cortex/http/sqlite leakage.

## Verification

- `queue_service/worker/contracts.py:1-5` explicitly states the module must not import task/saga/session business modules; the file defines generic `WorkerJob`, `WorkerResult`, `WorkerJobSpec`, `JobSource`, `JobHandler`, and `JobReporter`.
- `queue_service/worker/generic_worker.py:31-144` owns poll/handle/report mechanics without domain branching.
- `queue_service/worker/concurrent_worker.py:20-170` owns bounded concurrency without task/saga-specific branching.
- `queue_service/fsm/core.py:1-65` is IO-free and takes explicit state/event/reducer/context.
- `queue_service/fsm/sqlite_store.py:42-48` is table/column configured and states that values flow through explicit constructor configuration rather than clocks/env/external state.
- `wc -l` shows generic substrate size is modest: `queue_service/worker/*.py` totals 697 lines; `queue_service/fsm/core.py` is 65 lines.
- Gap evidence: `task_queue/workers/worker_assemblies.py` is 652 lines and contains application-specific imports/construction such as `BusinessClient`, `TaskQueueClient`, `SagaOrchestrator`, `Database`, `start_metrics_http_server`, and `get_assembler`.

## Known Gaps

- `worker_assemblies.py` is still a thick imperative composition root. It is much better than business handlers owning lifecycle, but it is not yet a fully declarative component assembly DSL.
- Startup DB retry policy lives in `worker_assemblies.py` (`_connect_db_with_schema_retry`) rather than a shared app-infra DB connector policy module.
- The generic `FsmSqliteStore` is generic, but still low-level SQL oriented; it is a store substrate, not a full event-sourced application runtime that owns migrations, replay, and invariant checking end-to-end.

## Artifacts

- `find queue_service/worker queue_service/fsm task_queue/workers -maxdepth 2 -type f`
- `wc -l queue_service/worker/*.py queue_service/fsm/*.py task_queue/workers/command_specs.py task_queue/workers/process_runner.py task_queue/workers/registry.py task_queue/workers/worker_assemblies.py`
- `rg -n "Task|Saga|Session|Business|Cortex|Queue|agent|wake|saga|task|session|business|cortex|http|sqlite|Database|ServiceConfig" ...`
