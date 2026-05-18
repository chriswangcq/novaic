# Runtime display semantic media ref result

## Summary

Fixed the P588 follow-up gap: runtime display durable payload now derives image references from semantic Blob metadata (`file_url`, `mime_type`, `size`) rather than from inline `_mcp_content[].data`.

## Code Changes

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `_display_durable_payload` now returns `None` unless the display result has a BlobRef and image MIME type.
  - It creates `image_ref` and `display_files` from BlobRef metadata first.
  - It preserves any text MCP items as context, but inline image bytes are not required and are never persisted.
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
  - Added a regression test where the display result is an image but `_mcp_content` contains only a large-image text placeholder.
  - The durable payload still includes `image_ref` and remains base64-free.

## Verification

- `python -m pytest novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py -q`
  - Passed: `5 passed in 0.05s`.
- Targeted search:
  - `rg -n "durable_payload.*_mcp_content|llm_content.*data|_mcp_content.*data|assert .*\\[\\\"data\\\"\\].*durable|image_ref|display_files" novaic-agent-runtime/task_queue/handlers/tool_handlers.py novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
  - Remaining matches are intended `image_ref`/`display_files` code and assertions, not durable-base64 requirements.

## Residual Risk

Runtime durable payload shape is fixed. Cortex projection and runtime current-round resolver still need sibling tickets before end-to-end display perception is complete.
