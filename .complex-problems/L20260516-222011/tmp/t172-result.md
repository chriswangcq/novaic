# Active stack plus current display media regression result

## Summary

Verified the exact active-stack/display regression path. Existing focused tests already cover a current display tool result followed by an active stack system message: the provider-ready messages preserve the tool placeholder, inject the image as a user visual input, and keep the following system stack message after the inserted image. Historical display outputs remain history/text-only and do not reinject raw media.

## Done

- Reviewed `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`.
- Confirmed `test_prepare_llm_call_injects_display_step_image_before_following_system` covers:
  - assistant display tool call,
  - display tool result resolved by `step_ref`,
  - following `[Active skill stack]` system message,
  - final provider message roles: `assistant`, `tool`, `user`, `system`,
  - `display_perception` projection,
  - raw image data removed from tool payload and inserted as user image input.
- Confirmed broader step-result tests cover current display selection and old display non-reinjection:
  - display projection by explicit tool name,
  - display projection by Cortex metadata,
  - inference from assistant tool call,
  - old display becomes `history` after a newer tool block.

## Verification

Focused runtime suite passed:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py \
  novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py \
  novaic-agent-runtime/tests/test_runtime_explicit_contracts.py
```

Result: `53 passed in 0.16s`.

## Known Gaps

- No test gap found for the active-stack-after-display regression.
- No production code change required.

## Artifacts

- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
- `novaic-agent-runtime/task_queue/contracts/llm_call.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/task_queue/utils/context.py`
