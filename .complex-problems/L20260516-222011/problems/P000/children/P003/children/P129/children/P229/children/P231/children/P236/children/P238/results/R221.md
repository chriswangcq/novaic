# Result: runtime display/media handoff audited

## Summary

Display/media handoff avoids raw image text in normal history. Direct display execution can fetch Blob images and produce `_mcp_content`, but public history projection sanitizes image items into placeholders. Runtime context expansion marks only current display tool results as `display_perception`; `process_multimodal_messages` strips markers, keeps history/current non-display tool results as text, and converts only display perception image content into structured provider image messages.

## Done

- Mapped display durable payload/public sanitization in `tool_handlers.py`.
- Mapped display file loading and `_mcp_content` creation in `_exec_display` and `_display_content_for_llm`.
- Mapped runtime context expansion projection selection in `step_result_client.py`.
- Mapped multimodal conversion boundary in `context.py` and `multimodal.py`.
- Ran focused display/media tests.

## Verification

- Code evidence: `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:120-164` sanitizes public display image content into placeholders and keeps image-bearing display results in durable payload.
- Code evidence: `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:362-422` loads Blob content for display and creates `_mcp_content`, with images only in inline display content under the display contract.
- Code evidence: `novaic-agent-runtime/task_queue/utils/step_result_client.py:119-139` marks only current display tool messages as `display_perception`; non-current tools become `history`.
- Code evidence: `novaic-agent-runtime/task_queue/utils/context.py:183-245` converts only `display_perception` tool messages into provider image messages; other tool/history messages remain tool text.
- Code evidence: `novaic-agent-runtime/task_queue/utils/multimodal.py:104-131` replaces display image payloads with placeholders in the tool message text.
- Test command: `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py`.
- Test result: `14 passed in 0.09s`.

## Known Gaps

- Provider-specific request conversion beyond runtime client preservation is not fully re-audited here; factory provider tests were covered earlier and broader provider conversion is outside this child scope.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/task_queue/utils/context.py`
- `novaic-agent-runtime/task_queue/utils/multimodal.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py`
