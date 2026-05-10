# Phase 2C2 Remove NDJSON Transition Log Surface

## Problem

After history reads move to SQLite, NDJSON transition helpers and startup/config fields should be physically removed. Leaving them creates misleading dual-source residue.

## Success Criteria

- Remove `scope_state_log_path` from `Workspace`, `WorkspaceRegistry`, `build_workspace_registry`, `main_cortex.py`, `scripts/start.sh`, docs, and tests.
- Remove `transition_log_path` from `scope_state.transition` and `mark_archived`.
- Delete `novaic_cortex/scope_state_log.py` and its direct NDJSON tests.
- Static search for `scope_state_log_path`, `transition_log_path`, and `scope_state_log` has no live authoritative code matches.
