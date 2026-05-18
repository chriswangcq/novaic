# Result: Factory Logs Safe Projection Helper

## Summary

Added deterministic projection helpers to `novaic-llm-factory/static/factory-logs.html` near the existing utility functions. The helpers summarize long strings, redact data URLs and base64-like strings, bound arrays/objects by item/key/depth limits, preserve compact scalars and BlobRefs, and expose `projectedJson` / `projectedText` for renderer wiring.

## Changes

- Added `PROJECTION_LIMITS` and `PAYLOADISH_KEYS`.
- Added detection helpers:
  - `isBlobRefString`
  - `looksLikeDataUrl`
  - `looksLikeBase64`
  - `isPayloadishKey`
- Added projection helpers:
  - `summarizeString`
  - `projectValue`
  - `projectedJson`
  - `projectedText`

## Verification

- `git -C novaic-llm-factory diff --check -- static/factory-logs.html`: passed.
- Node extraction check against the actual helper code in `factory-logs.html`: passed with `projection_helper_ok`.
- Sample check covered:
  - BlobRef preservation
  - base64-like string redaction
  - data URL redaction
  - long string summarization
  - nested payload redaction
  - large array summarization

## Residual Notes

Renderer wiring is intentionally not completed in this ticket; it is covered by the following child problem.
