# Ticket: Verify Factory Logs Projection End To End

## Problem Definition

Factory logs projection helper and renderer wiring are implemented, but the scoped factory-log child needs an aggregate verification pass to catch any missed raw rendering path or unsafe remaining `JSON.stringify`.

## Proposed Solution

- Run a focused aggregate check against `novaic-llm-factory/static/factory-logs.html`.
- Use representative log data containing base64-like strings in request body, response body, messages, reasoning, tool-call arguments, and `x_factory`.
- Verify rendered HTML does not contain raw base64 slices and does contain projection markers.
- Classify all remaining `JSON.stringify` and raw request/response references.

## Acceptance Criteria

- Representative unsafe payload values are redacted/summarized across raw and visual renderers.
- BlobRef values remain visible.
- Static diff/format checks pass.
- Remaining raw-rendering vocabulary in `factory-logs.html` is projection-helper-owned or safe metadata.
- No P812/P819 follow-up is needed.

## Verification Plan

- Run the Node extraction renderer test.
- Run `git diff --check`.
- Run focused `rg` residue scans for `JSON.stringify`, `log.request_body`, `log.response_body`, `reasoning_content`, `tool_calls`, and base64/data URL vocabulary.
- Record exact evidence in the result.
