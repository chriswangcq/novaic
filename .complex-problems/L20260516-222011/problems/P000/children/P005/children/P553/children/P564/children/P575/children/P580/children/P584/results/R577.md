# Replace display durable image bytes with BlobRef-backed perception fetch result

## Summary

Closed the follow-up that was created when `P580` found display durable payloads still persisted image bytes. The final contract is now: display durable payloads store BlobRef references, Cortex preserves references, and runtime resolves current-round display references into image MCP content only at LLM request assembly time.

## Completed Children

- `P585`: mapped the call path and selected the ownership boundary.
- `P586`: implemented BlobRef-backed display perception across runtime, Cortex, resolver, and cleanup.
- `P587`: verified no durable-base64 persistence and current-round image delivery with focused tests and static scans.

## Verification Summary

- Runtime/Cortex focused display tests: passed.
- Related boundary tests: passed.
- Consolidated final verification: `60 passed in 1.34s`.
- Changed Python compile check: passed.
- Static scans found no suspicious durable/base64 persistence.

## Resulting Architecture

- Blob Service owns image bytes.
- Display tool validates/fetches bytes for immediate metadata/classification but persists only references.
- Cortex stores and projects semantic references, not bytes.
- Runtime step-ref expansion resolves references only for current display perception.
- Multimodal conversion moves image bytes out of tool text into provider-native image input.

## Residual Risk

No local display-contract gap remains. Live deploy/smoke is still a separate operational action.
