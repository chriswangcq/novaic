# Phase 2B Result

## Summary

Cut live workspace scope transition writes over to operational SQLite while preserving existing metadata phase transition behavior.

## Done

- Added `novaic-cortex/novaic_cortex/scope_transition_events.py`.
  - Parses logical scope paths into root/scope IDs.
  - Builds the public transition-history payload shape.
  - Appends `scope_state_transition` events into `OperationalSqliteStore.scope_events`.
  - Provides a SQLite-backed list helper for Phase 2C read cutover.
- Updated `scope_state.transition(...)` and `mark_archived(...)`.
  - Accept optional `operational_store`.
  - Reject passing both `operational_store` and `transition_log_path`.
  - Non-noop transitions append to SQLite when `operational_store` is provided.
  - Noop transitions still do not append.
- Updated live workspace lifecycle methods.
  - `Workspace.complete_child_scope(...)` passes `operational_store`.
  - `Workspace.archive_root_scope(...)` passes `operational_store`.
  - They no longer pass `transition_log_path=self._scope_state_log_path`.
- Updated `test_scope_state.py` with SQLite-specific coverage.

## Verification

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_scope_state.py novaic-cortex/tests/test_operational_store.py`
  - Result: `26 passed in 0.16s`.
- `python3 -m py_compile novaic-cortex/novaic_cortex/scope_transition_events.py novaic-cortex/novaic_cortex/scope_state.py novaic-cortex/novaic_cortex/workspace.py`
  - Result: passed.
- Static search:
  - No live `transition_log_path=self._scope_state_log_path` remains in `workspace.py`.
  - Live workspace paths now show `operational_store=getattr(self, "_operational_store", None)`.

## Known Gaps

- Old `scope_state_log.py`, `/v1/scope/history`, `scope_state_log_path`, and NDJSON tests still exist. Phase 2C owns history read cutover and cleanup.
- Workspace currently uses `getattr(..., None)` so direct low-level tests without registry wiring still run. Phase 2C or Phase 3 should decide whether to fail hard when operational store is absent on live lifecycle paths.

## Artifacts

- `novaic-cortex/novaic_cortex/scope_transition_events.py`
- `novaic-cortex/novaic_cortex/scope_state.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_scope_state.py`
