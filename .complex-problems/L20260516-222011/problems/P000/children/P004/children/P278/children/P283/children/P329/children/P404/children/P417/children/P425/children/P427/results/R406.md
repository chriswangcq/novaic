# Result: P427 / T414 ContextEvent projection and guard verification

## Summary

Re-ran focused ContextEvent projection tests and guards. The projection boundary remains clean: history/current tool-result projections do not enable display expansion, and the previous dangerous `stable_json(observation)` fallback is absent.

## Verification

- Focused test command:
  - `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_context_event_projection.py tests/test_context_event_read_model.py tests/test_context_event_read_source_guards.py tests/test_tool_output_projection.py tests/test_workspace.py tests/test_payload_inspection_api.py tests/test_step_result_projection.py tests/test_context_event_api_lifecycle.py tests/test_context_event_api_steps_write.py`
- Result: `90 passed in 0.49s`

## Guard Results

- `stable_json(observation)` fallback guard: no hits.
- `include_display=True` guard:
  - history formatter uses `include_display=False`
  - current tool result formatter uses `include_display=False`
  - only display perception formatter uses `include_display=True`
- Image/base64 suspicious projection guard:
  - data/base64 handling remains inside `step_result_projection.py`
  - display expansion is gated by the formatter-level `include_display` flag

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p427/focused-pytest.with-status.txt`
- `.complex-problems/L20260516-222011/tmp/p427/projection-guards.txt`
- `.complex-problems/L20260516-222011/tmp/p427/step-result-projection-formatters.txt`
- `.complex-problems/L20260516-222011/tmp/p427/step-result-display-conversion.txt`
- `.complex-problems/L20260516-222011/tmp/p427/step-result-format-mcp-content.txt`

## Conclusion

No P427 regression candidate was found. No code change was required for this verification ticket.
