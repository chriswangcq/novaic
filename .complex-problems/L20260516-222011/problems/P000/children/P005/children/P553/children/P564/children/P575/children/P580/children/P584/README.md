# Follow-up Problem: Replace display durable image bytes with BlobRef-backed perception fetch

## Problem

P580 found that display public tool history strips image base64 correctly, but `_ok()` still persists `durable_payload.llm_content` containing inline base64 for small images. That is not ordinary shell-visible text, but it is still durable duplicated file bytes inside Cortex/runtime payload state. This conflicts with the infrastructure boundary that Blob Service owns bytes while product services persist BlobRefs and semantics.

## Success Criteria

- Display durable payload stores BlobRef plus MIME/size/metadata, not inline image base64.
- Current-turn display perception still reaches the LLM as provider-native image input.
- The projection path fetches Blob bytes on demand at the current perception boundary or an equivalent explicit media resolver boundary.
- Public tool history remains text-only/placeholder-only.
- Tests that currently assert `durable_payload.llm_content._mcp_content[].data` are updated or removed.
- Focused tests prove no base64 is stored in public content or durable display payload, while provider request still receives the image.
