# Cortex ToolOutputV1 projection satisfies Phase 2 step

## Summary

This Phase 2 step succeeds. Cortex now recognizes `tool-output.v1` durable payloads and projects artifacts/events as manifest text instead of legacy display/image content.

## Evidence

- Result `R000` updated `novaic-cortex/novaic_cortex/step_result_projection.py`.
- Result `R000` added `novaic-cortex/tests/test_tool_output_projection.py`.
- New projection tests passed: `4 passed in 0.04s`.
- Nearby Cortex tests passed: `14 passed in 0.24s`.
- Runtime context smoke/contract tests passed: `15 passed in 0.10s`.

## Criteria Map

- Detect ToolOutputV1 first -> `parse_tool_result()` checks `raw.get("version") == "tool-output.v1"` before legacy parsing.
- Render artifacts as manifest text -> `_tool_output_artifact_line()`.
- Do not create display_files from artifacts -> `_parse_tool_output_v1()` returns `display_files: []`.
- `include_display=True` does not inline artifact image -> `test_tool_output_v1_format_for_llm_never_inlines_artifact_image`.
- Legacy parsing remains -> `test_legacy_mcp_image_still_uses_display_files_during_migration`.

## Execution Map

- Ticket `T000` was classified `one_go`.
- Result `R000` records the focused Cortex projection implementation.

## Stress Test

- Failure mode: image artifact sneaks into `display_files`. The new test asserts `display_files == []`.
- Failure mode: `format_for_llm(include_display=True)` reintroduces image content. The new test asserts every `_mcp_content` item is text.
- Failure mode: legacy compatibility breaks too early. The new legacy test preserves the old MCP image behavior during migration.

## Residual Risk

- Legacy image/data-url paths still exist and must be deleted in later phases.
- Runtime producers still need to emit `ToolOutputV1`.
- Projection split between history/current/display is not fully complete.

## Result IDs

- R000
