# Runtime step-ref projection selection result

## Summary

Audited runtime step-ref projection selection. The runtime selects projection by current-round status and tool identity: current `display` uses `display_perception`, historical tool messages use `history`, and current non-display tools use `current_tool_result`. Existing focused tests directly assert the projection arguments passed to Cortex formatted step reads.

## Done

- Mapped `novaic-agent-runtime/task_queue/utils/step_result_client.py`:
  - `_latest_tool_call_ids`
  - `_tool_names_by_call_id`
  - `_tool_message_name`
  - `_projection_for_tool_message`
  - `expand_messages_for_llm`
- Confirmed current display can be detected from:
  - explicit `tool_name`,
  - `_metadata.tool`,
  - assistant `tool_calls` mapping.
- Confirmed old display after a newer tool block is downgraded to `history`.
- Confirmed current shell/non-display tool uses `current_tool_result`.

## Verification

- Projection argument tests passed:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py
```

Result: `14 passed in 0.08s`.

- Display/history media guard tests passed:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py
```

Result: `9 passed in 0.08s`.

## Known Gaps

- This ticket only proves projection selection. Media extraction after expansion is judged by P193.
- Provider-specific request schema conversion is judged by P190.

## Artifacts

- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
