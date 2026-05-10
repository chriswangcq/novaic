# Phase 5C Current Docs And Comments Cleanup

## Problem Definition

Source cleanup is no longer enough: current docs and live comments still contain stale authority wording such as `_walk_scope_tree` for uniqueness, `include_display` on `/v1/steps/read_formatted`, and process-local/in-memory cache language. These can mislead future agents into rebuilding old local authority paths.

## Proposed Solution

Perform a documentation/comment cleanup pass in four slices:

1. Audit and classify current docs/comments versus historical roadmap/review material.
2. Update current Cortex docs:
   - scope lifecycle
   - internal API schemas
   - state authority implementation plan / invariants if needed
   - architecture service/data ownership pages if current residue appears.
3. Update live-code comments/docstrings:
   - `registry.py` process-local/in-memory wording
   - any API/comment wording that presents DFS/file walk, fallback, temp paths, or in-memory behavior as production authority.
4. Add/update residue guard documentation and run static audit.

## Acceptance Criteria

- Current docs no longer mention `_walk_scope_tree` as runtime uniqueness/lookup authority.
- Current docs no longer list `include_display` in the step formatting API.
- Current docs/comments do not imply `/tmp/novaic-cortex-sandbox-*`, in-process locks, process-local state, or file walks are production authority.
- Historical roadmap/review docs are left intact unless they are being used as current guidance.
- Static audit output is classified with no unowned current residue.

## Verification Plan

Run focused static audits:

```bash
rg -n "_walk_scope_tree|include_display|scope_state_log|format_for_llm|Single-process service|in-memory caching|novaic-cortex-sandbox-|legacy DFS|fallback authority|local authority" docs novaic-cortex/novaic_cortex -S
rg -n "/v1/steps/read_formatted|scope_id.*unique|scope_projection|active_stack_projection" docs/cortex docs/architecture -S
```

Then inspect changed docs with `sed`/`rg` and run a markdown/source static check. Code tests only needed if live source comments change alongside code.

## Risks

- Historical roadmap/review docs intentionally mention old paths. Editing them can destroy useful provenance; classify before changing.
- Some guard docs intentionally say “fallback” to ban it; those should be retained or clarified, not deleted blindly.

## Assumptions

- This phase is documentation/comment cleanup, not runtime behavior changes.
- Phase 5D will run the broad final verification suite after this cleanup.
