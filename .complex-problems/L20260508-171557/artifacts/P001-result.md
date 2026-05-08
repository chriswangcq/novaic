# Result: Worker Assembly Specs Implemented

## Summary

Implemented the first DSL closure slice: registry-facing worker assembly is now spec-backed. `worker_assemblies.py` shrank from the old hand-written assembly body to a thin spec/interpreter surface, while concrete construction was moved into `assembly_factories.py` and preserved behind existing public `assemble_*` functions.

## Done

- Added `task_queue/workers/assembly_specs.py` with `WorkerAssemblySpec` and `WorkerAssemblySpecRegistry`.
- Moved concrete worker process construction into `task_queue/workers/assembly_factories.py`.
- Replaced `task_queue/workers/worker_assemblies.py` with `WORKER_ASSEMBLY_SPECS`, `WORKER_ASSEMBLIES`, `assemble_worker_process(...)`, and thin compatibility wrappers for each runtime mode.
- Re-exported `_connect_db_with_schema_retry` through `worker_assemblies.py` for existing startup retry tests.
- Updated tests so the guard now expects `worker_assemblies.py` to be thin and concrete lifecycle construction to live behind factories/specs.

## Verification

- `pytest -q tests/test_pr340_assembly_helpers.py tests/test_pr337_worker_command_registry.py tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr340_action_engine_effect_boundaries.py tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr339_worker_startup_db_retry.py`
  - Result: `32 passed in 0.33s`.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/ci/lint_runtime_worker_supervision.py`
  - Result: `lint_runtime_worker_supervision OK`.
- Focused diff in `novaic-agent-runtime`:
  - `worker_assemblies.py` changed from old direct assembly to thin specs/wrappers.
  - Added `assembly_specs.py`.
  - Added `assembly_factories.py`.

## Known Gaps

- Concrete factory implementation still exists in `assembly_factories.py`; this ticket intentionally moved the registry-facing assembly surface to specs first. Later tickets reduce action engines and policies behind those factories.

## Artifacts

- `novaic-agent-runtime/task_queue/workers/assembly_specs.py`
- `novaic-agent-runtime/task_queue/workers/assembly_factories.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- Updated worker assembly/registry tests.
