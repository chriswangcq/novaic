# P003 Result - Effect Adapter And Assembly Guardrails

## Summary

Guardrails were strengthened so future edits cannot silently move concrete side effects or worker lifecycle construction back into business engines or business assembly.

## Done

- Extended `tests/test_pr340_action_engine_effect_boundaries.py`.
- Added guard that `worker_assemblies.py` delegates lifecycle construction to helper builders.
- Added guard that direct worker lifecycle primitives are allowed in `assembly_helpers.py` but forbidden in `worker_assemblies.py`.
- Added guard that `assembly_helpers.py` remains business-agnostic.
- Added guard that concrete protocol clients live in effect adapter modules, not action engines.

## Verification

- `pytest -q tests/test_pr340_action_engine_effect_boundaries.py tests/test_pr340_assembly_helpers.py` -> 13 passed.
- `pytest -q tests/test_pr340_worker_effect_plan.py tests/test_pr340_action_engine_effect_boundaries.py tests/test_pr340_assembly_helpers.py tests/test_pr331_task_worker_handler_cutover.py tests/test_pr333_saga_worker_handler_cutover.py tests/test_pr328_health_generic_worker.py tests/test_pr329_scheduler_generic_worker.py tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr326_session_outbox_generic_worker.py tests/test_pr327_saga_outbox_generic_worker.py tests/test_health_dispatch.py tests/test_scheduler_dispatch.py tests/test_pr286a_session_outbox_worker.py` -> 58 passed.
- `python -m compileall -q tests/test_pr340_action_engine_effect_boundaries.py task_queue/workers` -> passed.
- `rg -n "GenericWorker\\(|ConcurrentGenericWorker\\(|SyntheticJobSource\\(|WorkerRuntimeConfig\\(|ShutdownController\\(|WorkerRuntime\\(|NoopReporter\\(|ResultLoggingReporter\\(" task_queue/workers/worker_assemblies.py` -> no matches.

## Known Gaps

- none for P003.

## Artifacts

- `novaic-agent-runtime/tests/test_pr340_action_engine_effect_boundaries.py`
