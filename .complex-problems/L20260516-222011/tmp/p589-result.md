# Cortex display projection media-reference result

## Summary

Implemented Cortex projection support for BlobRef-backed display media references. Cortex now parses `_mcp_content` `image_ref` items into `display_files`, and `display_perception` emits `image_ref` for BlobRef image media instead of degrading it to plain text or embedding bytes.

## Code Changes

- `novaic-cortex/novaic_cortex/step_result_projection.py`
  - `parse_tool_result` recognizes MCP `image_ref` items with `file_url` / `url`, MIME, filename, and size metadata.
  - `_format_mcp_content(..., include_display=True)` emits `image_ref` for `blob://` image display files.
  - Existing `data:` image handling is preserved.
  - Non-Blob normal URLs remain text diagnostics.
- `novaic-cortex/tests/test_tool_output_projection.py`
  - Added a tool-step payload test for the new runtime durable `image_ref` contract.
  - Confirmed history remains text-only while display perception carries `image_ref`.
- `novaic-cortex/tests/test_step_result_projection.py`
  - Added parsing and formatting tests for BlobRef image refs.

## Verification

- Initial focused test run failed during collection because local Python lacked imported workspace deps on `PYTHONPATH` (`logicalfs`, then `sandbox_sdk`). This was an environment import setup issue, not a projection assertion failure.
- Reran with explicit dependency paths:
  - `PYTHONPATH="/Users/wangchaoqun/new-build-novaic/novaic-logicalfs:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-sdk:/Users/wangchaoqun/new-build-novaic/novaic-cortex:${PYTHONPATH:-}" python -m pytest novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py -q`
  - Passed: `21 passed in 0.04s`.
- Targeted search confirmed intended `image_ref`, `display_files`, `data:image`, and BlobRef handling locations.

## Residual Risk

Cortex now preserves media references but does not resolve Blob bytes, by design. Runtime current-round resolver still needs to fetch BlobRefs and convert them into provider image input.
