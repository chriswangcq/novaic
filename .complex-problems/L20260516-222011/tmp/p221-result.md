# Focused projection test chain result

## Summary

Ran the focused Cortex/runtime/factory projection regression chain. All three commands passed.

## Done

- Ran Cortex projection tests.
- Ran runtime task-queue no-historical-image and factory-client multimodal tests.
- Ran factory chat/log tests, including the new Gemini inlineData regression.

## Verification

- `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py` -> `18 passed in 0.06s`.
- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py` -> `10 passed in 0.07s`.
- `pytest -q novaic-llm-factory/tests/test_chat_routes.py novaic-llm-factory/tests/test_log_routes.py` -> `17 passed in 0.21s`.

## Known Gaps

- No test failures. Residual branch classification is handled by sibling P222.

## Artifacts

- Focused pytest command outputs above.
