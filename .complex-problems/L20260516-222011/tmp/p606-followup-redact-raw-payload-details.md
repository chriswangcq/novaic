# Redact raw payload-like text in ActivityTimeline details

## Problem

Add a frontend safety boundary so ActivityTimeline does not render raw base64-like or data-url-like image payload text in either collapsed preview or expanded inline details, even if an upstream monitor record accidentally contains such text.

## Success Criteria

- `ActivityTimeline.tsx` detects obvious raw payload-like strings such as `data:image/*;base64,` and long base64/JPEG-prefix text.
- Such payload-like text is replaced with a short safe message, preferably pointing to saved payload/artifact availability when `has_payload` is true.
- Focused tests prove collapsed and expanded ActivityTimeline views do not expose raw base64-like payload text.
- Existing ActivityTimeline tests still pass.
