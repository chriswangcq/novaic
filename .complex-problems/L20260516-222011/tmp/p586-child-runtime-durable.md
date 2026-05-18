# Runtime display durable payload is BlobRef-only

## Problem

`novaic-agent-runtime/task_queue/handlers/tool_handlers.py` currently stores display image bytes in `durable_payload.llm_content._mcp_content[].data`. This child problem must change runtime display durable payload construction so persisted step payloads contain only text, metadata, and BlobRef media references.

## Success Criteria

- `_display_durable_payload` never copies image `data` into durable payload.
- Durable payload carries enough metadata for later perception: BlobRef, mime type, size, and a stable media reference item.
- Public display output remains terminal-style text/placeholder and never includes base64.
- Existing direct runtime display behavior remains valid for immediate tool execution.
