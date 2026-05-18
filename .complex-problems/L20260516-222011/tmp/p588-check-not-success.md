# P588 Check

## Summary

Not successful yet. The implementation removes durable base64 for small inline display images, but `_display_durable_payload` still discovers display media by looking for `_mcp_content` image items with `data`. That keeps the durable contract coupled to inline bytes and can drop BlobRef perception for images that are too large to inline or for future display implementations that never create inline image data.

## Gap

Durable display media references must be derived from semantic result metadata (`file_url`, `mime_type`, `size`) rather than from the presence of base64 in `_mcp_content`.

## Evidence

- `_display_durable_payload` currently loops over `mcp_content` and only creates `image_ref` when `item.get("type") == "image"` and `item.get("data")`.
- `_display_content_for_llm` emits text instead of image MCP content when image size exceeds the inline budget.
- Therefore a large image with valid BlobRef would not produce a durable `image_ref`.

## Required Follow-Up

Create durable display media references from `file_url` + image MIME metadata first, and treat `_mcp_content` only as optional text/context, not as the authority for whether a media reference exists.
