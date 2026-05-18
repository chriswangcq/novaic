# Cortex Step Result Projection BlobRef Contract Cleanup

## Problem

`novaic-cortex/novaic_cortex/step_result_projection.py` still has compatibility paths for direct MCP inline image/data URL display perception. The final contract should avoid preserving raw media payloads in context and prefer BlobRef/tool-output manifest paths.

## Success Criteria

- Direct inline image/data URL compatibility is removed or narrowed to a safe manifest-only projection.
- Existing BlobRef/display behavior remains intact.
- Focused Cortex tests cover the projection behavior.
- Targeted scans show no active path reintroduces base64/data URL display payloads into LLM context.
