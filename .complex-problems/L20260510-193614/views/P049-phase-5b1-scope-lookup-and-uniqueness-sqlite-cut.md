# P049: Phase 5B1 Scope Lookup And Uniqueness SQLite Cutover

Status: done
Parent: P046
Root: P000
Package: problems/P000/children/P006/children/P046/children/P049
Body: problems/P000/children/P006/children/P046/children/P049/README.md
Ticket(s): T047

## Problem
`skill_begin` still uses root `meta.scope_ids` and `_walk_scope_tree` as duplicate scope-id authority, and `_resolve_scope_path_for_lookup` can walk materialized scope directories to locate scopes. This keeps local workspace files in live control decisions after SQLite projections exist.

## Success Criteria
- Scope creation/open/close paths write enough operational SQLite projection data to answer scope-id existence and scope lookup questions.
- `skill_begin` rejects duplicate child scope ids without reading root `meta.scope_ids` or walking the workspace tree.
- `_resolve_scope_path_for_lookup` uses SQLite projection for live lookup rather than `_walk_scope_tree`.
- Root `meta.scope_ids`, `register_scope_id`, and `get_scope_id_index` are deleted or no longer live authority.
- Targeted lifecycle/API tests prove duplicate rejection and lookup still work after restart/reopen.

## Subproblems
- none

## Results
- R044

## Latest Check
C047

## Bodies
- Problem: problems/P000/children/P006/children/P046/children/P049/README.md
- Ticket T047: problems/P000/children/P006/children/P046/children/P049/tickets/T047.md
- Result R044: problems/P000/children/P006/children/P046/children/P049/results/R044.md
- Check C047: problems/P000/children/P006/children/P046/children/P049/checks/C047.md

## Follow-ups
- none
