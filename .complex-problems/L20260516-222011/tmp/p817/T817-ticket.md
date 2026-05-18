# Ticket: Implement Factory Logs Safe Projection Helper

## Problem Definition

Factory logs renderers need one deterministic helper for unsafe values. Without a shared helper, each renderer will continue using ad hoc truncation or raw `JSON.stringify`.

## Proposed Solution

- Add local JavaScript helpers inside `novaic-llm-factory/static/factory-logs.html`.
- Implement:
  - detection for base64-like strings and data URLs
  - long string summarization
  - recursive object/array projection with depth and item limits
  - conservative handling for payload-ish keys such as `data`, `screenshot`, `image`, `audio`, `content`, `request_body`, and `response_body`
  - preservation of compact scalar metadata and `blob://...` references
- Keep helpers framework-free and deterministic.

## Acceptance Criteria

- Helper functions exist near existing utilities.
- Helper returns display-safe values suitable for `JSON.stringify` or direct text rendering.
- Long/base64-like/media-like values are summarized without retaining raw bytes.
- Short scalars and BlobRefs remain readable.
- No renderer wiring is required in this ticket beyond helper-local smoke hooks if needed.

## Verification Plan

- Inspect helper code after editing.
- Run a focused extraction/static syntax check with Node if feasible.
- Use representative sample values to prove projection behavior for base64-like string, long text, BlobRef, nested payload object, and large array.
- Run `git diff --check` for the touched HTML file.
