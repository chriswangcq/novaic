# Require Store Follow-up Result

## Summary

Removed the silent missing-store fallback from workspace scope lifecycle transitions.

## Done

- Added `Workspace._require_operational_store()`.
- `Workspace.complete_child_scope(...)` now requires the store before writing `summary.md` or updating metadata.
- `Workspace.archive_root_scope(...)` now requires the store before writing root summary or marking archived.
- Removed lifecycle uses of `getattr(self, "_operational_store", None)`.
- Added a test proving `complete_child_scope` fails loudly and does not write partial summary output when no operational store is present.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_scope_state.py novaic-cortex/tests/test_operational_store.py`
  - Result: `27 passed in 0.15s`.
- Static search:
  - No `getattr(self, "_operational_store", None)` remains in `workspace.py`.
  - No live `transition_log_path=self._scope_state_log_path` remains in `workspace.py`.

## Known Gaps

- None inside this follow-up. Phase 2C still owns old NDJSON read/path cleanup.

## Artifacts

- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_scope_state.py`
