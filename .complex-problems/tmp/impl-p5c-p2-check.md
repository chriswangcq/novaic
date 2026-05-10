# Phase 5C.2 Current Cortex Docs Update Check

## Summary

Success. Result R054 satisfies P058: the current Cortex lifecycle and internal API docs no longer present removed runtime authorities as current behavior, and the replacement text documents SQLite projections, explicit step formatting projections, and archive/debug-only index semantics.

## Evidence

- R054 updated `docs/cortex/scope-lifecycle.md` and `docs/cortex/internal-api-schemas.md`.
- Negative static search returned no matches for `_walk_scope_tree`, `include_display`, `_SKILL_LOCKS`, or `asyncio.Lock` in the two current docs named by the ticket.
- Positive static search found current-contract terms including `scope_projection`, `active_stack_projection`, `projection`, `_build_archive_scope_index_projection`, and `Redis lock manager`.
- Diff review confirmed the edits stayed limited to the intended current Cortex docs.

## Criteria Map

- Update current Cortex docs that describe scope lifecycle, internal API schemas, and state authority boundaries: satisfied by edits to `docs/cortex/scope-lifecycle.md` and `docs/cortex/internal-api-schemas.md`.
- Remove or rewrite `_walk_scope_tree` as runtime lookup/uniqueness authority: satisfied; no `_walk_scope_tree` remains in those current docs, and lifecycle docs now describe archive/debug-only `_build_archive_scope_index_projection`.
- Describe SQLite `scope_projection` and archive-only projection: satisfied by lifecycle and internal API wording.
- Remove `include_display` from `/v1/steps/read_formatted` schema docs and describe explicit `projection`: satisfied by the internal API schema row.
- Preserve historical docs or mark them clearly historical: satisfied because this ticket only edited current docs; historical/roadmap files were not touched.
- Static doc search no longer finds current-doc stale contract claims: satisfied for the edited current-doc residues.

## Execution Map

- T057 was classified as `one_go` because the work was limited to two documentation files with direct static verification.
- R054 executed the doc edits and recorded both negative and positive verification commands.
- No implementation or behavior changes were made in this ticket.

## Stress Test

- Checked both absence and replacement presence: the negative search alone would miss accidental deletion without replacement, so the positive search verified that the docs now mention the intended SQLite projection and Redis lock-manager concepts.
- Reviewed diff scope to catch accidental broad documentation churn.

## Residual Risk

- This check is intentionally scoped to P058. Live source comments/docstrings and broad residue classification remain open in P059/P060 and are not counted as gaps for this problem.

## Result IDs

- R054
