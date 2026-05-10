# Shell output contract normalization success check

## Result IDs

- R000

## Evidence

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` contains shell-specific conversion from Cortex shell result to `ToolOutputV1`.
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py` covers success, nonzero exit, and large stdout behavior.
- Focused and adjacent tests passed:
  - `8 passed`
  - `25 passed`

## Criteria Map

- Explicit shell normalization: satisfied by `_exec_shell` returning `_shell_result_output(...)`.
- Concise bounded shell summary: satisfied by `exit_code`, stdout/stderr previews, and changed file preview in `text`.
- Full raw result preserved: satisfied by `diagnostics.raw_shell_result`.
- Nonzero exit maps to logical error: satisfied by `ok=false`, `tool_success=false`, and `tool_status=error` test.
- Tests cover success/nonzero/large output: satisfied by new unit tests.

## Execution Map

- Implemented helper functions for shell stream preview and envelope creation.
- Kept legacy wrapping only for non-shell executor returns.
- Verified no regressions in repeated-scope/logical-failure/device-tool handler tests.

## Stress Test

- The large stdout test uses 10,000 characters, verifies prompt text is bounded, verifies stream truncation metadata, and verifies raw stdout remains recoverable in diagnostics.

## Residual Risk

- Moving massive raw shell streams from JSON diagnostics into external artifacts is a potential future optimization, not required for the current contract closure.
