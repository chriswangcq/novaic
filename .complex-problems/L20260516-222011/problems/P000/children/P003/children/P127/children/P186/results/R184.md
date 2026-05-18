# Historical display and artifact manifest projection result

## Summary

Audited historical display/artifact projection. Historical artifacts are manifest/text-only with explicit display access hints, old display steps use `history`, and historical or generic image-like tool results do not create provider image messages.

## Done

- Mapped relevant projection paths:
  - Cortex `parse_tool_result`, `_parse_tool_output_v1`, `format_for_history_llm`, `format_for_display_perception_llm`.
  - Runtime `expand_messages_for_llm`, `_projection_for_tool_message`, `process_multimodal_messages`.
- Confirmed tool-output artifacts render as manifest text and include `display(file_url="...")` access hints.
- Confirmed artifact images are not inlined by display perception.
- Confirmed old display after a newer tool block uses `history`.
- Confirmed generic/historical tool image content does not create user image messages.

## Verification

- Cortex projection tests:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_step_result_projection.py
```

Result: `15 passed in 0.07s`.

- Runtime historical display/image guard tests:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py
```

Result: `23 passed in 0.09s`.

## Known Gaps

- None for historical backend projection. UI rendering of artifact previews is outside this ticket.

## Artifacts

- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_step_result_projection.py`
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
