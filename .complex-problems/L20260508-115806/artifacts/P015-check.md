# P015 Check - Health Engine Effect Adapter Migration

## Summary

P015 is solved. Health recovery HTTP effects are now isolated in `HealthRecoveryEffectAdapter`; `HealthRecoveryEngine` no longer owns protocol clients or Queue URL/internal key state.

## Evidence

- `health_recovery.py` accepts `effect_executor` and calls `health.recover_all`.
- `health_effects.py` owns `httpx`, `internal_sync_client`, cached client, headers, and recover-all POST.
- Worker assembly wires and cleans up `HealthRecoveryEffectAdapter`.
- Focused health tests passed with 10 tests.
- Residue scan found no old HTTP ownership tokens in `health_recovery.py`.

## Criteria Map

- Engine owns no HTTP client construction -> satisfied by code refactor and residue scan.
- Recover-all side effect runs through `EffectExecutor` -> satisfied by `execute_effect(..., "health.recover_all", ...)`.
- Health tests pass -> satisfied by focused test run.
- Assembly wires adapter explicitly -> satisfied by `assemble_health_worker`.

## Execution Map

- T008 -> R005: migrated health action engine and tests.

## Stress Test

- Missing adapter handler -> generic `EffectExecutor` failure path would surface as `recover_all_failed`.
- Header injection regression -> existing health test now checks `HealthRecoveryEffectAdapter`.
- Engine HTTP residue regression -> P017 will automate the guard; manual scan is already clean.

## Residual Risk

- none for health engine migration.

## Result IDs

- R005

## Blocking Gaps

- none
