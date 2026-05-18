# App message media and Blob renderer discovery ticket

## Problem Definition

Chat/message UI and media renderer code may still expect raw base64/data URLs instead of BlobRefs/artifact manifests and cached Blob bytes.

## Proposed Solution

Scan app frontend chat/message/media files for image/audio/video rendering, attachments, Blob refs, data URLs, base64 handling, display results, and artifact manifests. Inspect high-signal files and classify whether raw media handling is still part of LLM/tool context or only frontend byte rendering.

## Acceptance Criteria

- Relevant message/media renderer files are discovered.
- Suspicious media/base64/blob/artifact hits are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend files are modified.

## Verification Plan

Use `rg --files`, focused `rg -n -i`, and targeted slices under `novaic-app/src`.

## Risks

- Frontend may legitimately use data URLs to display already-fetched Blob bytes; that must be classified separately from LLM context payload leakage.

## Assumptions

- Message/media rendering code lives under `novaic-app/src`.
