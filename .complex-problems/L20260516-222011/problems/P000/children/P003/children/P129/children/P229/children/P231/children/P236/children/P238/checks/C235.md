# Check: runtime display/media handoff avoids raw image text history

## Summary

`P238` is solved by `R221`. Runtime display/media handling has a clear projection marker: only current display perception is converted into structured image content for the model, while historical/default tool text replaces image payloads with placeholders. Focused tests cover the old regression class where tool image/base64 could be injected from history.

## Evidence

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:120-164` sanitizes public display output and stores image-bearing display data in durable payload.
- `novaic-agent-runtime/task_queue/utils/step_result_client.py:119-139` chooses `display_perception` only for current display tool messages and `history` otherwise.
- `novaic-agent-runtime/task_queue/utils/context.py:183-245` converts only `display_perception` tool messages into image user messages and strips `_projection` before final output.
- `novaic-agent-runtime/task_queue/utils/multimodal.py:104-131` replaces image payloads with placeholders in the text-only tool result.
- Focused tests passed: `14 passed in 0.09s`.

## Criteria Map

- Display/media tool result handling and LLM message conversion paths are mapped with file/function pointers: satisfied by handler, step result client, context, and multimodal code pointers.
- Evidence shows normal tool result text is compact and image data is not passed as raw text history: satisfied by placeholder sanitation, projection gating, and tests for historical image injection.
- Focused display/media tests pass, including no historical tool image/base64 injection: satisfied by `test_no_historical_tool_image_injection.py`, `test_tool_handlers_display_chat_history.py`, and `test_factory_client_multimodal.py` passing.

## Execution Map

- Ticket `T227` was a bounded display/media audit.
- Execution inspected display handler and multimodal conversion code, ran focused tests, and recorded `R221`.

## Stress Test

The plausible regression is exactly the screenshot/base64 bug: a previous display result with `_mcp_content` image data gets re-expanded as text in the next request. Tests cover generic tool image content not creating user image messages, history projection markers being stripped without image injection, display perception being the only allowed conversion path, and prepare-LLM-call image insertion before following system messages.

## Residual Risk

Non-blocking for `P238`: provider-specific factory conversion is not exhaustively re-audited here, but runtime handoff and client preservation tests pass; broader provider behavior was handled in earlier projection work and is outside this child scope.

## Result IDs

- `R221`
