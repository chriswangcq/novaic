# Root and wake lifecycle event emission completed

## Summary

Cut the API root/wake lifecycle paths onto ContextEvent writes. `/v1/scope/create` now appends `RootInitialized` for root scopes and `WakeStarted` for wake child scopes; `/v1/scope/end` appends `WakeArchived` before wake archival. Idempotent retries reuse stable event keys and do not duplicate lifecycle events.

## Done

- Added API-level ContextEvent writer factory with explicit clock/id provider functions at the Cortex boundary.
- Added root scope identity helpers for child scope paths.
- Wired `/v1/scope/create`:
  - root scopes append `RootInitialized`;
  - wake child scopes append `WakeStarted`;
  - idempotent existing roots/wakes re-run writer append and rely on stable idempotency keys.
- Wired `/v1/scope/end`:
  - wake root/child archive paths append `WakeArchived` before structural archive;
  - idempotent archived wake paths also reconcile the event through the same idempotency key.
- Added `novaic-cortex/tests/test_context_event_api_lifecycle.py`.

## Verification

- Focused lifecycle/writer/wake API tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_lifecycle.py tests/test_context_event_writer.py tests/test_pr67_wake_child_api.py -q`
  - Result: `13 passed in 0.36s`
- Full Cortex suite:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Result: `431 passed in 0.72s`
- Static scan confirmed `api.py` now contains `ContextEventWriter` wiring and lifecycle event assertions exist in tests.

## Residual Risk

- Notification attachment remains open in P030.
- Broader context/tool/skill write cutovers remain open in later Phase 3 children.
- Legacy scope files still exist as transitional artifacts until P028 demotes/deletes them.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_lifecycle.py`
