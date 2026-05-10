# Remove include_display From Step Formatting Projection API Result

## Summary

Removed `include_display` from the Cortex/runtime step formatting request path. Step formatting now uses explicit `projection` values only, with unsupported projections rejected by Cortex.

## Done

- Removed `include_display` from `StepFormattedRequest`.
- Removed the `/v1/steps/read_formatted` boolean display/history fallback branch.
- Added explicit HTTP 400 rejection for unsupported projection values.
- Removed `include_display` parameter and payload field from `CortexBridge.read_step_formatted`.
- Removed `include_display` arguments from `expand_step_ref_to_content`, `fetch_step_for_llm`, and `expand_messages_for_llm`.
- Updated runtime tests to assert projection-only payloads.
- Added Cortex API test proving unknown/empty projection values are rejected.

## Verification

- Static path search:
  - `rg -n "include_display" novaic-cortex/novaic_cortex/api.py novaic-agent-runtime/task_queue/utils/cortex_bridge.py novaic-agent-runtime/task_queue/utils/step_result_client.py novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py -S`
  - Result: no matches.
- Workspace search:
  - `rg -n "include_display" novaic-cortex novaic-agent-runtime novaic-business novaic-common novaic-logicalfs novaic-sandbox-service novaic-sandbox-sdk -S`
  - Result: remaining hits are only `step_result_projection` internal formatting/`resolve_for_llm` byte-resolution behavior and its test.
- Cortex targeted tests:
  - `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_step_result_projection.py novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_context_event_no_compat.py`
  - Result: `17 passed in 0.36s`.
- Runtime targeted tests:
  - `PYTHONPATH="novaic-agent-runtime:novaic-common" python3 -m pytest -q novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
  - Result: `11 passed in 0.10s`.
- Compile check:
  - `python3 -m py_compile novaic-cortex/novaic_cortex/api.py novaic-agent-runtime/task_queue/utils/cortex_bridge.py novaic-agent-runtime/task_queue/utils/step_result_client.py`
  - Result: passed.

## Known Gaps

- None for the step formatting `include_display` cleanup. Final parent gates still need to rerun their own static/targeted checks.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
