# Shell output contract normalized

## Summary

Runtime shell execution now returns a deliberate `ToolOutputV1` envelope instead of relying on generic legacy dict wrapping.

## Done

- Added shell-specific result preview helpers in `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`.
- `_exec_shell` now returns `tool-output.v1` directly.
- Prompt-facing shell text includes:
  - `exit_code`
  - bounded stdout preview
  - bounded stderr preview
  - changed file list preview
- Full raw shell result is preserved under `diagnostics.raw_shell_result`.
- Nonzero shell exit codes now set `ok=false`, which makes Runtime mark `tool_status=error`.
- Added `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`.

## Verification

- Ran `python -m pytest tests/unit/task_queue/test_shell_output_contract.py tests/test_pr234_tool_logical_failure.py tests/unit/task_queue/test_tool_handlers_failure_event.py -q`.
- Result: `8 passed`.
- Ran `python -m pytest tests/unit/task_queue/test_shell_output_contract.py tests/test_pr71_no_tool_retry_context_cleanup.py tests/test_pr234_repeated_scope_mismatch.py tests/test_pr234_tool_logical_failure.py tests/unit/task_queue/test_tool_handlers_failure_event.py tests/unit/task_queue/test_device_tool_handlers.py -q`.
- Result: `25 passed`.

## Residual Risk

- Diagnostics intentionally preserve raw stdout/stderr, so very large shell payloads still live in durable step content. That is acceptable for recovery, but a later artifact/blob cutover can move massive raw streams out of the JSON envelope if needed.
