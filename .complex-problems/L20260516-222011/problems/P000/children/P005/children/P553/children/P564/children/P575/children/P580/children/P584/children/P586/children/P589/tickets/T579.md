# Ticket: Preserve BlobRef Display Media References In Cortex Projection

## Summary

Teach Cortex step-result projection to parse and format BlobRef-backed display media references without embedding image bytes.

## Problem Definition

Runtime display durable payload now stores `image_ref` and `display_files` references. Cortex projection must preserve those references for `display_perception`, while history and summary projections remain text/reference-only.

## Proposed Solution

Update `novaic-cortex/novaic_cortex/step_result_projection.py` so `parse_tool_result` recognizes MCP `image_ref` content and BlobRef-backed `display_files`. Update display perception formatting to emit `image_ref` items for BlobRefs instead of converting them to plain text. Keep data URLs supported for legacy/current inline cases until runtime resolver replaces the full path.

## Acceptance Criteria

- BlobRef `image_ref` input becomes a display file reference.
- BlobRef `display_files` becomes `image_ref` in `display_perception`.
- History formatting remains text-only.
- Data URL image behavior is not accidentally broken.
- Focused Cortex projection tests pass.

## Verification Plan

Run focused Cortex projection tests and targeted `rg` checks around `image_ref`, `display_files`, and data URL handling.
