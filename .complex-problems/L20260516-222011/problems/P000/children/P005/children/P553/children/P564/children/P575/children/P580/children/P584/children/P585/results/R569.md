# Display BlobRef perception design and call-path map result

## Summary

Mapped the active display perception path from runtime tool execution through Cortex step formatting and runtime LLM request assembly. The current public tool history is already mostly safe, but the durable display payload still persists image bytes under `durable_payload.llm_content._mcp_content[].data`. That means the next LLM turn can recover image bytes from Cortex step payloads, and the persisted step payload can still carry base64 rather than a BlobRef-owned byte boundary.

## Evidence

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:118-139`: `_display_public_output` replaces image items with placeholders, so the public shell/tool text output no longer exposes the base64 payload.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:142-164`: `_display_durable_payload` copies the full raw display result into `llm_content`, preserving `_mcp_content[].data`.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:362-397`: `_display_content_for_llm` still creates immediate image MCP content from Blob Service bytes for small images.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:400-422`: `_exec_display` validates BlobRefs and fetches Blob Service using `X-Tenant-ID`, so display can verify and classify the blob without persisting bytes.
- `novaic-agent-runtime/task_queue/utils/step_result_client.py:20-42`: runtime resolves Cortex step refs through `read_step_formatted`.
- `novaic-agent-runtime/task_queue/utils/step_result_client.py:119-139`: only current-round display tool results use `display_perception`; history and non-display tools remain text projections.
- `novaic-agent-runtime/task_queue/utils/context.py:183-250` and `novaic-agent-runtime/task_queue/utils/multimodal.py:1-150`: runtime converts display-perception image MCP content into provider-native multimodal input.
- `novaic-cortex/novaic_cortex/api.py:1829-1865`: Cortex `/v1/steps/read_formatted` formats step payloads by projection.
- `novaic-cortex/novaic_cortex/step_result_projection.py:143-179`: Cortex parses `_mcp_content` image data into `display_files`.
- `novaic-cortex/novaic_cortex/step_result_projection.py:202-244`: `display_perception` re-emits data-URL display files as image MCP content, while non-data URLs become text.
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py:95-101`: current test explicitly expects durable payload base64, proving the undesired contract is encoded in tests.

## Design Decision

Use BlobRef as the durable media boundary and keep bytes out of persisted display step payloads.

The preferred split of responsibilities is:

- `display` runtime tool may fetch Blob Service bytes only for immediate validation and metadata extraction.
- Public tool history remains terminal-style text and placeholders.
- Durable display payload stores text, metadata, and BlobRef references, not base64 image bytes.
- Cortex remains a semantic projection service. It should format persisted display media references as explicit media references, not fetch Blob bytes.
- Runtime LLM request assembly resolves current-round display media references into provider-ready image content just before the LLM call.

## Proposed Concrete Contract

Display durable payload should be shaped around a BlobRef reference:

```json
{
  "version": "tool-step-payload.v1",
  "llm_content": {
    "success": true,
    "message": "Loaded image-1 (154.0KB, image/jpeg)",
    "file_url": "blob://runtime-artifact/artifact-1",
    "mime_type": "image/jpeg",
    "size": 154169,
    "_mcp_content": [
      {"type": "text", "text": "Loaded image-1 (154.0KB, image/jpeg)"},
      {
        "type": "image_ref",
        "file_url": "blob://runtime-artifact/artifact-1",
        "mimeType": "image/jpeg",
        "size": 154169
      }
    ]
  },
  "raw": {
    "type": "display_result",
    "file_url": "blob://runtime-artifact/artifact-1",
    "mime_type": "image/jpeg",
    "size": 154169
  }
}
```

Then the current-round display perception path should:

1. Read the Cortex step formatted payload.
2. Preserve `image_ref` in Cortex projection output.
3. In runtime request assembly, resolve `image_ref` through Blob Service only for `display_perception`.
4. Replace `image_ref` with provider-compatible `image` MCP content for the LLM call.
5. Keep history, summaries, monitor output, and persisted payloads text/reference-only.

## Follow-Up Implementation Scope

- Change `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` so display durable payload never includes `_mcp_content[].data`.
- Change `novaic-cortex/novaic_cortex/step_result_projection.py` so display perception can carry `image_ref` rather than degrading BlobRefs to text or rehydrating base64 from persisted payloads.
- Add a runtime image-ref resolver in the step-ref expansion path, with explicit Blob Service dependency and current-round `display_perception` gating.
- Update tests that currently assert base64 durability.
- Add regression tests proving:
  - public shell/tool output is text/reference-only,
  - durable payload has BlobRef but no base64,
  - current display perception still reaches the model as image content,
  - historical display output does not re-inject old images.

## Residual Risk

This result is a design/map only. The known gap remains open until the follow-up implementation replaces durable base64 with BlobRef and verifies the LLM request path end to end.
