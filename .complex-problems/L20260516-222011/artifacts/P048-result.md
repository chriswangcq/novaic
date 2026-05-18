# Media/Base64 Tool Output Contract Result

## Summary

Closed the media/base64 output contract end to end. Active screenshot/media CLI output uses blob/artifact manifests, display image data is sanitized from public tool text while preserved for explicit perception, shell observations stay bounded terminal text, and regression guards now cover base64-like leakage shapes.

## Done

- Closed `P050`: device/screenshot CLI emits `tool-output.v1` artifact manifests instead of raw base64.
- Closed `P051`: display and LLM image projection avoids text base64 and preserves model-visible image input through explicit display perception.
- Closed `P052`: shell observations remain terminal-shaped, bounded text with durable raw output only in payload/RO.
- Closed `P053`: active base64 leakage regression guards classify legitimate fields and harden unstructured public output fallback.

## Verification

- Cortex shell capability blob contract tests: `8 passed`.
- Runtime display/context tests: `19 passed` in the final guard run, plus prior `13 passed` and `27 passed` focused runs.
- Cortex projection tests: `15 passed` in the final guard run, plus prior `19 passed`.
- LLM Factory image/provider tests: `3 passed, 8 deselected` focused run and `11 passed` full chat-route test file.

## Known Gaps

- No known blocking gap for this parent ticket. Base64 is still allowed in the correct places: structured provider-native image fields, explicit display-perception payloads, and durable raw payload/RO records.

## Artifacts

- Parent child results/checks:
  - `P050`: `R037`, `C047`
  - `P051`: `R043`, `C055`
  - `P052`: `R047`, `C059`
  - `P053`: `R050`, `C062`
- Main code/test areas:
  - `novaic-cortex/novaic_cortex/shell_capabilities.py`
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
  - `novaic-cortex/tests/test_tool_output_projection.py`
  - `novaic-llm-factory/tests/test_chat_routes.py`
