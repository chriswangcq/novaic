# Runtime ToolOutputV1 normalization result

## Summary

Runtime successful tool execution now stores durable `content` as `ToolOutputV1` JSON. Legacy executor dictionaries are converted into bounded readable `text`, while `tool_success` / `tool_status` semantics continue to come from the original executor result.

## Done

- Updated `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`:
  - added legacy-result text normalization;
  - preserved already-normalized `tool-output.v1` payloads;
  - wrapped `_ok()` durable content in `ToolOutputV1`;
  - preserved logical failure status when executor returns `success=false` or `ok=false`.
- Updated `novaic-agent-runtime/task_queue/contracts/react_actions.py` so repeated logical error detection can read legacy error fields from `ToolOutputV1.text`.
- Updated focused tests for logical failures, repeated scope mismatch, and mounted device tool execution.

## Verification

- `python -m pytest tests/test_pr234_tool_logical_failure.py tests/test_pr234_repeated_scope_mismatch.py tests/unit/task_queue/test_device_tool_handlers.py tests/unit/task_queue/test_tool_handlers_failure_event.py tests/unit/task_queue/test_tool_output_contract.py tests/test_tool_surface_boundary.py -q`
  - Result: `21 passed in 0.07s`.
- `python -m pytest tests/test_runtime_explicit_contracts.py tests/test_pr85_llm_context_smoke_guardrails.py tests/test_pr71_no_tool_retry_context_cleanup.py tests/test_runtime_tool_path_contract.py -q`
  - Result: `32 passed in 0.11s`.
- `cd novaic-cortex && python -m pytest tests/test_tool_output_projection.py tests/test_resolve_for_llm.py tests/test_payload_inspection_api.py -q`
  - Result: `18 passed in 0.18s`.

## Residual Risk

- `_err()` still uses the legacy raw error dictionary envelope. That is a separate failure-path normalization cleanup and should be handled by a follow-up ticket if the final target requires every tool result path, including handler exceptions and unknown tool names, to emit `ToolOutputV1`.
