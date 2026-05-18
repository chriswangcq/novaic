# Ticket: Add ActivityTimeline Payload Text Redaction

## Problem Definition

ActivityTimeline currently bounds collapsed previews but can show full expanded `record.text` for long non-debug strings. It needs a frontend guardrail against obvious raw payload-like image/base64 text so UI remains safe even if backend projection regresses.

## Proposed Solution

Add a small detector in `ActivityTimeline.tsx` for obvious data URL and long base64/JPEG-prefix payload text. Route detected payload-like text to a short safe message instead of returning the original detail. Add focused tests that prove raw payload-like text is not visible before or after expanding, while existing safe-detail behavior remains intact.

## Acceptance Criteria

- `ActivityTimeline.tsx` suppresses raw payload-like `record.text` in public detail projection.
- The replacement message is short and user-facing.
- Tests cover data URL payload text and long JPEG/base64-like text.
- Existing ActivityTimeline focused test suite passes.

## Verification Plan

Run focused `npm run test:unit` for ActivityTimeline tests after the edit. Inspect code to ensure no `dangerouslySetInnerHTML` or raw payload rendering was introduced.

## Risks

- Over-broad detection could hide legitimate long diagnostic text; keep detection narrow to data URLs and obvious base64/JPEG-like payloads.

## Assumptions

- Backend remains responsible for durable payload/artifact access; this frontend change is a final display guardrail, not the primary data contract.
