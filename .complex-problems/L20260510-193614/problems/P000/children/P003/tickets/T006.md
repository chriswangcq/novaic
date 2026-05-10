# Migrate Scope Transition Events To SQLite

## Problem Definition

Cortex still records scope lifecycle transitions in an NDJSON projection file (`scope_state_log_path`). That leaves durable lifecycle facts outside the new operational SQLite substrate and keeps two operational state mechanisms alive. Phase 2 must move scope transition event recording/querying onto the operational SQLite store while preventing a permanent dual-source design.

## Proposed Solution

Migrate scope lifecycle transition events in small steps:

- Identify the current transition write/read call sites and tests.
- Add a compatibility-thin SQLite-backed transition log adapter over `OperationalSqliteStore` if needed.
- Route scope transition writes through SQLite `scope_events`.
- Keep any NDJSON path only as temporary/export/debug if unavoidable, and mark/defer deletion explicitly if it cannot be removed in this phase.
- Update tests to assert transitions are persisted/read through SQLite and no live writer still requires NDJSON authority.

## Acceptance Criteria

- Scope transition event writes append to `scope_events` in operational SQLite.
- Existing transition query/read behavior used by tests is served from SQLite or a projection derived from SQLite.
- `scope_state_log_path` is no longer required for the authoritative transition state path.
- Tests cover open/archive/error transition cases through SQLite.
- Static search identifies any remaining NDJSON transition path as projection/debug or a follow-up deletion ticket.

## Verification Plan

- Read current transition writer/read model code and tests.
- Run existing scope-state/scope-state-log tests before and after migration.
- Add/update targeted tests for SQLite transition persistence.
- Search for `scope_state_log_path` and transition NDJSON writer residue.

## Risks

- Scope lifecycle is a hot path; changing it without focused tests could break skill begin/end or archive behavior.
- Removing `scope_state_log_path` too early may break unrelated diagnostics. If so, demote it explicitly rather than leaving it ambiguous.

## Assumptions

- Phase 1 operational store is available on every registry-built workspace.
- Existing transition semantics should be preserved while changing the authority substrate.
