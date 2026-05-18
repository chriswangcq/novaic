# Verify MCP image/data-url branch is display-only

## Problem Definition

`parse_tool_result` can parse MCP image blocks into `display_files`, and `_format_mcp_content` can emit image blocks when `include_display=True`. This is needed for explicit `display` perception but must never leak images into history or generic current-tool projections.

## Proposed Solution

Audit the branch against current projection functions and tests. Retain it only if it is clearly constrained to explicit `display_perception`; otherwise narrow or remove it. Strengthen tests if needed to prove history/current-tool projections remain text-only.

## Acceptance Criteria

- The branch decision is explicit: retained with rationale or removed.
- History and current-tool projections do not emit image content from parsed display files.
- Explicit display perception still emits image content when a display result provides image data.
- Focused projection tests pass.

## Verification Plan

Inspect `parse_tool_result`, `_format_mcp_content`, and existing tests, then run Cortex projection tests after any needed test/code adjustments.

## Risks

- Removing the branch would break actual display perception.
- Retaining it without projection constraints would recreate the original base64-in-context problem.

## Assumptions

- `display_perception` is the only valid LLM context mode for actual visual image blocks.
