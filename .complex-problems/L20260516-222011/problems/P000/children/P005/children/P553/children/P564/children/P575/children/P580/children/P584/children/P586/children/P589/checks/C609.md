# P589 Check

## Summary

Success. Cortex projection now preserves BlobRef-backed display media references as `image_ref` for `display_perception`, while keeping history text-only and preserving legacy data-URL handling.

## Strict Review

- `parse_tool_result` now recognizes MCP `image_ref`, so the new runtime durable payload contract is no longer treated as unknown JSON.
- Display perception emits `image_ref` for `blob://` image media references, so Cortex does not fetch Blob bytes or embed base64.
- History and current non-display projections still call `_format_mcp_content(..., include_display=False)`, so they remain text-only.
- Existing data URL tests still pass, proving legacy explicit inline image handling was not accidentally broken.
- Focused tests cover both the durable tool-step payload and direct projection helper paths.

## Stress Test

The test suite covers three important modes:

- artifact manifests stay text-only even under display perception,
- legacy data URLs remain image MCP content,
- new BlobRefs become `image_ref` instead of text or base64.

## Residual Risk

The runtime resolver still needs to consume `image_ref` and fetch Blob bytes for current-round LLM calls. That is intentionally left to the next sibling ticket.
