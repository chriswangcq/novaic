# Phase 5B1 Scope Lookup And Uniqueness SQLite Cutover Check

## Summary

Success. R044 solves P049: live scope lookup and duplicate child scope-id rejection no longer depend on root `meta.scope_ids` or `_walk_scope_tree`; they use operational SQLite `scope_projection`.

## Evidence

- `Workspace.register_scope_id` and `Workspace.get_scope_id_index` were removed.
- `_find_scope_path_by_id` now calls `operational_store.get_scope_projection` / `list_scope_projections` and no longer calls `ws._walk_scope_tree` or `list_dir`.
- `skill_begin` now calls `operational_store.get_scope_projection(root_scope_id=req.scope_id, scope_id=child_scope_id)` before creating a child scope.
- `scope_projection` now stores `scope_path` and has a schema migration for older DBs.
- Projection writes happen on create, transition, and archive path updates.
- Static guard tests were updated to reject `_walk_scope_tree` in `skill_begin` and lookup sections.

## Criteria Map

- Scope creation/open/close paths write enough SQLite projection data: satisfied by `Workspace.create_scope`, `scope_state.transition`, and archive projection path updates.
- `skill_begin` rejects duplicates without root `meta.scope_ids` or tree walking: satisfied by API code and duplicate lifecycle test assertions.
- `_resolve_scope_path_for_lookup` / lookup uses SQLite projection: satisfied by `_find_scope_path_by_id` rewrite and static guard.
- Root `meta.scope_ids`, `register_scope_id`, `get_scope_id_index` deleted: satisfied by static audit.
- Targeted lifecycle/API tests prove behavior: satisfied by 45 + 31 targeted tests.

## Execution Map

- T047 executed as one bounded implementation ticket.
- R044 records code changes, tests, static audits, and remaining P050/P047 boundaries.

## Stress Test

- Targeted tests cover duplicate rejection, stack persistence, reopened workspace behavior, operational store projection roundtrip, and no-file-walk guards.
- Additional scope state/history/control tests passed.
- Compile checks passed for modified modules.

## Residual Risk

- Low for P049. `_walk_scope_tree` still exists for archive projection in `workspace.py`, but that is explicitly outside this P049 scope and is assigned to P050.

## Result IDs

- R044
