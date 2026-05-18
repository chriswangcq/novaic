# Cortex Step Result Projection BlobRef Contract Patch Ticket

## Problem Definition

`novaic-cortex/novaic_cortex/step_result_projection.py` still preserves compatibility for direct inline MCP image/data URL payloads. The current tool contract should keep shell output textual/manifest-oriented and use BlobRef plus explicit display projection for images, without carrying raw base64/data URLs in LLM context.

## Proposed Solution

Inspect `step_result_projection.py` and its tests. Remove or narrow inline-image/data-URL compatibility to manifest-only/safe text while preserving BlobRef and display tool behavior. Add or update focused tests so base64/data URL payloads are scrubbed or summarized and BlobRef paths still work.

## Acceptance Criteria

- Raw base64/data URL image payloads are not preserved in projected LLM tool content.
- BlobRef/display manifest behavior remains intact.
- Focused tests cover both unsafe inline media and safe BlobRef/display output.
- Targeted scans do not find active projection code that reintroduces raw MCP image data into context.

## Verification Plan

Run focused Cortex tests for step result projection. If no focused tests exist, add one near existing Cortex tests. Also run targeted `rg` over `step_result_projection.py` for `data:image`, `base64`, and inline image compatibility.
