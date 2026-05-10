# Cortex ToolOutputV1 projection implemented

## Summary

Implemented the first Phase 2 Cortex projection step. `step_result_projection.parse_tool_result()` now detects `tool-output.v1` before legacy parsing and renders artifacts/events as compact manifest text while keeping `display_files` empty. This means a `ToolOutputV1` image artifact will not become inline image content even when `format_for_llm(... include_display=True)` is called.

## Done

- Updated `novaic-cortex/novaic_cortex/step_result_projection.py`.
- Added `novaic-cortex/tests/test_tool_output_projection.py`.
- Added structural parsing for `version == "tool-output.v1"`.
- Added compact artifact manifest text:
  - artifact label/name/URI;
  - modality/mime/size;
  - summary;
  - `display(file_url="...")` access hint.
- Added compact event manifest text.
- Added preview artifact count support.
- Preserved legacy `_mcp_content` image parsing during migration.

## Verification

- `cd novaic-cortex && python -m pytest tests/test_tool_output_projection.py -q`
  - Passed: `4 passed in 0.04s`
- `cd novaic-cortex && python -m pytest tests/test_resolve_for_llm.py tests/test_payload_inspection_api.py -q`
  - Passed: `14 passed in 0.24s`
- `cd novaic-agent-runtime && python -m pytest tests/test_pr85_llm_context_smoke_guardrails.py tests/test_runtime_explicit_contracts.py -q`
  - Passed: `15 passed in 0.10s`

## Known Gaps

- Generic legacy `_mcp_content` / `display_files` paths still exist and are intentionally preserved for now.
- Current-turn/history projection is not fully split yet.
- Runtime producers do not yet emit `ToolOutputV1` by default.

## Artifacts

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
