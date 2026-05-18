# Cortex Projection BlobRef-Only Patch

## Problem

Patch the projection behavior based on the inspection child so raw inline media/base64/data URLs are not preserved in LLM context while BlobRef/display manifest behavior remains intact.

## Success Criteria

- Unsafe inline media is scrubbed, summarized, or rejected in projected tool content.
- BlobRef and manifest-style display outputs remain available.
- Focused tests pass.
- Targeted scans confirm no active projection path emits raw image base64/data URLs.
