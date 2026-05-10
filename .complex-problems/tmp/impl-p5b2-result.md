# Phase 5B2 Archive Tree Projection Quarantine Result

## Summary

The remaining generic `_walk_scope_tree` live-source authority helper was removed from runtime source and replaced with an explicitly archive/debug projection helper. Runtime scope lookup and active-stack decisions are now kept on operational SQLite projection paths; the residual workspace tree walk is named and documented as `/ro/scopes/_index.jsonl` archive projection construction only.

## Done

- Renamed `Workspace._walk_scope_tree` to `Workspace._build_archive_scope_index_projection`.
- Updated the recursive helper call and `archive_root_scope` call site to use the archive-specific helper.
- Added an explicit docstring stating this helper is archive/debug projection-only and must not be used for runtime lookup or active-stack decisions.
- Added a static guard test that scans live `novaic_cortex/*.py` source and fails if the old generic helper name returns.
- Updated existing source guard tests to avoid embedding the old helper token directly in the test source while still checking the runtime source boundary.

## Verification

- Static search: `rg -n "_walk_scope_tree|_build_archive_scope_index_projection" novaic-cortex/novaic_cortex novaic-cortex/tests/test_context_event_read_source_guards.py -S`
  - Result: no `_walk_scope_tree` occurrences in live source; only `_build_archive_scope_index_projection` remains in `workspace.py`.
- Targeted tests: `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_read_source_guards.py novaic-cortex/tests/test_scope_state.py novaic-cortex/tests/test_archive_invariants.py novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
  - Result: `49 passed in 0.57s`.
- Compile check: `python3 -m py_compile novaic-cortex/novaic_cortex/workspace.py`
  - Result: passed.

## Known Gaps

- Current docs still mention `_walk_scope_tree` in non-live documentation; Phase 5C owns current docs/comments cleanup and should distinguish historical review docs from live design docs.
- `step_result_projection.py` still has a compatibility-wrapper review item assigned to Phase 5B3.
- Broad full-suite verification is intentionally deferred to Phase 5D after the remaining cleanup tickets are closed.

## Artifacts

- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
