# R012: Component Worker Assembly DSL Result

## Outcome

Worker process assembly moved out of `task_queue/workers/registry.py` and into
component-level factories in `task_queue/workers/worker_assemblies.py`.

The registry now declares `WorkerSpec` data only:

- mode
- description
- `WorkerOption` data
- `build_process=assemble_*_worker`

`WorkerRegistry` now builds a `WorkerProcessSpec`, and
`run_worker_registry_command()` runs it through the shared
`run_sync_worker_process()` infrastructure.

## Files Changed

- `novaic-agent-runtime/task_queue/workers/command_specs.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/task_queue/workers/registry.py`
- `novaic-agent-runtime/main_novaic.py`
- worker registry / lifecycle tests

## Notes

This is the physical cutover that prevents the registry from owning business
handler construction. Concrete assembly factories still exist, but they are now
component-layer worker assembly code rather than registry branches.
