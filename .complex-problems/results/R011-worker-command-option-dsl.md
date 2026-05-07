# R011: Worker Command Option DSL Result

## Outcome

Worker command parser configuration is now declarative data. `WorkerCommand`
contains immutable `WorkerOption` entries, `WorkerRegistry.build_parser()` has a
single generic option application path, and all `_configure_*` functions were
physically removed from `task_queue/workers/registry.py`.

## Files Changed

- `novaic-agent-runtime/task_queue/workers/registry.py`
- `novaic-agent-runtime/tests/test_pr337_worker_command_registry.py`

## Notes

This only closed the parser/options half of P006. Per-worker process assembly
functions still exist and are tracked by P012/P013.
