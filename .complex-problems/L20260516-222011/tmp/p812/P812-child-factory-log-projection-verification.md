# Child Problem: Factory logs projection verification

## Problem

The factory logs scrub change needs focused verification so future regressions do not reintroduce raw base64/large JSON display through another renderer.

## Success Criteria

- Representative long/base64-like request, response, message, and tool argument values are verified as summarized/redacted.
- Static syntax checks for the edited HTML/JS pass.
- Remaining `JSON.stringify` uses in `factory-logs.html` are classified as projected-safe, metadata-only, or removed.
