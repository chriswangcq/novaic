# Result: Wire Factory Log Renderers To Safe Projection

## Summary

Updated `novaic-llm-factory/static/factory-logs.html` so the renderers identified by `P816` use the safe projection helpers from `P817` instead of raw truncation or raw JSON/string rendering.

## Changes

- Added `projectedBodyText` for request/response body display.
- Wired `renderMessageBubble`:
  - `reasoning_content` now uses `projectedText`.
  - `content` now uses `projectedText`.
  - tool-call `function.arguments` now parse and use `projectedJson` / `projectedText`.
- Wired `renderVisualDetail`:
  - `x_factory` now uses `projectedJson`.
  - fallback request/response body blocks now use `projectedBodyText`.
- Wired `renderRawDetail`:
  - raw request/response tabs now use `projectedBodyText`.

## Verification

- `git -C novaic-llm-factory diff --check -- static/factory-logs.html`: passed.
- Node renderer extraction test against the actual HTML code: passed with `factory_log_renderer_projection_ok`.
- Renderer test covered:
  - message content redaction
  - reasoning redaction
  - tool-call argument redaction
  - raw request/response tab redaction
  - visual detail redaction
  - BlobRef preservation in tool arguments
- Focused `rg` showed remaining `JSON.stringify` calls are inside projection helpers or projected call sites, and raw `log.request_body` / `log.response_body` usage now flows through parse/projection helpers.

## Residual Notes

No P818-scoped residual risk remains. Aggregate verification remains in child problem `P819`.
