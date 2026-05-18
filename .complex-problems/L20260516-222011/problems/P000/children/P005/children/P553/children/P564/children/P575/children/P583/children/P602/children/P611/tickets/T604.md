# Audit Chat Attachment BlobRef Rendering

## Problem Definition

P611 must prove chat attachment and image preview UI paths render image attachments through BlobRef/authenticated URLs rather than raw base64 strings or tool-output text.

## Proposed Solution

Scan chat/application attachment files, cite exact rendering/conversion slices, run focused attachment conversion/path tests, and record whether any risky raw base64 path remains.

## Acceptance Criteria

- Chat attachment/image preview scan is recorded.
- Relevant slices in `FileAttachment`, `ImagePreviewOverlay`, and attachment conversion code are cited.
- Focused attachment tests pass.
- No raw base64 tool-text dependency remains, or a follow-up is created.

## Verification Plan

Run `blobAttachmentPath.test.ts` and `converters.test.ts`, plus any directly relevant chat component tests if present.

## Risks

- Image source code may legitimately consume already-authenticated blob URLs; do not misclassify this as raw base64.

## Assumptions

- BlobRef/authenticated HTTP URL rendering is the intended UI contract.
