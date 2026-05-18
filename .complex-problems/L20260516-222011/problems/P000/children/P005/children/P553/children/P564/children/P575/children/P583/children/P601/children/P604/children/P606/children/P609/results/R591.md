# ActivityTimeline payload-like text redaction result

## Summary

Added a narrow frontend guardrail in `ActivityTimeline.tsx` that detects obvious raw image/base64 payload text and replaces it with a short safe monitor message. Added focused tests proving both data URL image payloads and long JPEG-like base64 strings are hidden and cannot be revealed through expansion.

## Done

- Added `DATA_IMAGE_BASE64_PATTERN`, `BINARY_BASE64_PREFIX_PATTERN`, and `looksLikeRawPayloadText` in `novaic-app/src/components/Visual/ActivityTimeline.tsx`.
- Routed payload-like text through `RAW_PAYLOAD_DETAIL` before public detail preview/expansion.
- Added two ActivityTimeline tests:
  - hides raw image data URLs.
  - hides long JPEG-like base64 text from expanded details.
- Re-ran the focused ActivityTimeline suite.

## Verification

- Test command:
  - `cd novaic-app && npm run test:unit -- src/components/Visual/ActivityTimeline.test.tsx src/components/Visual/ActivityTimeline.acceptance.test.tsx src/components/Visual/ActivityTimeline.guard.test.ts src/components/hooks/useActivityTimeline.test.ts`
- Test result:
  - `Test Files 4 passed (4)`
  - `Tests 19 passed (19)`
- Code evidence:
  - `novaic-app/src/components/Visual/ActivityTimeline.tsx` lines around the new payload detector and `publicFullDetail`.
  - `novaic-app/src/components/Visual/ActivityTimeline.test.tsx` lines around the new redaction tests.

## Known Gaps

- Detection is intentionally narrow; it is not a general binary classifier. This avoids hiding normal long text while covering the obvious raw image/base64 failure modes.
- Backend remains the primary boundary for storing payloads as BlobRefs; this frontend change is a final UI guardrail.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p609-activity-timeline-tests.txt`
