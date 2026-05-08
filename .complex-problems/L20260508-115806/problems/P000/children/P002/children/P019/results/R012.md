# P019 Result - Worker Assemblies Migrated To Helper Substrate

## Summary

Concrete worker assembly functions now use the generic helper substrate for worker construction. `worker_assemblies.py` keeps business wiring and explicit adapters, while worker lifecycle construction lives in `assembly_helpers.py`.

## Done

- Extended `task_queue/workers/assembly_helpers.py` with explicit-runtime synthetic worker support for outbox workers.
- Migrated task worker assembly to `build_generic_worker`.
- Migrated saga worker assembly to `build_concurrent_worker`.
- Migrated health and scheduler assemblies to `build_synthetic_worker`.
- Migrated session-outbox and saga-outbox assemblies to `build_synthetic_worker_with_runtime`.
- Removed direct `GenericWorker`, `ConcurrentGenericWorker`, `SyntheticJobSource`, `WorkerRuntimeConfig`, `ShutdownController`, `WorkerRuntime`, `NoopReporter`, and `ResultLoggingReporter` construction from `worker_assemblies.py`.
- Updated old text-assertion tests so they guard helper-backed assembly rather than protecting old constructor placement.

## Verification

- `pytest -q tests/test_pr340_assembly_helpers.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_pr340_action_engine_effect_boundaries.py` -> 35 passed.
- `pytest -q tests/test_health_dispatch.py tests/test_scheduler_dispatch.py tests/test_pr286a_session_outbox_worker.py tests/test_pr327_saga_outbox_generic_worker.py` -> 21 passed.
- `python -m compileall -q task_queue/workers` -> passed.
- `rg -n "GenericWorker\\(|ConcurrentGenericWorker\\(|SyntheticJobSource\\(|WorkerRuntimeConfig\\(|ShutdownController\\(|WorkerRuntime\\(|NoopReporter\\(|ResultLoggingReporter\\(" task_queue/workers/worker_assemblies.py` -> no matches.
- `wc -l task_queue/workers/worker_assemblies.py task_queue/workers/assembly_helpers.py` -> `worker_assemblies.py` 557 lines, `assembly_helpers.py` 232 lines.

## Known Gaps

- none for P019.

## Artifacts

- `novaic-agent-runtime/task_queue/workers/assembly_helpers.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- Updated focused worker assembly tests.
