# P015 T012 Result - Remove NDJSON Transition Log Surface

## Summary

Removed the old scope transition NDJSON authority surface from live Cortex code and tightened the remaining scope transition path so any non-noop transition must write a SQLite lifecycle event through the operational store.

## Done

- Deleted the legacy `scope_state_log.py` module and its dedicated test file.
- Removed the transition-log startup/config surface from Cortex startup wiring and replaced it with the operational SQLite path.
- Removed `transition_log_path` from `scope_state.transition()`, `scope_state.mark_archived()`, and Workspace lifecycle call sites.
- Made non-noop scope transitions fail loud when no `operational_store` is provided.
- Updated scope-state tests to assert SQLite lifecycle events and added coverage for missing operational-store wiring.
- Updated the state-authority design notes so Phase 2 points to SQLite as the only durable lifecycle-history authority.
- Removed stale import/comment residue from `workspace.py` and `scope_state.py`.

## Verification

- `rg -n "scope_state_log|scope_state_log_path|transition_log_path|scope-state-log-path" novaic-cortex/novaic_cortex novaic-cortex/tests docs/cortex scripts/start.sh -S` returned no matches.
- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_scope_state.py novaic-cortex/tests/test_scope_history_api.py novaic-cortex/tests/test_operational_store.py novaic-cortex/tests/test_workspace_registry_dependencies.py` passed: 31 tests.
- `python3 -m py_compile novaic-cortex/novaic_cortex/api.py novaic-cortex/novaic_cortex/scope_state.py novaic-cortex/novaic_cortex/scope_transition_events.py novaic-cortex/novaic_cortex/workspace.py novaic-cortex/novaic_cortex/registry.py novaic-cortex/novaic_cortex/main_cortex.py novaic-cortex/novaic_cortex/operational_store.py` passed.

## Known Gaps

- Generic context event-source files still use their own `event_log_path`; that is separate context event-stream infrastructure, not the removed scope lifecycle transition log.
- Phase 3 active-stack/status authority cutover remains pending in the parent ledger.

## Artifacts

- `novaic-cortex/novaic_cortex/scope_state.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_scope_state.py`
- `scripts/start.sh`
- `docs/cortex/state-authority-implementation-plan.md`
