# Gate multimodal extraction to display perception

## Problem Definition

The Runtime multimodal processor still treats any tool result containing `_mcp_content` image data as provider-visible image input. This conflicts with the new projection model where only explicit display perception may send visual content to the model.

## Proposed Solution

Have step-ref expansion tag tool messages with an internal `_projection` marker. Then update `process_multimodal_messages()` so:

- `display_perception` tool messages may be converted to provider image user messages;
- all other tool messages are passed through as text/tool content only;
- the internal `_projection` marker is stripped before provider delivery.

## Acceptance Criteria

- Generic tool image `_mcp_content` does not create a user image message.
- Historical display output without `display_perception` does not create a user image message.
- Explicit display perception does create a user image message and keeps the tool result text-only.
- Internal `_projection` is not present in final provider messages.

## Verification Plan

- Run `python -m pytest tests/unit/task_queue/test_no_historical_tool_image_injection.py -q`.
- Run `python -m pytest tests/test_pr71_no_tool_retry_context_cleanup.py tests/test_runtime_explicit_contracts.py tests/test_pr85_llm_context_smoke_guardrails.py -q`.

## Risks

- If a provider requires image content in a different role shape, the explicit display perception test should catch the intended conversion contract.

## Assumptions

- `_projection` is an internal transient field between step-ref expansion and multimodal processing.
