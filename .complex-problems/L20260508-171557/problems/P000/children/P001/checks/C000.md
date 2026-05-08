# P001 Check

## Summary

P001 is successful. Worker mode selection now goes through a business-agnostic `WorkerAssemblySpecRegistry`, while concrete worker construction has been moved out to `assembly_factories.py`. The old registry-facing module no longer owns business handler wiring.

## Evidence

- Added `novaic-agent-runtime/task_queue/workers/assembly_specs.py` with `WorkerAssemblySpec` and `WorkerAssemblySpecRegistry`.
- Added `novaic-agent-runtime/task_queue/workers/assembly_factories.py` for concrete process construction.
- Replaced `novaic-agent-runtime/task_queue/workers/worker_assemblies.py` with a small spec-backed registry and compatibility wrapper functions.
- Updated tests to verify the boundary:
  - `novaic-agent-runtime/tests/test_pr302_session_outbox_worker_production_wiring.py`
  - `novaic-agent-runtime/tests/test_pr338_business_handlers_lifecycle_free.py`
  - `novaic-agent-runtime/tests/test_pr340_action_engine_effect_boundaries.py`

## Criteria Map

- Assembly spec substrate exists: satisfied by `assembly_specs.py`.
- Worker assembly entrypoint is declarative/spec-backed: satisfied by `WORKER_ASSEMBLY_SPECS` and `WORKER_ASSEMBLIES` in `worker_assemblies.py`.
- Concrete handler wiring is not in the registry-facing module: satisfied by moving the construction details to `assembly_factories.py` and adding tests that ban handler constructors from `worker_assemblies.py`.
- Runtime roster remains authoritative for exposed worker modes: satisfied by deriving `WORKER_ASSEMBLIES` from `RUNTIME_WORKER_MODES`.

## Execution Map

Verified with:

```bash
pytest -q tests/test_pr340_assembly_helpers.py tests/test_pr337_worker_command_registry.py tests/test_pr302_session_outbox_worker_production_wiring.py tests/test_pr340_action_engine_effect_boundaries.py tests/test_pr338_business_handlers_lifecycle_free.py tests/test_pr339_worker_startup_db_retry.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/ci/lint_runtime_worker_supervision.py
```

Observed:

```text
32 passed in 0.33s
lint_runtime_worker_supervision OK
```

## Stress Test

The main residual risk is that concrete assembly logic remains large, but this is now isolated behind a stable substrate. Later tickets can reduce concrete factories without reworking mode dispatch.

## Residual Risk

No blocker for this ticket. Factory internals remain intentionally out of scope for P001 and are covered by later tickets on effect plans, policies, and business DSL boundaries.

## Result IDs

- `R000`
