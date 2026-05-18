# Cortex Projection BlobRef-Only Patch Result

## Summary
Patched Cortex step result projection so inline MCP image/data URL payloads no longer become provider-facing image content or preserved raw base64 in LLM context. BlobRef `image_ref` display behavior remains intact.

## Evidence
- `novaic-cortex/novaic_cortex/step_result_projection.py`:
  - Added `_inline_media_omitted_text()`.
  - MCP `{"type": "image", "data": ...}` now becomes a text diagnostic unless a `blob://` `file_url` is present.
  - `blob://` image URLs and `image_ref` still become `display_files`.
  - Legacy `display_files` entries with `data:` URLs now project as text diagnostics instead of `{"type": "image", "data": ...}`.
- Updated focused tests:
  - `novaic-cortex/tests/test_step_result_projection.py`
  - `novaic-cortex/tests/test_tool_output_projection.py`

## Criteria Map
- Raw image base64/data URLs are not emitted in `_mcp_content`: satisfied.
- BlobRef `image_ref` behavior remains intact: satisfied.
- Focused projection tests pass: satisfied.
- Targeted scan confirms no active projection emits `{"type": "image", "data": ...}`: satisfied.

## Execution Map
- Patched projection code.
- Updated tests that previously asserted old inline base64 image behavior.
- Ran focused tests:
  - `PYTHONPATH="../novaic-logicalfs:../novaic-sandbox-sdk:${PYTHONPATH:-}" pytest tests/test_step_result_projection.py tests/test_tool_output_projection.py`
  - Result: `21 passed`.
- Ran targeted scans:
  - no `{"type": "image"` emission in `step_result_projection.py`
  - no `data_b64` / `base64.b64encode` / `f"data:{mime};base64"` emission in `step_result_projection.py`

## Stress Test
- The patch does not remove explicit display perception for BlobRefs; `blob://runtime-artifact/...` still becomes `image_ref`.
- The patch protects even legacy `data:` display file inputs by converting them to text diagnostics.
- Existing shell `tool-output.v1` artifact manifests remain text/manifest-oriented.

## Residual Risk
- First test run without local dependency paths failed on missing `logicalfs`/`sandbox_sdk`; rerun with repository-local `PYTHONPATH` passed.

## Result IDs
- Builds on inspection result `R769`.
