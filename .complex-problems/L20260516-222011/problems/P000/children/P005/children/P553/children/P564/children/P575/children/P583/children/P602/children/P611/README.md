# UI Chat Attachment BlobRef Rendering

## Problem

Audit chat and application attachment rendering/conversion to ensure uploaded or runtime image attachments are rendered from BlobRef/authenticated URLs and never require raw base64 tool text in normal UI paths.

## Success Criteria

- Records exact scans for chat attachment, BlobRef, image preview, data URL, and base64 paths.
- Cites UI slices for `FileAttachment`, image preview overlay, and application attachment conversion.
- Runs focused tests for attachment conversion/path behavior.
- Creates a follow-up if chat attachment rendering depends on raw base64 tool text.
