# Cut Scope History API To SQLite

## Problem Definition

The scope history endpoint still reads from the NDJSON helper. It must use the operational SQLite transition events written by Phase 2B.

## Proposed Solution

Update `scope_history` in `api.py` to call `list_scope_transition_events(_registry.operational_store, scope_path, limit=limit)` and return rows from SQLite. Add a direct API-level test using an initialized operational store with transition events.

## Acceptance Criteria

- API no longer imports `scope_state_log`.
- API response rows come from SQLite.
- API response no longer exposes `log_path`.
- Test covers rows returned from SQLite.

## Verification Plan

- Run the new API history test plus scope-state/operational-store tests.
- Search `api.py` for `scope_state_log`.

## Risks

- Existing callers may expect `log_path`; no compatibility required.

## Assumptions

- Registry has `operational_store` from Phase 1.
