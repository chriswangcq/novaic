# Phase 0 design result

## Summary

Completed the first bounded execution attempt for Phase 0 by writing the target design and construction plan for a full Cortex ContextEvent source-of-truth cutover. This phase intentionally produced documentation only; implementation is left to the already-created Phase 1 through Phase 5 child problems.

## Done

- Added `docs/cortex/context-event-source.md` with the final target model: append-only ContextEvent stream, event envelope, stream identity, ordering, idempotency, projection semantics, failure/replay behavior, no-compat reset policy, implementation phases, and hard invariants.
- Updated `docs/cortex/README.md` to include the new design document in the Cortex docs index.
- Made the no-dual-truth policy explicit: legacy `context.jsonl`, `steps/_index.jsonl`, `steps/*.json`, `meta.json`, and `summary.md` are no longer source-of-truth in the target model; any remaining RO/debug shape must be projection-only.
- Made the old-data policy explicit: old historical context data may be deleted/reset, with no compatibility reader for old `summary.md` or fallback to old `steps/_index.jsonl` as source.

## Verification

- Ran `rg` over `docs/cortex/context-event-source.md` and `docs/cortex/README.md` for the required terms and sections: old data deletion, legacy source paths, projection model, construction plan, and hard invariants.
- Ran `wc -l docs/cortex/context-event-source.md`; the design document is 372 lines.
- Confirmed the current ledger next action was `execute-ticket` for `T001` before recording this result.

## Known Gaps

- None for Phase 0's documentation objective.
- Implementation remains intentionally open and is tracked by child problems P002 through P006.
- There are pre-existing uncommitted repository changes from prior work in `.complex-problems/L20260510-152822`, `.complex-problems/L20260510-153817`, and the `novaic-cortex` subrepo; Phase 0 did not attempt to clean or revert them.

## Artifacts

- `docs/cortex/context-event-source.md`
- `docs/cortex/README.md`
- `.complex-problems/L20260510-154902`
