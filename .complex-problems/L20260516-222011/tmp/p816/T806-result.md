# Result: Factory Logs Rendering Inventory

## Summary

Mapped raw and structured rendering paths in `novaic-llm-factory/static/factory-logs.html`. The unsafe paths are concentrated in message/reasoning content, tool-call argument pretty-printing, visual fallback raw bodies, `x_factory` metadata, and the raw JSON tab.

## Inventory

### Safe metadata
- `renderMetaGrid` lines 305-318: displays scalar metadata fields with `esc(safeStr(v))`.
- `renderTokensBar` lines 320-338: displays numeric token counts.
- table row rendering lines 261-275: displays compact scalar log metadata.
- `renderToolSchemas` lines 415-443: mostly safe; it displays tool name, description truncated to 200 chars, and parameter names only.
- `renderUsage` lines 459-467: displays usage scalar values.

### Projected payload targets
- `renderMessageBubble` lines 351-407:
  - `reasoning_content` is rendered raw except HTML escaping at lines 366-373.
  - `content` is only sliced to 2000 chars at lines 376-379, with no base64/media/payload detection.
  - tool-call `function.arguments` are parsed and `JSON.stringify` pretty-printed at lines 384-396.
- `renderResponseChoices` lines 445-456:
  - delegates response choice messages to `renderMessageBubble`, so it inherits the same payload risk.
- `renderVisualDetail` lines 471-565:
  - request `messages` delegates to `renderMessages` / `renderMessageBubble` at lines 505-512.
  - request `tools` delegates to `renderToolSchemas` at lines 515-518.
  - `x_factory` is raw `JSON.stringify` at lines 520-528.
  - fallback request/response blocks render raw `log.request_body` / `log.response_body` at lines 530-560.
- `renderRawDetail` lines 567-580:
  - parses request/response bodies and pretty-prints the full JSON with `JSON.stringify` at lines 569-578.

### Helper shape needed
- A deterministic projection helper should accept unknown values and return a display-safe value/string.
- It should:
  - preserve short scalar values and `blob://...` refs
  - summarize long strings
  - redact/summarize base64-like strings and data URLs
  - summarize large arrays/objects
  - treat payload-ish keys such as `data`, `screenshot`, `image`, `audio`, `content`, `response_body`, and `request_body` conservatively
- Renderer wiring should replace direct `JSON.stringify` and raw string rendering in payload targets while leaving safe metadata renderers intact.

## Evidence

- `rg -n "function render|JSON\\.stringify|request_body|response_body|messages|tool_calls|<pre|content|reasoning" novaic-llm-factory/static/factory-logs.html`
- `nl -ba ... | sed -n '330,430p'`
- `nl -ba ... | sed -n '415,470p'`
- `nl -ba ... | sed -n '480,585p'`

## Residual Notes

No code was changed in this inventory ticket.
