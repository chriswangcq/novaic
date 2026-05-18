# Runtime resolves current display image refs for LLM calls

## Problem

Once Cortex returns display media references instead of image bytes, runtime LLM request assembly must resolve only current-round `display_perception` image refs through Blob Service and convert them into provider-ready multimodal content. This must not happen for history, summaries, or non-display tools.

## Success Criteria

- Step-ref expansion resolves `image_ref` only when projection is `display_perception`.
- Blob Service access is explicit and dependency-bounded through runtime config/client inputs.
- Resolved images feed the existing `process_multimodal_messages` path as image MCP content.
- Non-display and historical tool outputs are not fetched as images.
- Oversized or unreadable BlobRefs degrade to bounded text diagnostics, not base64 or crashes.
