# Result: Cortex projection BlobRef no-inline tests inventoried

## Summary

Cortex projection has direct regression coverage for BlobRef no-inline behavior. Tests prove shell `tool-output.v1` image artifacts remain manifest text, while explicit display step payload BlobRefs project as `image_ref` for display perception and stay text-only in history.

## Done

- Recorded scan output in `.complex-problems/L20260516-222011/tmp/p599/cortex-projection-blobref-scan.txt`.
- Scan command recorded:
  - `rg -n 'tool-output\\.v1|display_files|image_ref|blob://|never_inlines|BlobRef|data:image|inline' novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py -S`
  - `nl -ba ... | sed -n ...` slices for Cortex projection tests.
- Cited `novaic-cortex/tests/test_tool_output_projection.py:47-65`, which proves `tool-output.v1` image artifacts parse as manifest text and display perception never inlines those artifact images.
- Cited `novaic-cortex/tests/test_tool_output_projection.py:225-269`, which proves `tool-step-payload.v1` display BlobRef content parses to `display_files`, history is text-only, and display perception emits `image_ref`.
- Cited `novaic-cortex/tests/test_step_result_projection.py:126-148`, which proves BlobRef display files project as `image_ref` and history remains text-only.

## Verification

- Focused test command:
  - `PYTHONPATH="/Users/wangchaoqun/new-build-novaic/novaic-logicalfs:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-sdk:/Users/wangchaoqun/new-build-novaic/novaic-cortex:${PYTHONPATH:-}" python -m pytest novaic-cortex/tests/test_tool_output_projection.py::test_tool_output_v1_artifacts_render_as_manifest_text novaic-cortex/tests/test_tool_output_projection.py::test_tool_output_v1_display_perception_never_inlines_artifact_image novaic-cortex/tests/test_tool_output_projection.py::test_display_tool_step_payload_projects_blobref_image_ref_content novaic-cortex/tests/test_step_result_projection.py::test_display_perception_projection_blob_ref_image_ref -q`
- Result artifact: `.complex-problems/L20260516-222011/tmp/p599/cortex-projection-blobref-tests.txt`.
- Outcome: `4 passed in 0.03s`.

## Known Gaps

- None for Cortex BlobRef no-inline projection coverage.
- Legacy `data:` image projection remains intentionally covered separately as compatibility and is not the shell/display BlobRef artifact path.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p599/cortex-projection-blobref-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p599/cortex-projection-blobref-tests.txt`
