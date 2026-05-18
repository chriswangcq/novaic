# P606 timeline preview check

## Summary

Not successful yet. R590 proves the collapsed timeline preview is bounded and React-escaped, and the tests pass. However, R590 also identifies a real frontend boundary gap: expanded inline details can render the full `record.text` for long non-debug strings, and there is no frontend detector for raw base64/data-url-like image text. Because this is a one-go result and the problem explicitly asks for a follow-up if raw image bytes can be rendered from tool text, the gap must be closed.

## Blocking Gaps

- `publicPreviewDetail` bounds collapsed text, but `ActivityTimelineRow` can set `detail = fullDetail` when expanded. If upstream sends long base64-like text as `record.text`, the expanded UI can render that full text.
- `publicFullDetail` filters JSON/debug/action records, but does not filter base64-like or data-url-like payload text.
- The current tests do not assert that base64-like tool text is suppressed or replaced with a safe payload message.

## Result IDs

- R590
