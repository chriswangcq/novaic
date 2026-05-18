# Ticket: Derive Runtime Display Media Refs From Blob Metadata

## Summary

Fix runtime display durable payload creation so BlobRef image references are derived from result metadata rather than inline image bytes.

## Problem Definition

The previous runtime change still used `_mcp_content[].data` as the signal for durable image references. That is backwards: BlobRef + MIME metadata is the durable source of truth, while inline bytes are only an optional immediate perception projection.

## Proposed Solution

Change `_display_durable_payload` to create one `image_ref` when `file_url` is present and `mime_type` starts with `image/`. Preserve text from `_mcp_content` if present, but do not require inline image data. Add a large-image/text-placeholder unit test.

## Acceptance Criteria

- Inline image bytes are optional and never persisted.
- Valid image BlobRefs produce durable `image_ref` even when `_mcp_content` contains only text.
- Focused runtime tests pass.

## Verification Plan

Run focused runtime display handler tests and targeted `rg` checks for stale durable-base64 expectations.
