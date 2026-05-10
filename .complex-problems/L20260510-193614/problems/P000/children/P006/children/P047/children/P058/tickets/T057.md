# Phase 5C.2 Current Cortex Docs Update

## Problem Definition

Current Cortex docs still describe old runtime contracts: `_walk_scope_tree` for archive/uniqueness and `include_display` on `/v1/steps/read_formatted`. These docs must reflect SQLite projections and explicit projection modes.

## Proposed Solution

Update current docs only:

- `docs/cortex/scope-lifecycle.md`
  - Replace `_walk_scope_tree` runtime language with archive-only `_build_archive_scope_index_projection`.
  - Describe child scope ID uniqueness via operational SQLite `scope_projection`.
  - Replace `_SKILL_LOCKS`/`asyncio.Lock` wording with Redis lock manager / test-only in-memory lock wording.
- `docs/cortex/internal-api-schemas.md`
  - Replace `include_display?` with `projection?`.
  - Replace `_walk_scope_tree(root_scope_path)` uniqueness wording with `scope_projection`.

## Acceptance Criteria

- Current Cortex docs no longer mention `_walk_scope_tree`.
- `/v1/steps/read_formatted` docs no longer mention `include_display`.
- Scope lifecycle docs say archive tree index is archive/debug projection-only.
- Skill uniqueness docs say SQLite `scope_projection` is authority.
- Static doc search for the edited current-doc residues returns no stale matches in current Cortex docs.

## Verification Plan

```bash
rg -n "_walk_scope_tree|include_display|_SKILL_LOCKS|asyncio\\.Lock" docs/cortex/scope-lifecycle.md docs/cortex/internal-api-schemas.md -S
rg -n "scope_projection|active_stack_projection|read_formatted|projection" docs/cortex/scope-lifecycle.md docs/cortex/internal-api-schemas.md -S
```

## Risks

- Docs may include historical notes in current files; preserve historical notes only when clearly marked and not contradicting current contract.

## Assumptions

- This ticket does not edit roadmap/history docs.
