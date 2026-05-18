# `resolve_for_llm` deletion result

## Summary

Removed the stale `resolve_for_llm` production helper and its root package export. Active Cortex projection tests and import smoke checks pass.

## Code Changes

- `novaic-cortex/novaic_cortex/step_result_projection.py`
  - Removed stale module docstring text advertising `resolve_for_llm`.
  - Removed unused `base64` import.
  - Removed `_IMAGE_EXTS`, `_TEXT_EXTS`, `_ext_of`, `_human_size`, and `resolve_for_llm`.
- `novaic-cortex/novaic_cortex/__init__.py`
  - Removed `resolve_for_llm` import from `step_result_projection`.
  - Removed `resolve_for_llm` from `__all__`.

## Verification

- Production reference check:
  - `rg -n "resolve_for_llm" novaic-cortex/novaic_cortex novaic-agent-runtime novaic-llm-factory novaic-common -S || true`
  - Result: no output; no production references remain.
- Cortex focused tests:
  - `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py`
  - Result: `15 passed in 0.05s`.
- Active API smoke:
  - Imported `parse_tool_result`, `preview_for_text`, `format_for_history_llm`, and `format_for_display_perception_llm`.
  - Verified history projection stays text-only and display perception still emits image content for current explicit display perception.

## Retained Branch Notes

This ticket intentionally did not delete the active current-display `data:` image handling in `format_for_display_perception_llm`; that path is still the current explicit display perception path and is separate from the stale helper. Its detailed branch audit remains in P209.

## Known Remaining Cleanup

`novaic-cortex/tests/test_resolve_for_llm.py` still references the removed helper and is intentionally left for the test-residue cleanup ticket P200.
