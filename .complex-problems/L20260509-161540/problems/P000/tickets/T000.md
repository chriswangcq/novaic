# Add Cortex parser/projection support for ToolOutputV1

## Problem Definition

Runtime can now construct `ToolOutputV1`, but Cortex still primarily parses legacy `_mcp_content`, `files_created`, and `display_files`. If Cortex does not recognize the new contract, later producer migration will either serialize poorly or re-enter legacy display paths.

## Proposed Solution

Update `novaic-cortex/novaic_cortex/step_result_projection.py` so `parse_tool_result()` detects `version == "tool-output.v1"` first and returns:

- bounded text;
- artifact manifest lines in text;
- an `artifacts` list for non-LLM consumers;
- empty `display_files` for artifacts by default.

Add `novaic-cortex/tests/test_tool_output_projection.py`.

## Acceptance Criteria

- ToolOutputV1 image artifacts do not create `display_files`.
- `format_for_llm(... include_display=True)` does not create image content from ToolOutputV1 artifacts.
- Text and events remain visible in compact form.
- Legacy tests still pass.

## Verification Plan

- Run the new Cortex test.
- Run nearby Cortex projection tests.

## Risks

- Existing callers expect exactly three keys from `parse_tool_result`; adding an `artifacts` key should be compatible but should be tested.
- Artifact manifest text must stay compact.

## Assumptions

- Cortex should not import Runtime's Python module; it parses the JSON shape structurally.
