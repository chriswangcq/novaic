# Child Problem: Implement BlobRef-backed display perception

## Problem

Change display durable payload and projection code so durable display payloads keep BlobRef metadata instead of inline image bytes, while current display perception still emits provider image content.

## Success Criteria

- Runtime display durable payload has no image `data` base64.
- Perception projection resolves BlobRef on demand or uses an explicit media resolver to produce image MCP content for current display perception.
- Public/history projections remain text-only.
- Obsolete tests expecting durable base64 are rewritten or deleted.

