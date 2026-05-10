# Require Operational Store For Scope Transition Writes

## Problem

The Phase 2B write cutover still has a silent fallback: workspace lifecycle methods pass `getattr(self, "_operational_store", None)` into transition handling. If a Workspace is created outside the registry boundary, lifecycle transitions can update `meta.phase` without writing the SQLite transition event. That is exactly the kind of half-wired path this migration is meant to eliminate.

## Success Criteria

- Workspace lifecycle transition writes require an operational store and fail loudly when it is absent.
- `Workspace.complete_child_scope` and `Workspace.archive_root_scope` no longer use `getattr(..., None)` for the operational store.
- Tests cover the missing-store failure and update lifecycle tests to provide an explicit store where needed.
- Targeted scope-state/workspace tests pass.
