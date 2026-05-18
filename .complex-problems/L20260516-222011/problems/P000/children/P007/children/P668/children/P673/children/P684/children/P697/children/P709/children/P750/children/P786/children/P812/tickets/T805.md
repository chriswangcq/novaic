# Ticket: Add Safe Projection To Factory Logs Detail Rendering

## Problem Definition

`novaic-llm-factory/static/factory-logs.html` renders request/response bodies, message content, tool-call arguments, and tool observation content by pretty-printing raw JSON or raw strings. Large payloads and base64-like values can therefore appear directly in the logs UI.

## Proposed Solution

- Introduce a small client-side projection layer for the static logs page.
- Redact or summarize long strings, base64-like strings, large arrays/objects, and media-looking payload fields before rendering.
- Apply the projection consistently to:
  - raw request body view
  - raw response body view
  - structured message bubbles
  - tool-call arguments
  - tool/schema details where relevant
- Preserve useful debugging metadata such as roles, status, model, latency, token counts, tool names, ids, and compact references.

## Acceptance Criteria

- Raw request/response detail blocks no longer blindly render unbounded JSON/string payloads.
- Structured message and tool renderers use the same safe projection helper for large/raw values.
- Blob refs and compact textual summaries remain visible.
- The page still loads without framework/build changes.
- Focused static checks or lightweight script tests demonstrate that base64-like and very long payloads are redacted/summarized.

## Verification Plan

- Inspect the existing rendering functions before editing.
- Patch the static HTML/JS only.
- Run a focused syntax/static check for the HTML/JS if available.
- Use a small Node or shell-based projection check against representative large/base64-like JSON.
- Re-run `rg` for raw `JSON.stringify` rendering paths in the file and classify or reduce remaining ones.
