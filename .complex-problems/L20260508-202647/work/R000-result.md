# Mounted device tools Runtime fix result

## Summary

Implemented the Host Desktop mounted-device tool path in Runtime. Runtime now merges Business-resolved mounted `hd_*` schemas into LLM context and can execute those `hd_*` tools through Device Service proxy routes.

## Done

- Added `task_queue/device_tools.py` as the explicit Runtime boundary for mounted device tools.
- Added schema normalization from Business `inputSchema` to LLM assembly `parameters`.
- Filtered dynamic tools to Runtime-executable Host Desktop names only, preventing stale Business static tools from leaking into LLM context.
- Updated `cortex.prepare_llm_context` to merge Cortex static schemas with Business dynamic mounted device schemas.
- Added Runtime execution support for all Host Desktop tools:
  - `hd_screenshot`
  - `hd_mouse`
  - `hd_keyboard`
  - `hd_shell_exec`
  - `hd_clipboard_get`
  - `hd_clipboard_set`
  - `hd_file_pull`
  - `hd_file_push`
- Routed Host Desktop tools to Device Service `/internal/agents/{agent_id}/hd/...` proxy paths.
- Updated static tool contract tests to distinguish static Runtime tools from dynamic mounted device executors.
- Added tests for dynamic schema merge, stale tool filtering, `inputSchema` normalization, successful HD proxy routing, and HTTP error surfacing.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common pytest -q novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py novaic-agent-runtime/tests/test_runtime_tool_path_contract.py novaic-agent-runtime/tests/unit/task_queue/test_device_tool_handlers.py`
  - 17 passed
- `PYTHONPATH=novaic-cortex:novaic-common pytest -q novaic-cortex/tests/test_tool_schemas_limits.py`
  - 10 passed
- `PYTHONPATH=novaic-common pytest -q novaic-common/tests/test_tool_definitions_contract.py novaic-common/tests/test_tool_product_semantics_contract.py`
  - 10 passed

## Known Gaps

- This fixes Host Desktop (`hd_*`) mounted device tools, which is 小马's active device category. VM/mobile dynamic tool execution remains intentionally out of scope for this ticket.
- Live deployment smoke was not run in this turn because the local Codex workspace has no running `/opt/novaic` service set.

## Artifacts

- `novaic-agent-runtime/task_queue/device_tools.py`
- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- `novaic-agent-runtime/tests/test_runtime_tool_path_contract.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_device_tool_handlers.py`
