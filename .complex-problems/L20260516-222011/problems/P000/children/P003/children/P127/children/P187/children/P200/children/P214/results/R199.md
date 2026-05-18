# Projection guard test label audit result

## Summary

Cleaned misleading projection guard test labels. The tests still guard malformed/unsupported image payload shapes, but no longer describe those shapes as legacy contracts to preserve.

## Code Changes

- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
  - Renamed `test_legacy_content_array_is_not_image_projection_contract` to `test_unsupported_content_array_does_not_create_image_projection`.
  - Renamed `test_nested_result_wrapper_is_not_image_projection_contract` to `test_nested_result_wrapper_does_not_create_image_projection`.
  - Replaced `old shape` / `old wrapped shape` fixtures with `unsupported shape` / `unsupported wrapped shape`.
- `novaic-cortex/tests/test_tool_output_projection.py`
  - Replaced `old wrapped shape` fixture text with `unsupported wrapped shape`.

## Verification

- Label residue check:
  - `rg -n "legacy|old shape|old wrapped|is_not_image_projection_contract" novaic-cortex/tests/test_tool_output_projection.py novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py -S || true`
  - Result: no output.
- Runtime guard tests:
  - `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
  - Result: `9 passed in 0.10s`.
- Cortex projection tests:
  - `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py`
  - Result: `18 passed in 0.08s`.

## Residual Risk

None for the touched guard labels. Other tests may still use historical terminology outside the projection guard scope.
