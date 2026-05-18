# MCP image/data-url branch audit result

## Summary

Retained the MCP image/data-url parsing branch, but verified and strengthened its constraint: parsed images become visual image blocks only through explicit `display_perception`; history and current-tool projections remain text-only.

## Branch Decision

Retained with rationale. The branch is still needed for current explicit display perception: `display` may return `_mcp_content` image data, `parse_tool_result` stores it as `display_files`, and `format_for_display_perception_llm` is the only formatter that passes `include_display=True`.

## Code Changes

- `novaic-cortex/tests/test_tool_output_projection.py`
  - Added `test_mcp_image_content_is_only_visual_in_display_perception_projection`.

## Verification

- Source inspection:
  - `parse_tool_result` stores MCP image `data` as `display_files`.
  - `format_for_history_llm` and `format_for_current_tool_result_llm` call `_format_mcp_content(..., include_display=False)`.
  - `format_for_display_perception_llm` calls `_format_mcp_content(..., include_display=True)`.
- Focused tests:
  - `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py`
  - Result: `17 passed in 0.07s`.

## Safety Properties

- Historical tool output remains text-only even when parsed data contains image data.
- Current non-display tool output remains text-only.
- Explicit display perception still emits the image block needed for multimodal LLM calls.

## Residual Risk

The branch still stores image data in `display_files` after parsing, so projection mode must remain explicit and correct at call sites. Existing tests now pin the formatter-level boundary.
