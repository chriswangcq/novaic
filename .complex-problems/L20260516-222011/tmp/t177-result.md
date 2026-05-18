# Cortex display projection contract result

## Summary

Audited the Cortex-local display projection boundary. Cortex separates normal/history tool projection from explicit display perception: history and current non-display tool results call `_format_mcp_content(..., include_display=False)`, while `display_perception` calls it with `include_display=True`. Current display media is represented as `_mcp_content` image data when the parsed display file is a data URL, while artifacts and historical displays remain manifest/text-only.

## Done

- Mapped Cortex projection code:
  - `novaic-cortex/novaic_cortex/step_result_projection.py`
    - `parse_tool_result`
    - `_parse_tool_output_v1`
    - `_format_mcp_content`
    - `format_for_history_llm`
    - `format_for_current_tool_result_llm`
    - `format_for_display_perception_llm`
  - `novaic-cortex/novaic_cortex/api.py`
    - `/v1/steps/read_formatted` chooses `history`, `current_tool_result`, or `display_perception`.
- Mapped runtime step-ref client projection selection for current display:
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py`
    - `_projection_for_tool_message`
    - `expand_messages_for_llm`
- Confirmed Cortex history/current-tool formatting does not include display media.
- Confirmed explicit display perception can emit `_mcp_content` image entries for parsed data-url display files.
- Confirmed tool-output artifact manifests remain text-only and do not inline artifact images.

## Verification

- Cortex projection tests passed:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_step_result_projection.py
```

Result: `15 passed in 0.07s`.

- Runtime display-image projection guard tests passed:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py
```

Result: `9 passed in 0.09s`.

## Known Gaps

- Provider request conversion is not judged here; that is P190.
- Runtime current-round media selection and active-stack ordering are not judged here; that is P189.
- End-to-end screenshot/display regression is not judged here; that is P191.

## Artifacts

- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_step_result_projection.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
