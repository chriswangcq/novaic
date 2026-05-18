# Ticket: Inventory Factory Logs Raw Rendering Entrypoints

## Problem Definition

`factory-logs.html` has several rendering functions that may display request/response/message/tool values. We need a concrete inventory before implementing projection so no entrypoint is missed.

## Proposed Solution

- Inspect `novaic-llm-factory/static/factory-logs.html`.
- Map functions that render:
  - raw request/response body tabs
  - structured request visual tab
  - message bubbles
  - tool-call arguments
  - tool schemas/details
- Classify each entrypoint as safe metadata, projected payload, or candidate for removal.

## Acceptance Criteria

- Inventory names every relevant rendering function.
- Inventory identifies the unsafe raw rendering paths and exact value sources.
- Inventory recommends the minimal projection helper and wiring targets.

## Verification Plan

- Use `rg` for `JSON.stringify`, `render`, `messages`, `tool_calls`, `request_body`, `response_body`, and `<pre>`.
- Read the relevant line ranges and record evidence pointers.
- Do not edit production files in this inventory ticket.
