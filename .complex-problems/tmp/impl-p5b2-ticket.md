# Quarantine Archive Scope Tree Projection Helper

## Problem Definition

After P049, `_walk_scope_tree` remains only in `workspace.py` for root archive projection, but its generic name and comments still look like a reusable authority helper. Phase 5B2 must remove that misleading surface so future runtime code cannot casually call it for control decisions.

## Proposed Solution

- Rename `_walk_scope_tree` to an archive/debug projection-specific helper.
- Update recursive calls and `archive_root_scope`.
- Keep `/ro/scopes/_index.jsonl` generation working as historical projection.
- Add or update a static guard so `_walk_scope_tree` no longer exists in live Cortex source.
- Run targeted workspace/archive/scope tests.

## Acceptance Criteria

- No live source defines or calls `_walk_scope_tree`.
- The remaining helper name makes archive projection/debug-only semantics explicit.
- `archive_root_scope` still writes historical `/ro/scopes/_index.jsonl` projection.
- Targeted tests pass.

## Verification Plan

- Run static `rg -n "_walk_scope_tree" novaic-cortex/novaic_cortex novaic-cortex/tests`.
- Run targeted tests around archive/scope lifecycle and guard tests.
- Run `py_compile` for modified modules.

## Risks

- Renaming the helper can break tests or docs that intentionally refer to the old name.
- Archive projection behavior must remain stable until a later phase chooses to delete `/ro/scopes/_index.jsonl`.

## Assumptions

- P049 already removed API live lookup/uniqueness calls to `_walk_scope_tree`.
