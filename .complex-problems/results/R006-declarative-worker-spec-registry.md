# R006: Declarative WorkerSpec Registry Result

## Outcome

P006 is closed through P011/P012/P013:

- P011 replaced per-worker parser callbacks with immutable `WorkerOption` data.
- P012 moved concrete worker process assembly out of `registry.py` and into
  component-level `worker_assemblies.py` factories.
- P013 updated tests/docs that still encoded old bespoke `_run_*worker` and
  `_configure_*` registry shapes.

`task_queue/workers/registry.py` is now a small declarative registry of
`WorkerSpec` entries. `main_novaic.py` delegates worker modes through
`run_worker_registry_command()`, which builds a `WorkerProcessSpec` and sends it
through the shared process runner.

## Files Changed

- `novaic-agent-runtime/task_queue/workers/command_specs.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/task_queue/workers/registry.py`
- `novaic-agent-runtime/main_novaic.py`
- worker registry/lifecycle tests
- current worker architecture docs and PR-338 phase bill

## Remaining Parent Scope

P007 still owns final parent residue audit and P002 closure evidence.
