# Runtime ToolOutputV1 error path result

## Summary

Normalized Runtime `_err()` durable `content` to `ToolOutputV1` so unknown-tool and handler-exception paths no longer write raw legacy error JSON.

## Done

- Updated `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`:
  - `_err()` now serializes `tool_error(str(error)).to_dict()` into `content`;
  - top-level `error`, `success=false`, and `status=error` semantics remain unchanged.
- Updated `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_failure_event.py`:
  - executor exception path asserts `tool-output.v1`, `ok=false`, and preserved error text;
  - unknown tool path asserts the same envelope shape.

## Verification

- `python -m pytest tests/unit/task_queue/test_tool_handlers_failure_event.py tests/test_pr234_tool_logical_failure.py tests/test_pr234_repeated_scope_mismatch.py tests/unit/task_queue/test_device_tool_handlers.py tests/unit/task_queue/test_tool_output_contract.py tests/test_tool_surface_boundary.py -q`
  - Result: `22 passed in 0.07s`.
- `python -m pytest tests/test_runtime_explicit_contracts.py tests/test_pr85_llm_context_smoke_guardrails.py tests/test_pr71_no_tool_retry_context_cleanup.py tests/test_runtime_tool_path_contract.py -q`
  - Result: `32 passed in 0.11s`.
- `cd novaic-cortex && python -m pytest tests/test_tool_output_projection.py tests/test_resolve_for_llm.py tests/test_payload_inspection_api.py -q`
  - Result: `18 passed in 0.21s`.

## Residual Risk

- Direct LLM tool surface still includes migration tools until later shell-capability cutover phases. This ticket only closes Runtime durable output normalization.
