# Shell projection bounded terminal text result

## Summary

Audited shell projection across runtime wrapper and Cortex formatted projection. Shell output is publicized as terminal-style `tool-output.v1` text with bounded stdout/stderr previews and diagnostics, while the full raw shell result is kept only in durable step payload. Cortex projection formats `tool-output.v1` as text and applies its own LLM budget truncation.

## Done

- Mapped runtime shell output creation:
  - `_preview_shell_stream`
  - `_shell_result_text`
  - `_shell_result_output`
  - `_execute_shell`
- Mapped Cortex formatted projection:
  - `parse_tool_result`
  - `_parse_tool_output_v1`
  - `_format_mcp_content`
  - `format_for_history_llm`
  - `format_for_current_tool_result_llm`
- Confirmed public shell content includes terminal text plus diagnostics, not raw nested shell result.
- Confirmed durable payload keeps raw stdout/stderr for later step/payload inspection.

## Verification

- Runtime shell/tool contract tests passed:

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py \
  novaic-agent-runtime/tests/test_runtime_explicit_contracts.py
```

Result: `26 passed in 0.13s`.

- Cortex projection tests passed:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_tool_output_projection.py
```

Result: `8 passed in 0.05s`.

## Known Gaps

- No shell projection gap found.
- Display/media projection is intentionally handled by sibling P185/P186.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py`
- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
