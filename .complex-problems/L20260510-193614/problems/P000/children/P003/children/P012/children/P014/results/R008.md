# Phase 2C1 Result

## Summary

Cut `/v1/scope/history` reads from NDJSON to operational SQLite.

## Done

- Updated `novaic-cortex/novaic_cortex/api.py`.
  - `scope_history(...)` now calls `list_scope_transition_events(_registry.operational_store, ...)`.
  - Response now reports `backend: operational_sqlite`.
  - Removed `log_path` response field.
- Added `novaic-cortex/tests/test_scope_history_api.py`.
  - Seeds a SQLite transition event and verifies the API returns it.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_scope_history_api.py novaic-cortex/tests/test_scope_state.py novaic-cortex/tests/test_operational_store.py`
  - Result: `28 passed in 0.35s`.
- `rg -n "scope_state_log|log_path" novaic-cortex/novaic_cortex/api.py novaic-cortex/tests/test_scope_history_api.py`
  - Result: no matches.

## Known Gaps

- Old `scope_state_log_path`, `transition_log_path`, `scope_state_log.py`, and NDJSON tests still exist outside the API path. `P015` owns physical cleanup.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_scope_history_api.py`
