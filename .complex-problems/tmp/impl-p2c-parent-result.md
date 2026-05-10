# P012 T010 Result - Scope History Read Cutover And NDJSON Cleanup

## Summary

Completed the split Phase 2C work. Scope history reads now use operational SQLite, the old scope transition NDJSON surface is physically removed, and the cleanup verification passed.

## Done

- P014 cut `/v1/scope/history` over to `OperationalSqliteStore` through `scope_transition_events.list_scope_transition_events`.
- P015 removed the old scope transition NDJSON module, startup/config surface, transition parameters, and direct tests.
- P015 also made non-noop scope transitions require `operational_store`, preventing silent history-less phase changes.
- P016 verified tests, compilation, exact old-symbol search, and broader log/NDJSON match classification.

## Verification

- P014 success check C009 closed the API read cutover.
- P015 success check C010 closed physical deletion of the old transition-log surface.
- P016 success check C011 closed final cleanup verification.
- The latest targeted suite passed with 31 tests.
- Exact old-symbol search for `scope_state_log`, `scope_state_log_path`, `transition_log_path`, and `scope-state-log-path` returned no matches across live Cortex code, tests, current docs, and startup.

## Known Gaps

- None for Phase 2C.
- Parent Phase 3 active-stack/status authority remains pending and is intentionally outside this result.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/scope_transition_events.py`
- `novaic-cortex/novaic_cortex/scope_state.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/novaic_cortex/registry.py`
- `novaic-cortex/novaic_cortex/main_cortex.py`
- `scripts/start.sh`
- `novaic-cortex/tests/test_scope_history_api.py`
- `novaic-cortex/tests/test_scope_state.py`
- `novaic-cortex/tests/test_workspace_registry_dependencies.py`
