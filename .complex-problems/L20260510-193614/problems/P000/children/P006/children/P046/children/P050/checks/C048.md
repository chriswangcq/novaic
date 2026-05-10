# Phase 5B2 Archive Projection Quarantine Check

## Summary

Success. Result `R045` satisfies the Phase 5B2 problem: the generic `_walk_scope_tree` helper no longer exists in live Cortex source, the remaining tree walk is explicitly archive/debug projection-only, and runtime lookup/active-stack guard tests prevent the API control path from reusing file-tree authority.

## Evidence

- `novaic-cortex/novaic_cortex/workspace.py` now defines `_build_archive_scope_index_projection` with a docstring saying it builds `/ro/scopes/_index.jsonl` archive projection entries and that runtime scope lookup/active-stack decisions must use operational SQLite projections.
- `archive_root_scope` calls `_build_archive_scope_index_projection` only to build historical archive index entries before moving the root to `/ro/scopes`.
- `novaic-cortex/tests/test_context_event_read_source_guards.py` has guard coverage for skill begin lookup, scope lookup, skill end, active write routing, and live-source absence of the old generic helper name.
- Static search found only `_build_archive_scope_index_projection` occurrences in `workspace.py` and no `_walk_scope_tree` live-source occurrence.
- Targeted suite passed: `49 passed in 0.57s`.
- Compile check passed for `novaic-cortex/novaic_cortex/workspace.py`.

## Criteria Map

- `_walk_scope_tree` is removed or renamed to an archive/debug projection-specific helper: satisfied by replacing it with `_build_archive_scope_index_projection` and adding the live-source guard.
- No API live control path calls the archive projection helper: satisfied by static search showing the helper only appears in `workspace.py`, plus API guard tests checking SQLite projection use.
- `/ro/scopes/_index.jsonl` generation is clearly projection/debug-only: satisfied by the helper name and docstring.
- Tests prove root archive still writes expected historical projection without making it runtime authority: satisfied by `test_archive_invariants.py` in the targeted suite and the read-source guard suite.

## Execution Map

- Result `R045` made one bounded change set in `workspace.py` and `test_context_event_read_source_guards.py`.
- The execution did not perform unrelated docs cleanup or compatibility-wrapper cleanup; those are separate sibling tickets already planned under Phase 5C and Phase 5B3.

## Stress Test

- The check looked for the old helper name across live Cortex source/tests and confirmed the new helper does not leak into API paths.
- The check also inspected the surrounding archive code to ensure the residual file walk is still limited to archive index projection.

## Residual Risk

- Historical/current docs can still mention the old helper name; this is intentionally outside P050 and remains assigned to Phase 5C.
- Broad full-suite verification remains assigned to Phase 5D after the remaining cleanup tickets are closed.

## Result IDs

- R045
