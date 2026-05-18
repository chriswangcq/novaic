# P609 ActivityTimeline payload redaction check

## Summary

P609 succeeds. The implementation adds a narrow frontend guardrail against obvious raw image/base64 payload text and focused tests prove the raw payload strings are not rendered in collapsed or expanded ActivityTimeline details.

## Evidence

- Code changed:
  - `novaic-app/src/components/Visual/ActivityTimeline.tsx`.
  - `novaic-app/src/components/Visual/ActivityTimeline.test.tsx`.
- Test artifact: `.complex-problems/L20260516-222011/tmp/p609-activity-timeline-tests.txt`.
- Focused tests passed: `Test Files 4 passed (4)`, `Tests 19 passed (19)`.

## Criteria Map

- Detects obvious raw payload-like strings: satisfied by `DATA_IMAGE_BASE64_PATTERN`, `BINARY_BASE64_PREFIX_PATTERN`, and `looksLikeRawPayloadText`.
- Replaces payload-like text with short safe message: satisfied by `RAW_PAYLOAD_DETAIL` returned from `publicFullDetail`.
- Tests prove collapsed and expanded views do not expose raw base64-like text: satisfied by the two new ActivityTimeline tests.
- Existing focused tests still pass: satisfied by the 19-test focused suite.

## Execution Map

- Added detector and safe replacement in the existing public detail projection path.
- Added tests for `data:image/jpeg;base64,...` and long `/9j/` JPEG-like base64.
- Re-ran the focused ActivityTimeline suite.

## Stress Test

- Tested the exact likely failure shapes from the previous incident class: data URL image payload and raw JPEG/base64-like text with secret suffixes.
- Tests assert the secret substrings and base64 prefixes are absent from rendered output, and no expansion control appears for the redacted payload detail.

## Residual Risk

- Non-blocking: detection is deliberately narrow and may not catch every arbitrary encoded binary format. It covers the practical image/base64 shapes without hiding normal long text.

## Result IDs

- R591
