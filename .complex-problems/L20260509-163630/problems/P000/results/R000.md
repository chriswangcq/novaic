# No generic tool image injection result

## Summary

Runtime multimodal processing is now gated by explicit projection mode. Generic/historical tool results no longer synthesize provider-visible image user messages; only `display_perception` may do so.

## Done

- Updated `novaic-agent-runtime/task_queue/utils/step_result_client.py` to attach transient `_projection` to expanded tool messages.
- Updated `novaic-agent-runtime/task_queue/utils/context.py`:
  - non-`display_perception` tool messages bypass image extraction;
  - `_projection` is stripped before provider delivery;
  - explicit `display_perception` retains the existing text-only tool result plus user image conversion.
- Added `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`.
- Updated existing step-ref expansion tests for the transient projection marker.

## Verification

- `python -m pytest tests/unit/task_queue/test_no_historical_tool_image_injection.py tests/test_pr71_no_tool_retry_context_cleanup.py tests/test_runtime_explicit_contracts.py tests/test_pr85_llm_context_smoke_guardrails.py -q`
  - Result: `29 passed in 0.12s`.
- `python -m pytest tests/unit/task_queue/test_user_content.py tests/unit/task_queue/test_tool_handlers_display_chat_history.py tests/test_runtime_tool_path_contract.py -q`
  - Result: `18 passed in 0.06s`.
- `cd novaic-cortex && python -m pytest tests/test_tool_output_projection.py tests/test_step_result_projection.py tests/test_resolve_for_llm.py -q`
  - Result: `20 passed in 0.03s`.

## Residual Risk

- Generic multimodal helper functions still exist because explicit display perception uses them. Later deletion can remove unused helper variants after display becomes fully resource-first.
