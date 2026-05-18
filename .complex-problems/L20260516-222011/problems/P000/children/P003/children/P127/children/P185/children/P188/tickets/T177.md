# Audit Cortex display projection contract

## Problem Definition

Cortex must project display tool outputs according to two separate contracts: current-round display perception can expose media content, while historical/tool-message projection must stay text/manifest-only and never inline raw image bytes. P188 audits this Cortex-local boundary.

## Proposed Solution

Inspect `novaic-cortex/novaic_cortex/step_result_projection.py` and `step_result_client.py` for display result parsing, history formatting, current tool formatting, and display perception formatting. Verify existing tests or add focused tests that cover display output with blob/image content, historical formatting, and raw-base64 exclusion.

## Acceptance Criteria

- Display parsing and formatting functions are mapped with file/function evidence.
- Current display perception formatting produces structured image/media content when given display output.
- History and normal tool-result formatting remain text/manifest-only.
- Raw base64 is not projected as plain text by display parsing/formatting.
- Focused Cortex tests pass.

## Verification Plan

Run `novaic-cortex/tests/test_tool_output_projection.py` and any display-specific Cortex projection tests. Add a narrow test if current display media versus history manifest-only behavior is not already explicitly covered.

## Risks

- Internal `_mcp_content` shape is not the same as provider request shape; this ticket must stop at Cortex projection and leave provider conversion to P190.
- A current display result might look correct in Cortex but still be dropped later by runtime assembly; that is P189/P190 scope.

## Assumptions

- The source display artifact is already a blob/artifact reference, not raw shell stdout; shell artifact creation is outside this child.
