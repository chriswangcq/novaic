# Formatted step read and display projection refs mapped

## Summary

Mapped the formatted-read/display-projection path. Runtime LLM preparation expands tool messages by stable `step_ref`; Cortex locates the step using that stable ref, then reads the actual payload using the normalized final `payload_ref` stored on the step. Public tool content remains placeholder/text-safe, while explicit display perception can produce LLM image input.

## Source Map

- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
  - `expand_messages_for_llm(...)` requires `step_ref` on tool messages.
  - Projection selection is current-round aware: display tool messages become `display_perception`; other current tools become `current_tool_result`; old tool messages become `history`.
  - `expand_step_ref_to_content(...)` calls `bridge.read_step_formatted(..., step_ref=step_ref)`.
- `novaic-cortex/novaic_cortex/api.py`
  - `_find_step_by_call_id_in_path(...)` can match `entry.step_ref == requested step_ref` even after payload externalization changes `entry.payload_ref`.
  - `_read_step_payload(...)` reads the actual payload through `step.payload_ref`.
  - `steps_read_formatted(...)` formats `history`, `current_tool_result`, and `display_perception` projections.
- `novaic-cortex/novaic_cortex/step_result_projection.py`
  - `format_for_history_llm(...)` and `format_for_current_tool_result_llm(...)` are text/manifest only.
  - `format_for_display_perception_llm(...)` is the only projection that includes display media.
- Runtime multimodal tests:
  - Sanitization strips raw image data from tool messages and injects LLM image content only through explicit `display_perception`.

## Verification

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_context_event_api_steps_write.py \
  novaic-cortex/tests/test_tool_output_projection.py
```

Result: `14 passed in 0.34s`.

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py \
  novaic-agent-runtime/tests/test_runtime_explicit_contracts.py
```

Result: `26 passed in 0.15s`.

## Findings

- No production code change was needed in this leaf.
- Existing Cortex test `test_steps_read_formatted_resolves_externalized_payload_by_stable_step_ref` covers the important split: lookup by stable `step_ref`, read by final externalized `payload_ref`.
- Existing runtime tests cover display image injection order, public placeholder safety, non-display media suppression, and history-projection non-injection.

## Residual Notes

P179 still needs the cross-layer regression/ambiguity inventory to make sure no legacy compatibility branch outside this path treats `step_ref` and `payload_ref` as silently interchangeable.
