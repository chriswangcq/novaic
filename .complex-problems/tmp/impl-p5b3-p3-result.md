# Phase 5B3.3 Legacy Test And Comment Wording Cleanup Result

## Summary

Cleaned misleading `legacy` wording from current-behavior projection/context tests and the context budget docstring while preserving intentional legacy/fallback guard tests and schema migration wording.

## Done

- Updated `context_stack/budget.py` docstring from "event-backed and legacy context preparation" to current event-backed wording.
- Renamed current-behavior projection tests in `test_tool_output_projection.py`:
  - MCP image parsing now describes explicit projection behavior instead of "legacy during migration".
  - display-files projection test now describes parsed display files instead of "legacy display files".
- Replaced `legacy` sample text in those projection tests with current neutral text.
- Renamed keyed retry context append test from `preserves_legacy_behavior` to `preserves_context_projection`.
- Renamed stale root-summary meta test wording from `legacy_meta`/`legacy staged text` to `stale_meta`/`stale staged text`.
- Renamed the no-compat helper and agent IDs from `legacy_only` to `file_tree_only` while preserving tests that explicitly assert no legacy DFS fallback.

## Verification

- Static search: `rg -n "legacy|fallback|compat|compatibility" novaic-cortex/novaic_cortex novaic-cortex/tests -S`
  - Result: remaining hits are guard tests, schema migration internals, no-local-fallback boundary checks, or explicit reset-required/no-DFS-fallback wording.
- Targeted tests:
  - `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_context_event_api_context_writes.py novaic-cortex/tests/test_context_event_no_compat.py novaic-cortex/tests/test_context_budget.py novaic-cortex/tests/test_pr56_root_scope_summary.py novaic-cortex/tests/test_pr57_list_archived_summaries.py`
  - Result: `27 passed in 0.40s`.
- Compile check:
  - `python3 -m py_compile novaic-cortex/novaic_cortex/context_stack/budget.py`
  - Result: passed.

## Known Gaps

- Remaining `legacy`/`fallback` hits are intentionally left for P055 to verify and record as justified residue:
  - persisted SQLite migration names in `operational_store.py`
  - guard tests for deleted legacy routes/fallbacks
  - no-local-fallback sandbox boundary checks
  - reset-required error wording for forbidden legacy DFS fallback.

## Artifacts

- `novaic-cortex/novaic_cortex/context_stack/budget.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_context_event_api_context_writes.py`
- `novaic-cortex/tests/test_pr56_root_scope_summary.py`
- `novaic-cortex/tests/test_context_event_no_compat.py`
