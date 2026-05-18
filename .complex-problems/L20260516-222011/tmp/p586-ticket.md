# Ticket: Implement BlobRef-Backed Display Perception

## Summary

Replace the current durable display image-byte contract with a BlobRef-backed perception contract across runtime display execution, Cortex step-result projection, runtime LLM request assembly, tests, and stale-code cleanup.

## Problem Definition

Current `display` execution keeps public history safe, but durable display payloads still preserve `_mcp_content[].data` base64 image bytes. That violates the intended contract: Blob Service owns bytes, Cortex persists semantic step references, and runtime resolves current-round display perception just before the LLM request.

## Proposed Solution

Implement the `P585` design in focused child problems:

- Runtime display durable payload stores text, metadata, and BlobRef media references only.
- Cortex projection preserves display media references as explicit `image_ref` content for `display_perception`, while history remains text/reference-only.
- Runtime step-ref expansion resolves `image_ref` through Blob Service only for current-round `display_perception`, with explicit dependencies and size limits.
- Tests and old assertions are updated so no active path expects persisted base64.

## Acceptance Criteria

- No display durable payload stores image base64 under `llm_content`.
- Current-round `display` still reaches provider request assembly as image content.
- Historical display outputs and summaries do not re-inject images.
- Legacy tests or helper branches that encode the old durable-base64 contract are removed or rewritten.
- Focused runtime and Cortex tests pass.

## Verification Plan

Run focused unit tests for:

- runtime display handler output contract,
- Cortex step-result projection,
- runtime step-ref expansion and multimodal image projection,
- shell/tool output history safety.

Also run targeted searches proving display durable payload code and tests no longer depend on `_mcp_content[].data` persistence.
