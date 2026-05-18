# Ticket: Audit Agent Monitor Step Preview Boundary

## Problem Definition

Agent monitor step previews display tool output to humans. They may truncate text or show status snippets, but must not be treated as LLM context and must not render unredacted image bytes from display/tool results.

## Proposed Solution

Scan agent monitor frontend/backend rendering paths for step output, preview, truncation, screenshots, thumbnails, BlobRefs, and base64. Read relevant slices and classify monitor preview behavior.

## Acceptance Criteria

- Exact scans for monitor step preview rendering are recorded.
- Relevant rendering slices are cited with line references.
- Result separates human monitor preview/truncation from LLM request context.
- Any unredacted raw image-byte rendering is recorded as a follow-up.

## Verification Plan

Use read-only scans and source slices. Run focused frontend/backend tests only if existing tests directly target monitor preview rendering.

## Risks

- Monitor code may be spread across app and runtime packages; scan must not stop at the first matching file.

## Assumptions

- Agent monitor timeline is observability UI and does not feed model context.
