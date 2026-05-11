# Step-ref projection repair result

## Summary

Repaired Cortex event projection so tool-result messages carry the top-level `step_ref` required by runtime LLM expansion.

## Done

- Updated `_tool_result_message` to copy non-empty string `payload_ref` to top-level `step_ref`.
- Preserved `_metadata.payload_ref` for diagnostics and existing observability.
- Updated regression tests for ordinary, multiple, and orphan tool results.

## Verification

- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-logicalfs:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-sdk:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-service:/Users/wangchaoqun/new-build-novaic/novaic-common pytest -q tests/test_context_event_projection.py` in `novaic-cortex`: `28 passed`.
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-logicalfs:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-sdk:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-service:/Users/wangchaoqun/new-build-novaic/novaic-common pytest -q tests/test_context_event_read_model.py tests/test_context_event_api_steps_write.py` in `novaic-cortex`: `7 passed`.

## Known Gaps

- None for this projection boundary. The compensation finalize path still needs repair.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/tests/test_context_event_projection.py`
