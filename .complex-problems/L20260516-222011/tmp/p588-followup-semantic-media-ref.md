# Runtime display durable media refs must not depend on inline bytes

## Problem

The first P588 implementation removed persisted base64 for inline images, but still derived `image_ref` from `_mcp_content[].data`. This leaves a hidden dependency on inline bytes and fails for large images or future display implementations that return BlobRef metadata without inline image data.

## Success Criteria

- `_display_durable_payload` creates image references from `file_url`, `mime_type`, and `size` when the result represents an image BlobRef.
- Inline `_mcp_content[].data` is never required to create durable `image_ref`.
- Tests cover both a small inline image and a large image/text-placeholder result.
- Durable payload remains base64-free in both cases.
