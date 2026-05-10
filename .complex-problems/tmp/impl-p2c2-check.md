# P015 Success Check - NDJSON Transition Log Surface Removed

## Summary

P015 is solved. The legacy scope transition NDJSON surface is physically removed from live Cortex code, startup wiring, docs, and tests, and non-noop scope transitions now require the operational SQLite store instead of silently falling back to a file path.

## Evidence

- Result R009 deletes the old module/test and removes `scope_state_log_path` plus `transition_log_path` from the product surface.
- Static search for `scope_state_log`, `scope_state_log_path`, `transition_log_path`, and `scope-state-log-path` across Cortex code, tests, docs, and startup returned no matches.
- Targeted tests passed: 31 tests across scope-state, scope-history API, operational-store, and registry dependency coverage.
- Modified modules passed Python bytecode compilation.

## Criteria Map

- Remove `scope_state_log_path` from Workspace, WorkspaceRegistry, `build_workspace_registry`, `main_cortex.py`, `scripts/start.sh`, docs, and tests: satisfied by R009 static search and code edits.
- Remove `transition_log_path` from `scope_state.transition` and `mark_archived`: satisfied by R009 code edits and static search.
- Delete `novaic_cortex/scope_state_log.py` and direct NDJSON tests: satisfied by deleted files in R009.
- Static search for old symbols has no live authoritative code matches: satisfied by R009 `rg` evidence.

## Execution Map

- T012 executed as one bounded cleanup attempt.
- R009 records the actual edits, verification commands, and the remaining out-of-scope Phase 3 work.
- This check cites R009 and performs no additional implementation work.

## Stress Test

- The change goes beyond deleting names: `scope_state.transition()` now raises `RuntimeError` for non-noop transitions without `operational_store`, closing the most likely future regression where a caller changes phase without durable SQLite history.
- Generic `event_log_path` matches were reviewed and are context event-stream infrastructure, not the removed scope lifecycle transition authority.

## Residual Risk

- Phase 3 active-stack/status authority cutover is still pending in the parent ledger, but it is not part of P015's old NDJSON transition-log cleanup scope.
- Context event-source files still use file-backed event streams by design and should be handled by their own state-authority phase if later selected.

## Result IDs

- R009
