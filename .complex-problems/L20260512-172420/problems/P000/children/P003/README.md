# Full Path Regression Tests And Audit

## Problem

Existing tests cover idealized direct inputs but missed the actual executor-wrapper-Cortex-runtime path. Add or update tests so the real path catches both shell contract regressions and display base64 leakage.

## Success Criteria

- A regression test exercises display executor output through `_ok()`, Cortex `parse_tool_result` / `format_for_display_perception_llm`, and runtime `process_multimodal_messages`.
- Tests prove shell large output is bounded and does not include full raw stdout/stderr in diagnostics.
- Tests prove current display creates structured image content and history/current non-display projections do not inject images.
- Relevant focused tests pass.
