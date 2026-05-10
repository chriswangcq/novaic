# Device tool mount diagnosis check

## Summary

The diagnostic problem is solved. The root cause is not that 小马 lacks a device binding; it is that the actual Runtime/Cortex LLM tool assembly path ignores the Business dynamic mounted-device tool endpoint, and Runtime lacks executors for `hd_*` tools.

## Evidence

- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py:331` loads `raw_tool_schemas` only through `bridge.load_tool_schemas(...)`.
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:630` sends that request only to Cortex `/v1/internal/tools`.
- `novaic-cortex/novaic_cortex/api.py:1737` returns `tool_schemas_for_subagent(...)`.
- `novaic-cortex/novaic_cortex/tool_schemas.py:22` returns static schemas from `common.tools.llm_builtin`.
- `novaic-business/business/internal/agent.py:232` has the dynamic mounted-tool calculation, including `HD_TOOLS` at lines 311-318, but this endpoint is not in the Runtime LLM assembly path.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:525` does not register any `hd_*` executors.
- `novaic-common/common/contracts/llm_assembly.py:142` expects `parameters`, while the Business endpoint returns `inputSchema`, so dynamic tools require normalization before merge.

## Criteria Map

- Identify whether the binding path exists -> Evidence from Business `_filter_builtin_tools_for_agent()` and Device `hd_*` mount mapping.
- Identify why 小马 does not see mounted device tools -> Evidence from Runtime/Cortex static schema chain.
- Identify whether execution would work if tools were exposed -> Evidence from Runtime `_EXECUTORS` missing `hd_*`.
- Avoid unverified live-state claims -> Current environment unavailability is explicitly recorded.

## Execution Map

- T000 -> R000: Performed source-level and environment-level diagnosis, recorded the broken assembly/executor boundary, and documented the current verification limits.

## Stress Test

- Failure mode: Device binding exists but LLM still sees no tools. Explanation holds because Runtime does not consume Business dynamic tools.
- Failure mode: Business correctly returns `hd_*`, but execution fails. Explanation holds because `_EXECUTORS` has no `hd_*` route.
- Failure mode: A quick fix adds `hd_*` to Cortex static schemas. This would violate the current static 17-tool contract and still lack execution routing; it is not the right fix.
- Failure mode: Dynamic tools are blindly merged. This would drop parameters because Business uses `inputSchema`; the integration must normalize `inputSchema -> parameters`.

## Residual Risk

- Live production DB/service state was not re-verified in the current workspace because `/opt/novaic` and local services are absent. This does not weaken the code-path diagnosis, but it means the exact current deployed binding row should be rechecked in the deployment environment before patch rollout.
- The fix should be done as a separate implementation ticket: Runtime should fetch and normalize Business dynamic device tools, merge only device tool schemas, and route device tool execution through the Device proxy.

## Result IDs

- R000

## Blocking Gaps

- none
