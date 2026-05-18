# Active-stack-after-display media preservation result

## Summary

Audited runtime sanitization and multimodal processing for display media when an active-stack system message follows the display tool result. The runtime preserves `_projection=display_perception` through sanitization, replaces image payloads in the tool result with placeholders, emits a separate provider-visible user image message, and keeps the following system message.

## Done

- Mapped `novaic-agent-runtime/task_queue/utils/context.py`:
  - `sanitize_context`
  - `process_multimodal_messages`
- Mapped `novaic-agent-runtime/task_queue/utils/multimodal.py`:
  - `has_images`
  - `extract_from_result`
  - `result_to_text_only`
  - `to_openai_content`
  - `to_anthropic_content`
- Confirmed `_projection` is preserved only until multimodal conversion and stripped before final output.
- Confirmed the exact active-stack-after-display scenario is covered.

## Verification

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py
```

Result: `9 passed in 0.08s`.

Key covered regression:

- `test_prepare_llm_call_injects_display_step_image_before_following_system`
  - Cortex read uses `display_perception`.
  - Final message order is `assistant`, `tool`, `user`, `system`.
  - Tool message image entry is placeholder-only and has no `data`.
  - User message contains `image_url` data URL.
  - Following active-stack system message remains present.

## Known Gaps

- This ticket proves runtime-internal message conversion. Provider/factory final request schema remains P190.

## Artifacts

- `novaic-agent-runtime/task_queue/utils/context.py`
- `novaic-agent-runtime/task_queue/utils/multimodal.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
