# Display perception tests and stale durable-base64 cleanup

## Problem

Tests currently encode the old durable-base64 contract. After runtime/Cortex/resolver changes, tests must prove the new contract and remove stale assertions or helper code that implies display bytes belong in durable Cortex payloads.

## Success Criteria

- Unit tests prove runtime durable display payload contains BlobRef references and no base64 `data`.
- Cortex projection tests prove BlobRef image references survive `display_perception` and remain text-only in history.
- Runtime expansion tests prove current display refs become provider image input and historical refs do not.
- Targeted searches show no active test or code path expects `durable_payload.llm_content._mcp_content[].data` for display.
- Focused test commands pass.
