# Display Tool History Sanitization Audit

## Problem

`display(blob://...)` may produce current-turn perception content, but public/history tool output must stay sanitized so future context does not contain raw image base64 or data URLs.

## Success Criteria

- Inspect runtime display executor wrapping and Cortex step-result projection.
- Verify historical display tool messages are text or placeholders only.
- Verify current non-display history also remains text-only.
- Fix any projection path that reinserts raw base64 into ordinary context.
