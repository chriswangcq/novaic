# Result: Display Tool Public Output Sanitized

## Summary

Fixed the runtime display wrapper so public tool history no longer contains raw image base64. Display executor output may still carry image bytes internally, but `_ok()` now publishes a placeholder-only tool content and stores the raw image result in durable payload for the display-perception path.

## Done

- Updated `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`:
  - added `_display_public_output()` to replace display image entries with placeholders in public tool content,
  - added `_display_durable_payload()` to preserve the raw display result as `tool-step-payload.v1` for later LLM image projection,
  - wired `_ok()` to attach this durable payload for display results.
- Updated display-focused tests:
  - `tests/unit/task_queue/test_tool_handlers_display_chat_history.py` now asserts wrapped display content has no `data` field and durable payload preserves image data.
  - `tests/unit/task_queue/test_no_historical_tool_image_injection.py` now asserts display public content is sanitized before multimodal conversion.

## Verification

- `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q tests/unit/task_queue/test_tool_handlers_display_chat_history.py tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- Result: `13 passed in 0.10s`.

## Known Gaps

- The next LLM request/image assembly path still needs to be audited and checked in `P055`.
- Provider adapter/logging behavior remains scoped to `P056`.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
