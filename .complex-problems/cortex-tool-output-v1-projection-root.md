# Cortex ToolOutputV1 projection implementation

## Problem

Implement the first Phase 2 step: make Cortex `step_result_projection` understand `ToolOutputV1` durable payloads. Historical LLM projection should render bounded text and artifact manifests, not image/base64/display payloads.

This should be a behavior-preserving extension for legacy payloads while adding first-class support for the new contract.

## Success Criteria

- `parse_tool_result()` detects `{"version": "tool-output.v1", ...}` before legacy `_mcp_content` / `display_files` parsing.
- `ToolOutputV1.artifacts[]` are rendered as compact manifest text/access hints.
- `ToolOutputV1` image artifacts do not become `display_files` and do not create inline image content through `format_for_llm(... include_display=True)`.
- Existing legacy parsing behavior remains covered.
- Add Cortex unit tests for ToolOutputV1 projection.
