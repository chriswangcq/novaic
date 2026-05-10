# SubAgent tool schema cutover result

## Summary

Completed the SubAgent schema cutover: `subagent_spawn` is no longer an LLM-visible builtin schema, and SubAgent creation is available through the `agentctl subagent spawn` shell capability.

## Done

- Added `agentctl subagent spawn --task TEXT`.
- Added `agentctl subagent spawn --task-file PATH`.
- Added `--share-context` and `--timeout-minutes` options.
- Routed shell command to existing Business `/internal/subagents/{agent_id}/spawn` endpoint.
- Removed `subagent_spawn` from canonical LLM-facing builtin schemas and Common active runtime metadata.
- Updated shell description and help text to advertise `agentctl subagent spawn`.
- Added `subagent_spawn` to `SHELL_CAPABILITY_SCHEMA_CUTOVER_TOOLS`.
- Updated Cortex/Common/Runtime guard tests.

## Verification

- `cd novaic-agent-runtime && python -m pytest tests/test_runtime_tool_path_contract.py tests/test_tool_surface_boundary.py tests/unit/task_queue/test_shell_output_contract.py tests/unit/task_queue/test_environment_tool_handlers.py -q`
  - Passed: `31 passed`
- `cd novaic-cortex && python -m pytest tests/test_tool_schemas_limits.py tests/test_shell_capability_runtime.py -q`
  - Passed: `18 passed`
- `cd novaic-common && python -m pytest tests/test_tool_definitions_contract.py tests/test_tool_product_semantics_contract.py tests/test_payload_tool_schemas.py -q`
  - Passed: `11 passed`

## Residual Risk

- Direct `subagent_spawn` executor remains internally available for compatibility and later physical cleanup.
