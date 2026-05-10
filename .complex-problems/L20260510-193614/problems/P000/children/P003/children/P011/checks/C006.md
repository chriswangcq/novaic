# Phase 2B Not Success Check

## Summary

`P011` is not fully successful yet. The main write cutover exists and tests pass, but `Workspace.complete_child_scope` and `Workspace.archive_root_scope` currently pass `getattr(self, "_operational_store", None)`. That creates a silent no-SQLite fallback for Workspace instances constructed without the registry boundary. This violates the no-half-wiring/no-fallback goal.

## Blocking Gaps

- Remove the `operational_store=None` lifecycle fallback from live transition writes.
- Add tests proving lifecycle transition writes fail loudly or require explicit operational store when the store is absent.
- Ensure existing direct Workspace tests that exercise lifecycle methods pass explicit store dependencies.

## Result IDs

- `R006`
