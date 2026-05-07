# R001: Worker Registry Perfect-Shape Result

Problem: P001
Ticket: T001
Status: complete
Date: 2026-05-07

## Result

Agent Runtime worker command assembly is now registry-owned.

Implemented:

- `novaic-agent-runtime/task_queue/workers/registry.py`
  - `WorkerCommandDependencies`
  - `WorkerCommand`
  - `WorkerRegistry`
  - `build_runtime_worker_registry()`
- Registered modes:
  - `task-worker`
  - `saga-worker`
  - `session-outbox-worker`
  - `saga-outbox-worker`
  - `health`
  - `scheduler`
- `novaic-agent-runtime/main_novaic.py`
  - removed per-worker run functions
  - removed per-worker mode branches
  - delegates worker modes through `run_worker_mode_if_registered`
- `novaic-agent-runtime/novaic-agent-runtime.spec`
  - includes `task_queue.workers.registry`
- `novaic-agent-runtime/queue_service/worker/generic_worker.py`
  - exposes `shutdown()` alias for the shared process runner contract
- `novaic-agent-runtime/queue_service/worker/concurrent_worker.py`
  - exposes `shutdown()` alias for the shared process runner contract

## Tests Added Or Updated

- Added `novaic-agent-runtime/tests/test_pr337_worker_command_registry.py`.
- Updated production/residue tests that previously asserted old
  `main_novaic.py` per-worker functions.

## Deleted Shape

The previous shape of one `run_xxx_worker()` function and one
`elif mode == "<worker>"` branch per worker in `main_novaic.py` is gone.

The remaining worker shape is:

```text
main_novaic.py
  -> run_worker_mode_if_registered(mode, argv)
  -> WorkerRegistry
  -> WorkerCommand.configure(parser, deps)
  -> WorkerCommand.run(args, deps)
  -> run_sync_worker_process(WorkerProcessSpec(...))
```
