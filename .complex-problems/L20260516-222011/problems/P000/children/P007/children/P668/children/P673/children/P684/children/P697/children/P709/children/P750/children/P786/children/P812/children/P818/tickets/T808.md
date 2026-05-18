# Ticket: Wire Factory Log Renderers To Safe Projection

## Problem Definition

The safe projection helper exists, but factory log renderers still use raw string slices or raw `JSON.stringify` output. The UI will remain unsafe until all relevant render paths call the helper.

## Proposed Solution

- Update `factory-logs.html` renderers identified by `P816`:
  - message reasoning and content
  - tool-call function arguments
  - request `x_factory`
  - visual fallback request/response bodies
  - raw request/response tab
- Preserve metadata-only renderers as-is where they are already safe.
- Keep BlobRefs and compact summaries visible.

## Acceptance Criteria

- Raw request and response tab content uses projected output.
- Message content/reasoning and tool-call arguments use projected output.
- Visual detail fallback bodies and `x_factory` use projected output.
- Remaining direct `JSON.stringify` calls in the file are either inside the helper or explicitly safe metadata/projection calls.
- The edited HTML/JS passes focused checks.

## Verification Plan

- Patch only `novaic-llm-factory/static/factory-logs.html`.
- Re-run Node extraction/sample tests against renderer output for request/response/message/tool sample data.
- Run `git diff --check`.
- Run focused `rg` for `JSON.stringify`, raw `log.request_body`, raw `log.response_body`, `reasoning`, and `content` rendering to classify the remainder.
