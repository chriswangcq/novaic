# Check: Cortex BlobRef projection coverage is direct

## Summary

Success. `R583` directly covers the Cortex projection layer: shell `tool-output.v1` artifacts remain manifest text, display tool-step BlobRefs become `image_ref` only for display perception, and history stays text-only.

## Evidence

- `R583` records scan and test artifacts:
  - `.complex-problems/L20260516-222011/tmp/p599/cortex-projection-blobref-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p599/cortex-projection-blobref-tests.txt`
- `novaic-cortex/tests/test_tool_output_projection.py:47-65` proves `tool-output.v1` image artifacts render as manifest text and are not inlined in display perception.
- `novaic-cortex/tests/test_tool_output_projection.py:225-269` proves display tool-step BlobRefs parse to `display_files`, history is text-only, and display perception emits `image_ref`.
- `novaic-cortex/tests/test_step_result_projection.py:126-148` proves generic BlobRef display files project as `image_ref` and history remains text-only.

## Criteria Map

- Exact scans and focused tests recorded: satisfied.
- `tool-output.v1` artifact image no-inline coverage: satisfied.
- Display BlobRef `image_ref` coverage: satisfied.
- Follow-up if missing: not needed.

## Execution Map

- `T590` executed read-only inventory plus focused pytest.
- Focused command passed: `4 passed in 0.03s`.
- No code changes were needed.

## Stress Test

- Plausible failure mode: Cortex treats shell screenshot artifact manifests as display media and emits base64/image content during projection.
- Covered by `test_tool_output_v1_display_perception_never_inlines_artifact_image`, which asserts all projected MCP items are text and the BlobRef remains a textual manifest reference.

## Residual Risk

- Legacy `data:` URL visual compatibility remains intentional and separately tested; it is not the BlobRef artifact path.

## Result IDs

- R583
