# Health Engine Effect Adapter Migration

## Problem Definition

`HealthRecoveryEngine` still imports `httpx` and `internal_sync_client`, owns an HTTP client cache, and directly calls Queue Service recover-all. This makes the action engine both compute health recovery flow and own external protocol details.

## Proposed Solution

Move HTTP client construction and recover-all POST into `HealthRecoveryEffectAdapter`. Refactor `HealthRecoveryEngine` to accept an `EffectExecutor` and call `health.recover_all`. Keep metrics, logging, and recovery result interpretation in the engine.

## Acceptance Criteria

- `HealthRecoveryEngine` accepts `effect_executor` instead of queue URL/internal key.
- `health_recovery.py` no longer imports `httpx` or `internal_sync_client`.
- `HealthRecoveryEngine` no longer owns `_client` or `_get_client`.
- `assemble_health_worker` wires `HealthRecoveryEffectAdapter` and cleans it up.
- Existing health worker tests pass with adapter-based test setup.

## Verification Plan

- Run `tests/test_health_dispatch.py` and `tests/test_pr328_health_generic_worker.py`.
- Compile health worker modules.
- Scan `health_recovery.py` for old HTTP ownership residue.

## Risks

- Tests currently monkeypatch engine `_get_client`; they must instead use an explicit fake adapter/executor.

## Assumptions

- Non-200 Queue recover-all responses remain non-exception success payloads with status code.
