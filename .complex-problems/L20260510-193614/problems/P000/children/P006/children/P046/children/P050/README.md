# Phase 5B2 Archive Tree Projection Quarantine

## Problem

After live lookup and uniqueness move to SQLite, `_walk_scope_tree` should not remain a generic authority-sounding helper. If it is still needed to build `/ro/scopes/_index.jsonl`, it must be renamed and confined to archive/debug projection behavior.

## Success Criteria

- `_walk_scope_tree` is removed or renamed to an archive/debug projection-specific helper.
- No API live control path calls the archive projection helper.
- `/ro/scopes/_index.jsonl` generation, if retained, is clearly projection/debug-only.
- Tests prove root archive still writes the expected historical projection without making it runtime authority.
