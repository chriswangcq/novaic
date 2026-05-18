# Result: Displayed Images Survive Context Assembly

## Summary

Verified and strengthened the displayed-image handoff: public display tool content is now placeholder-only, while durable display payload remains available to Cortex step projection and becomes model-visible image content during display-perception assembly.

## Done

- Added a Cortex projection test in `novaic-cortex/tests/test_tool_output_projection.py` proving `tool-step-payload.v1` display `llm_content` parses into text for history and image content for display perception.
- Reused the runtime tests updated in `P054` to prove public display content is sanitized while `durable_payload["llm_content"]` retains image data.
- Verified the request assembly path with existing runtime tests that inject display step images before following system messages.

## Verification

- `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q tests/unit/task_queue/test_tool_handlers_display_chat_history.py tests/unit/task_queue/test_no_historical_tool_image_injection.py tests/test_pr71_no_tool_retry_context_cleanup.py`
- Result: `27 passed in 0.10s`.
- `cd novaic-cortex && PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_tool_output_projection.py tests/test_step_result_projection.py tests/test_context_event_api_steps_write.py`
- Result: `19 passed in 0.35s`.

## Known Gaps

- Provider adapter/log redaction behavior remains scoped to `P056`.
- This ticket proves runtime/Cortex assembly shape; it does not inspect a live external LLM provider call.

## Artifacts

- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
