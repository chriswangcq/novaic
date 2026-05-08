# P020 Result - Assembly DSL Shrink Verification

## Summary

Assembly shrink was verified. The business assembly file no longer directly constructs worker lifecycle primitives, tests now protect helper-backed assembly, and the focused behavior/boundary suite passes.

## Done

- Verified `worker_assemblies.py` has no direct lifecycle primitive construction.
- Verified old text assertions now reject raw constructors in assembly instead of requiring them.
- Re-ran focused task/saga/health/scheduler/outbox/helper/boundary tests.
- Re-ran compile checks for worker substrate and worker modules.
- Recorded line-count evidence.

## Verification

- `rg -n "GenericWorker\\(|ConcurrentGenericWorker\\(|SyntheticJobSource\\(|WorkerRuntimeConfig\\(|ShutdownController\\(|WorkerRuntime\\(|NoopReporter\\(|ResultLoggingReporter\\(" task_queue/workers/worker_assemblies.py` -> no matches.
- `pytest -q tests/test_pr340_assembly_helpers.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr340_action_engine_effect_boundaries.py tests/test_health_dispatch.py tests/test_scheduler_dispatch.py tests/test_pr286a_session_outbox_worker.py` -> 51 passed.
- `python -m compileall -q task_queue/workers queue_service/worker` -> passed.
- `wc -l task_queue/workers/worker_assemblies.py task_queue/workers/assembly_helpers.py` -> `worker_assemblies.py` 557 lines, `assembly_helpers.py` 232 lines.

## Known Gaps

- none for P020.

## Artifacts

- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/task_queue/workers/assembly_helpers.py`
- Focused worker assembly and boundary tests.
