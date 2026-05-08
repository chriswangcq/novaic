# P015 Result - Health Engine Effect Adapter Migration

## Summary

Migrated `HealthRecoveryEngine` to explicit effects. HTTP client creation and Queue recover-all protocol calls now live in `HealthRecoveryEffectAdapter`; the engine only coordinates metrics, logging, and recovery result interpretation.

## Done

- Added `task_queue/workers/health_effects.py` with `HealthRecoveryEffectAdapter`.
- Refactored `HealthRecoveryEngine` to accept `effect_executor` and call `health.recover_all`.
- Removed direct `httpx`, `internal_sync_client`, `_client`, `_get_client`, URL, and internal-key ownership from `health_recovery.py`.
- Updated `assemble_health_worker` to wire the adapter and close it during cleanup.
- Updated health dispatch/generic worker tests to use explicit adapter/effect setup.

## Verification

- `pytest -q tests/test_health_dispatch.py tests/test_pr328_health_generic_worker.py` passed with 10 tests.
- `python -m compileall -q task_queue/workers/health_recovery.py task_queue/workers/health_effects.py task_queue/workers/worker_assemblies.py` passed.
- `rg -n "httpx|internal_sync_client|_client|_get_client|queue_service_url|queue_internal_key" task_queue/workers/health_recovery.py` returned no matches.

## Known Gaps

- none for health action engine migration.
- Automated health/scheduler boundary guard tests are covered by P017.

## Artifacts

- `novaic-agent-runtime/task_queue/workers/health_effects.py`
- `novaic-agent-runtime/task_queue/workers/health_recovery.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/tests/test_health_dispatch.py`
- `novaic-agent-runtime/tests/test_pr328_health_generic_worker.py`
