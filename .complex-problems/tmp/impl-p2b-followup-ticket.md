# Remove Missing Operational Store Fallback

## Problem Definition

Scope transition writes should not silently skip SQLite when a Workspace lacks an operational store. The current `getattr(..., None)` fallback must be replaced with an explicit failure boundary.

## Proposed Solution

Add a small `Workspace._require_operational_store()` helper and use it in lifecycle transition calls. Update tests to assert missing-store failure and to pass explicit stores in lifecycle tests.

## Acceptance Criteria

- No `getattr(self, "_operational_store", None)` remains in lifecycle transition writes.
- Missing operational store raises a clear `RuntimeError`.
- Lifecycle tests pass with explicit operational store.
- Static search confirms fallback removal.

## Verification Plan

- Run `test_scope_state.py`, `test_operational_store.py`, and representative workspace lifecycle tests.
- Run static search for `getattr(self, "_operational_store", None)`.

## Risks

- Some tests construct Workspace without the registry boundary; they must be updated where they exercise lifecycle transitions.

## Assumptions

- Registry-built production workspaces always provide `operational_store`.
