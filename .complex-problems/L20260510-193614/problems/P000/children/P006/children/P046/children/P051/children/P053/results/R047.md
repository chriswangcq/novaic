# Phase 5B3.2 Step Projection Explicit API Cutover Result

## Summary

Removed the broad `format_for_llm` compatibility wrapper and cut Cortex tests/package exports over to explicit projection APIs. Step result projection now exposes explicit history/current/display/monitor behavior without the old `include_display` wrapper.

## Done

- Deleted `format_for_llm` from `novaic-cortex/novaic_cortex/step_result_projection.py`.
- Removed `format_for_llm` import/export from `novaic-cortex/novaic_cortex/__init__.py`.
- Updated `novaic-cortex/tests/test_step_result_projection.py` to use:
  - `format_for_history_llm` for truncation/history behavior.
  - `format_for_display_perception_llm` for data-url visual behavior.
- Updated `novaic-cortex/tests/test_tool_output_projection.py` to use `format_for_display_perception_llm` for explicit display-perception checks.
- Ran a workspace-wide static search to confirm no `format_for_llm` references remain in Cortex or sibling packages.

## Verification

- Static search: `rg -n "format_for_llm" novaic-cortex/novaic_cortex novaic-cortex/tests -S`
  - Result: no matches.
- Workspace static search: `rg -n "format_for_llm" novaic-cortex novaic-agent-runtime novaic-business novaic-common novaic-logicalfs novaic-sandbox-service novaic-sandbox-sdk -S`
  - Result: no matches.
- Targeted tests:
  - `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_step_result_projection.py novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_resolve_for_llm.py`
  - Result: `20 passed in 0.11s`.
- Compile check:
  - `python3 -m py_compile novaic-cortex/novaic_cortex/step_result_projection.py novaic-cortex/novaic_cortex/__init__.py novaic-cortex/novaic_cortex/api.py`
  - Result: passed.

## Known Gaps

- Test names and string data still contain `legacy` wording in a few places; P054 owns source/test wording cleanup.
- `/v1/steps/read_formatted` still accepts the existing `include_display` request field for callers that do not send an explicit `projection`; this no longer depends on `format_for_llm`, but P055 should decide whether to record it as current adapter behavior or create a follow-up if strict explicit-only API is required.

## Artifacts

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/novaic_cortex/__init__.py`
- `novaic-cortex/tests/test_step_result_projection.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
