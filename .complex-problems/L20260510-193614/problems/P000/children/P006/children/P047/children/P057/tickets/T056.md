# Phase 5C.1 Current Documentation And Comment Residue Audit

## Problem Definition

Current docs/comments must be cleaned without destroying historical roadmap/review provenance. We need a classified residue map before editing.

## Proposed Solution

Run focused static searches, inspect the highest-risk current docs/comments, and record a categorized map:

- current docs to edit
- live comments/docstrings to edit
- intentional guard/migration wording to keep
- historical docs to leave untouched

## Acceptance Criteria

- Audit includes `_walk_scope_tree`, `include_display`, `scope_state_log`, `format_for_llm`, temp sandbox backing paths, in-memory/process-local wording, and fallback/local authority wording.
- `docs/cortex` current docs are separated from `docs/roadmap/tickets` and review-history docs.
- The result names concrete edit targets for P058/P059.
- No source/docs modifications are made in this audit ticket.

## Verification Plan

```bash
rg -n "_walk_scope_tree|include_display|scope_state_log|format_for_llm|Single-process service|in-memory caching|novaic-cortex-sandbox-|legacy DFS|fallback authority|local authority|process-local|in-process" docs novaic-cortex/novaic_cortex -S
rg -n "/v1/steps/read_formatted|scope_id.*unique|scope_projection|active_stack_projection" docs/cortex docs/architecture -S
```

Inspect selected files with `sed`/`nl` and record classifications.

## Risks

- Search output includes historical tickets and roadmap docs; these should not be edited unless they present themselves as current architecture.

## Assumptions

- This is read-only audit work.
