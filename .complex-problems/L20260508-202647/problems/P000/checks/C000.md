# Mounted device tools Runtime fix check

## Summary

The Host Desktop mounted-device tool issue is fixed at the Runtime boundary. Runtime now consumes Business dynamic mounted `hd_*` schemas for LLM context and has executors that route those tools to Device Service.

## Evidence

- `task_queue/device_tools.py` defines the Runtime-owned dynamic device tool boundary and Host Desktop proxy path map.
- `cortex_handlers.py` merges Cortex static schemas with `fetch_mounted_device_tool_schemas(...)`.
- `tool_handlers.py` registers `DYNAMIC_DEVICE_TOOL_NAMES` into `_EXECUTORS`.
- `test_prepare_llm_context_merges_mounted_device_tools` proves `hd_screenshot` becomes LLM-visible while stale `subagent_list` does not.
- `test_hd_tool_execute_routes_through_device_proxy` proves `hd_shell_exec` routes to `/internal/agents/{agent_id}/hd/shell/command`.
- Static Cortex/Common tests still pass, proving Cortex's 17 static tool contract was not polluted.

## Criteria Map

- Dynamic mounted schemas are merged into Runtime LLM context -> covered by `test_prepare_llm_context_merges_mounted_device_tools`.
- `inputSchema` is normalized to `parameters` -> covered by the same test's assertion on LLM function parameters.
- Stale/non-executable Business static names are filtered -> covered by `subagent_list` exclusion.
- `hd_*` execution routes to Device proxy -> covered by `test_hd_tool_execute_routes_through_device_proxy`.
- Static tool contracts remain stable -> covered by Cortex/Common focused tests.

## Execution Map

- T000 -> R000: Implemented Runtime dynamic mounted Host Desktop tool schema merge and executor routing, then ran focused contract tests.

## Stress Test

- Business returns old non-runtime tool names: filtered out unless the name is an explicit Runtime-supported dynamic device tool.
- Business returns `inputSchema`: normalized before LLM assembly to avoid empty parameter schemas.
- LLM calls unmounted Host Desktop tool: Runtime can route it, and Device Service still enforces binding/mounted permission.
- Device Service returns a 4xx/5xx: Runtime surfaces a structured tool failure instead of silently succeeding.
- Cortex static tool list changes: static guardrails still assert the 17-tool Cortex contract separately from dynamic tools.

## Residual Risk

- VM/mobile dynamic device tools are not included in this ticket; they should get their own explicit mapping and executor tests before exposure.
- A live deployed smoke test is still needed after deployment because local services were not running here.

## Result IDs

- R000

## Blocking Gaps

- none
