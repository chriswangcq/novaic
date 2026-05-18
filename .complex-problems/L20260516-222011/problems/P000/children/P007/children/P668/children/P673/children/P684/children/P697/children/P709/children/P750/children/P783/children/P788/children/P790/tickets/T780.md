# Cortex Projection BlobRef-Only Patch Ticket

## Problem Definition

Patch Cortex step result projection so inline MCP image/data URL payloads do not become provider-facing image content or preserved raw base64 in LLM context. Keep BlobRef `image_ref` display behavior intact.

## Proposed Solution

Change `parse_tool_result()` and/or `_format_mcp_content()` so:

- MCP `{"type": "image", "data": ...}` becomes safe text diagnostic, not `display_files` data URL.
- `display_files` with `data:` URLs become safe text diagnostic, not provider image data.
- BlobRef `image_ref` remains provider-facing visual content for explicit display perception.

Update focused tests in `novaic-cortex/tests/test_step_result_projection.py` and `novaic-cortex/tests/test_tool_output_projection.py`.

## Acceptance Criteria

- Raw image base64/data URLs are not emitted in `_mcp_content`.
- BlobRef `image_ref` behavior remains intact.
- Focused projection tests pass.
- Targeted `rg` confirms no active projection data URL image emission path remains.

## Verification Plan

Run:

```bash
cd novaic-cortex && pytest tests/test_step_result_projection.py tests/test_tool_output_projection.py
```

Then run targeted `rg` scans for `data:{mime};base64`, `url.startswith("data:")`, and `{"type": "image", "data":`.
