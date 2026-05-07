# R014: Worker Source Adapter Extraction Result

## Outcome

Task and saga source adapters were moved out of business handler modules:

- `TaskQueueJobSource` moved from `task_worker.py` to `task_sources.py`.
- `SagaClaimSource` moved from `saga_worker.py` to `saga_sources.py`.
- `worker_assemblies.py` imports source adapters from those component modules.
- Business handler modules now expose job specs and handler/engine delegation,
  not source polling adapters.

## Files Changed

- `novaic-agent-runtime/task_queue/workers/task_sources.py`
- `novaic-agent-runtime/task_queue/workers/saga_sources.py`
- `novaic-agent-runtime/task_queue/workers/task_worker.py`
- `novaic-agent-runtime/task_queue/workers/saga_worker.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- worker source/handler boundary tests.
