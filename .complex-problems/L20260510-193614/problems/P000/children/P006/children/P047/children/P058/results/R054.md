# Phase 5C.2 Current Cortex Docs Update Result

## Summary

Updated the current Cortex docs that still described removed or misleading runtime authorities. The docs now describe SQLite projections for scope lookup and stack resolution, archive/debug-only scope index projection, Redis-backed scope lock manager for production locking, and the current `read_formatted` projection contract.

## Done

- Updated `docs/cortex/scope-lifecycle.md` to remove `_walk_scope_tree` as runtime lookup/uniqueness authority.
- Updated `docs/cortex/scope-lifecycle.md` to describe `/ro/scopes/_index.jsonl` as archive/debug projection only.
- Updated `docs/cortex/scope-lifecycle.md` to replace `_SKILL_LOCKS` / `asyncio.Lock` wording with scope lock manager and Redis/in-memory manager roles.
- Updated `docs/cortex/scope-lifecycle.md` to describe active stack routing through SQLite `active_stack_projection`.
- Updated `docs/cortex/internal-api-schemas.md` to remove `include_display?` from `/v1/steps/read_formatted` and document `projection?` values.
- Updated `docs/cortex/internal-api-schemas.md` to describe skill begin/end checks through operational SQLite projections.

## Verification

- `rg -n "_walk_scope_tree|include_display|_SKILL_LOCKS|asyncio\\.Lock" docs/cortex/scope-lifecycle.md docs/cortex/internal-api-schemas.md -S` returned no matches.
- `rg -n "scope_projection|active_stack_projection|read_formatted|projection|_build_archive_scope_index_projection|Redis lock manager" docs/cortex/scope-lifecycle.md docs/cortex/internal-api-schemas.md -S` returned expected current-contract matches.
- Reviewed `git diff -- docs/cortex/scope-lifecycle.md docs/cortex/internal-api-schemas.md` to confirm the edit scope stayed limited to the two current Cortex docs.

## Known Gaps

- Live source comments/docstrings are intentionally left for P059.
- Broad final residue gate is intentionally left for P060.

## Artifacts

- `docs/cortex/scope-lifecycle.md`
- `docs/cortex/internal-api-schemas.md`
