# P812 Check: Factory Logs Safe Payload Projection

## Verdict

`success`

## Summary

The factory logs payload projection problem is solved. The scoped static page now has a reusable projection helper, all previously identified payload renderers are wired through it, and aggregate checks prove base64-like/data URL payloads are redacted while BlobRefs remain visible.

## Criteria Map

- Request/response raw JSON detail rendering is bounded/scrubbed: satisfied by `renderRawDetail` using `projectedBodyText` and aggregate renderer test.
- Message and tool-call renderers project large/media-like values: satisfied by `renderMessageBubble` wiring and aggregate renderer test.
- Debug metadata remains visible: satisfied; metadata renderers were left intact and tool names/ids/usage/model fields still render.
- Focused checks prove base64-like payloads are redacted/summarized: satisfied by Node helper and aggregate tests.

## Evidence

- `R800` parent result.
- Child checks:
  - `C845` inventory success.
  - `C846` helper success.
  - `C847` renderer wiring success.
  - `C848` aggregate verification success.
- `git diff --check` passed for `factory-logs.html`.
- Node tests printed `projection_helper_ok` and `factory_log_aggregate_projection_ok`.

## Stress Test

The work was split because one-go would have been too easy to miss a tab. The final aggregate sample covered visual and raw detail views, nested factory metadata, messages, reasoning, tool args, base64-like strings, data URLs, and BlobRefs.

## Residual Risk

No P812-scoped residual risk remains.
