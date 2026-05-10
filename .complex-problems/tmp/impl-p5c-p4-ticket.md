# Phase 5C.4 Documentation Residue Final Static Gate

## Problem Definition

After P058/P059, Phase 5C needs a final residue gate across current docs and live source to prove stale authority contracts are not still advertised. Remaining matches must be explicitly classified instead of left ambiguous.

## Proposed Solution

Run a broad static audit over current Cortex docs and live source for stale authority terms, then classify every remaining match:

- Search for removed names and stale contracts such as `_walk_scope_tree`, `include_display`, `format_for_llm`, `scope_state_log`, temp sandbox backing paths, in-process locks as authority, and local/fallback authority wording.
- Separate allowed matches from defects:
  - historical/roadmap docs
  - migration internals
  - explicit negative guard language
  - low-level `resolve_for_llm` behavior unrelated to removed compatibility wrappers
  - test-only helpers
- If a current unowned residue is found, edit or create a follow-up problem through the ledger.

## Acceptance Criteria

- Final static searches are recorded with commands and outcomes.
- Remaining hits are listed in a classification table.
- No current docs/comments present temp sandbox backing paths, in-process locks, file-walk helpers, `_walk_scope_tree`, `format_for_llm`, or `include_display` as current production authority.
- Any remaining matches are intentionally historical, negative guard, schema migration, test-only, or low-level projection behavior.

## Verification Plan

```bash
rg -n "_walk_scope_tree|include_display|scope_state_log|format_for_llm|Single-process service|in-memory caching|novaic-cortex-sandbox-|legacy DFS|fallback authority|local authority|process-local|in-process|_SKILL_LOCKS|asyncio\\.Lock" docs/cortex docs/architecture novaic-cortex/novaic_cortex -S
rg -n "resolve_for_llm|projection|scope_projection|active_stack_projection|RedisScopeLockManager|OperationalSqliteStore" docs/cortex novaic-cortex/novaic_cortex -S
```

## Risks

- Broad searches will produce intentional matches; treating all matches as defects would delete useful negative guards.
- Treating broad matches too casually would hide stale guidance. The result must classify each category with evidence.

## Assumptions

- Historical docs may keep old wording if they are clearly historical and not current guidance.
- Behavior changes are out of scope unless the static gate exposes a direct contradiction.
