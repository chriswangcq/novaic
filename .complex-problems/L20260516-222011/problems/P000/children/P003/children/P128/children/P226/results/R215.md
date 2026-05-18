# Runtime current/history media boundary result

## Summary

Verified runtime current/history media boundary. Current display can become provider image content; historical and non-display tool results do not create provider images; shell/tool outputs stay bounded public text with durable raw payloads behind the step boundary.

## Done

- Re-inspected `step_result_client.py`, `context.py`, `multimodal.py`, and `tool_handlers.py` branch evidence.
- Ran targeted runtime tests covering historical image suppression, current display multimodal payloads, shell output bounds, and generic tool-output wrapping.

## Verification

- Command:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py \
  novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py
```

- Result: `23 passed in 0.09s`.
- Runtime projection branch evidence:
  - `step_result_client.py:119-139` selects `display_perception` only for current display tool messages.
  - `context.py:203-249` converts only `display_perception` tool results into provider image messages.
  - `multimodal.py:104-131` strips display image bytes from tool-result text with placeholders.
  - `tool_handlers.py:178-242` bounds shell output text and keeps raw shell data in durable payload.

## Known Gaps

- No runtime current/history media-boundary gap found. Active-stack ordering is verified separately in P227.

## Artifacts

- Runtime test command output above.
