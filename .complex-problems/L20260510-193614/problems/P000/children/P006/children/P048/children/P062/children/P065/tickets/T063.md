# Phase 5D.2a Scope And Active Stack Guard Coverage

## Problem Definition

Verify guard coverage for scope lookup uniqueness and active stack authority after the SQLite projection cutover.

## Proposed Solution

- Search existing tests for duplicate scope ID rejection, `scope_projection`, active stack write/read/finalize, and removal of file-walk/root-meta authority.
- Run relevant tests.
- Add a minimal guard only if no durable coverage exists for a high-risk removed path.

## Acceptance Criteria

- Guard coverage map is recorded for scope uniqueness and active stack authority.
- Static guard search confirms removed runtime authority names do not exist in live source/current contract docs.
- Relevant tests pass.

## Verification Plan

```bash
rg -n "scope_projection|already used|active_stack_projection|register_scope_id|get_scope_id_index|meta\\.scope_ids|_walk_scope_tree" novaic-cortex/tests novaic-cortex/novaic_cortex docs/cortex -S
pytest -q <relevant tests>
```

## Risks

- Some tests may cover behavior indirectly; the result must explain the mapping instead of assuming coverage from filenames.

## Assumptions

- This ticket is allowed to add a small unit/API guard if coverage is absent.
