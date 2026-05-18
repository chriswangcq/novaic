# Cortex Projection Contract Inspection Result

## Summary
Read-only inspection completed. `step_result_projection.py` still has active inline media compatibility: MCP `{"type": "image", "data": ...}` is parsed into a `data:image/...;base64,...` display file, and display perception projection converts that data URL back into provider-facing image data. Existing tests currently assert the old behavior.

## Evidence
- `novaic-cortex/novaic_cortex/step_result_projection.py`:
  - `parse_tool_result()` handles MCP `content` / `_mcp_content`.
  - For `{"type": "image", "data": ...}`, it appends `display_files` with `url = "data:{mime};base64,{data}"`.
  - `_format_mcp_content(..., include_display=True)` detects `url.startswith("data:")` and emits `{"type": "image", "data": data_b64, "mimeType": mime}`.
  - BlobRefs are handled as `image_ref` when URL starts with `blob://`.
- Tests preserving old inline behavior:
  - `novaic-cortex/tests/test_step_result_projection.py::test_parse_tool_result_mcp_image_data`
  - `test_parse_tool_result_json_string_mcp_content`
  - `test_display_perception_projection_data_url`
  - `novaic-cortex/tests/test_tool_output_projection.py::test_mcp_image_content_parses_to_display_files_for_explicit_projection`
  - `test_mcp_image_content_is_only_visual_in_display_perception_projection`
  - `test_display_tool_step_payload_projects_llm_image_content`
  - `test_explicit_projection_modes_control_parsed_display_files`
- Tests already protecting current desired BlobRef path:
  - `test_display_perception_projection_blob_ref_image_ref`
  - `test_display_tool_step_payload_projects_blobref_image_ref_content`
  - `test_tool_output_v1_display_perception_never_inlines_artifact_image`

## Criteria Map
- Exact projection functions identified: satisfied.
- Existing unsafe compatibility behavior described: satisfied.
- Patch scope and test locations explicit: satisfied.
- No product code modified: satisfied.

## Execution Map
- Read projection module.
- Searched Cortex tests for `_mcp_content`, `data:image`, `base64`, `blob://`, `display`, and projection helpers.
- Read focused projection tests.

## Stress Test
- This inspection does not assume display should stop working. It separates unsafe inline data images from safe BlobRef `image_ref` display behavior.
- Shell `tool-output.v1` artifact manifest paths are already text/manifest-only and should remain intact.

## Residual Risk
- Patch child must update tests that currently assert old inline data behavior.

## Result IDs
- No code result; inspection result for sibling `P790`.
