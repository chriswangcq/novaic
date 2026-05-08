# P017 Result - Health/Scheduler Boundary Guards

## Summary

Extended the PR-340 action-engine boundary guard suite to cover health and scheduler engines. Tests now reject direct HTTP/client/assembler ownership and assert health/scheduler adapter wiring in worker assembly.

## Done

- Updated `tests/test_pr340_action_engine_effect_boundaries.py`.
- Added health checks for forbidden `httpx` / `internal_sync_client` imports, queue URL/internal-key constructor params, and `_client` ownership.
- Added scheduler checks for forbidden `business_client` / `assembler` constructor params, self-owned collaborators, and direct collaborator calls.
- Extended assembly checks for `HealthRecoveryEffectAdapter` and `ScheduledWakeEffectAdapter`.

## Verification

- `pytest -q tests/test_pr340_action_engine_effect_boundaries.py tests/test_health_dispatch.py tests/test_pr328_health_generic_worker.py tests/test_scheduler_dispatch.py tests/test_pr329_scheduler_generic_worker.py` passed with 22 tests.
- `python -m compileall -q task_queue/workers tests/test_pr340_action_engine_effect_boundaries.py` passed.

## Known Gaps

- none for health/scheduler boundary guards.

## Artifacts

- `novaic-agent-runtime/tests/test_pr340_action_engine_effect_boundaries.py`
