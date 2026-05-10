# Cut Scope Transition Writes To SQLite

## Problem Definition

Workspace lifecycle code still writes durable transition history through NDJSON. Phase 2B must route live non-noop scope transition writes into `OperationalSqliteStore.scope_events` while preserving existing metadata transition semantics.

## Proposed Solution

Add a small transition-event helper over `OperationalSqliteStore`, then pass the workspace operational store into `scope_state.mark_archived/transition` from live workspace lifecycle methods.

Keep old NDJSON helper available only for legacy direct tests until Phase 2C removes/demotes it. Prevent dual writes by rejecting calls that pass both SQLite store and NDJSON path.

## Acceptance Criteria

- Live `Workspace.complete_child_scope` and `Workspace.archive_root_scope` pass the operational store into transition handling.
- Non-noop transitions append one `scope_state_transition` event to SQLite.
- Noop transitions do not append.
- Transition payload preserves the public history row shape.
- Tests cover direct transition SQLite append and workspace child completion SQLite append.

## Verification Plan

- Run `test_scope_state.py`, `test_operational_store.py`, and registry tests.
- Search workspace live paths to confirm they pass `operational_store`, not `transition_log_path`.
- Search for dual-write risk.

## Risks

- Direct tests still using NDJSON could hide a live-path cutover gap; add SQLite-specific tests.

## Assumptions

- Phase 2C will remove or demote the old NDJSON read/path API after history reads are served from SQLite.
