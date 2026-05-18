# Runtime display durable payload BlobRef-only result

## Summary

Implemented the runtime side of the display durable payload contract. Display execution can still fetch Blob Service bytes and return immediate image MCP content in memory, but `_ok(..., tool_name="display", ...)` now persists only text, metadata, `image_ref`, and `display_files` BlobRef references in `durable_payload.llm_content`.

## Code Changes

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - Reworked `_display_durable_payload` so it no longer copies the raw display result.
  - Durable content now contains:
    - `message`,
    - `file_url`,
    - `mime_type`,
    - `size`,
    - `_mcp_content` with text plus `image_ref`,
    - `display_files` with BlobRef metadata.
  - Durable content no longer contains image `data`.
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
  - Rewrote the focused display test so public output has no image data and durable payload asserts BlobRef-backed `image_ref` / `display_files`.
  - Removed the old assertion that durable payload should equal the inline base64 image data.

## Verification

- `python -m pytest novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py -q`
  - Passed: `4 passed in 0.06s`.
- Targeted search:
  - `rg -n "durable_payload.*_mcp_content|_mcp_content.*\\[0\\].*data|llm_content.*data|image_ref|display_files" novaic-agent-runtime/task_queue/handlers/tool_handlers.py novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
  - Remaining matches are the intended new `image_ref`/`display_files` code and assertions, not durable base64 expectations.

## Residual Risk

This child only fixes the runtime durable payload shape. Cortex projection and runtime image-ref rehydration for current-round LLM calls are intentionally still open in sibling child problems.
