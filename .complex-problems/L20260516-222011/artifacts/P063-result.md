# Public-Surface Base64 Leakage Guard Result

## Summary

Strengthened the active public-surface guard. Runtime unstructured tool fallback now sanitizes nested image bytes before JSON text serialization, so non-display tools cannot accidentally leak `_mcp_content` image `data` through public tool text.

## Done

- Updated `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`.
  - Added `_sanitize_media_bytes_for_public()`.
  - Routed `_unstructured_result_text()` through the sanitizer before JSON serialization.
  - The sanitizer recursively omits image `data` and replaces it with placeholder metadata for public text.
- Strengthened `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`.
  - `test_runtime_wrapper_does_not_preserve_media_for_non_display_tools` now asserts the sentinel base64 is absent and placeholder text is present.
- Reused P061 runtime/Cortex guards and P056/P058 LLM Factory guards as adjacent coverage.

## Verification

- `cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q tests/unit/task_queue/test_no_historical_tool_image_injection.py tests/unit/task_queue/test_shell_output_contract.py tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
  - Passed: `19 passed`.
- `cd novaic-cortex && PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_tool_output_projection.py tests/test_step_result_projection.py`
  - Passed: `15 passed`.
- `cd novaic-llm-factory && PYTHONPATH=. pytest -q tests/test_chat_routes.py -k 'image or anthropic_provider_converts'`
  - Passed: `3 passed, 8 deselected`.

## Known Gaps

- No known gap for this guard slice. The guard intentionally allows provider-native or display-perception structured image payloads; it rejects accidental public text leakage.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
