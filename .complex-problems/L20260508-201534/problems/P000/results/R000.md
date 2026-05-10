# Device tool mount diagnosis result

## Summary

Diagnosed why 小马 does not currently see mounted device tools in the LLM tool surface. The binding/design path exists, but the actual Runtime LLM assembly path is still static: Runtime loads tool schemas only from Cortex, Cortex returns `common.tools.llm_builtin.AGENT_BUILTIN_TOOL_SCHEMAS`, and Runtime executors do not include `hd_*` device tool handlers.

## Done

- Confirmed the intended dynamic source exists in `novaic-business/business/internal/agent.py`: `_filter_builtin_tools_for_agent()` fetches device binding/mounted tools and adds `HD_TOOLS` when `device_type == "host_desktop"`.
- Confirmed the host desktop mount map exists in `novaic-device/device/agent_binding.py`: `hd_screenshot`, `hd_mouse`, `hd_keyboard`, `hd_shell_exec`, `hd_clipboard_get`, `hd_clipboard_set`, `hd_file_pull`, and `hd_file_push`.
- Confirmed the actual LLM context assembly path does not call the Business dynamic tool endpoint:
  - `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py:331` calls `bridge.load_tool_schemas(...)`.
  - `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:630` posts only to Cortex `/v1/internal/tools`.
  - `novaic-cortex/novaic_cortex/api.py:1737` returns `tool_schemas_for_subagent(...)`.
  - `novaic-cortex/novaic_cortex/tool_schemas.py:22` delegates to `agent_tool_schemas_for_subagent(...)` from `common.tools.llm_builtin`.
- Confirmed Runtime execution is also not wired for device tools: `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:525` `_EXECUTORS` contains runtime/Cortex/environment/payload tools but no `hd_*`.
- Confirmed current tests encode the old static assumption:
  - `novaic-agent-runtime/tests/test_runtime_tool_path_contract.py:78` asserts static schema names exactly equal executor names.
  - `novaic-cortex/tests/test_tool_schemas_limits.py:14` hard-codes the static 17 Cortex tools.
- Identified a schema-shape mismatch for future integration: Business returns device tools as `{name, description, inputSchema}`, while `common/contracts/llm_assembly.py:142` expects raw schemas with `parameters`.
- Attempted to re-check local production DB/service state, but this environment has no `/opt/novaic` and local Business port `19998` refused connections. Current result therefore uses source-code evidence plus prior production observations, not a live local DB replay.

## Verification

- Ran targeted source inspections with `rg` and `nl -ba` across `novaic-agent-runtime`, `novaic-cortex`, `novaic-business`, `novaic-common`, and `novaic-device`.
- Attempted local runtime evidence collection:
  - `/opt/novaic/data/entangled.db` was unavailable in this workspace.
  - `/opt/novaic/data/queue.db` was unavailable in this workspace.
  - `http://127.0.0.1:19998/internal/agents/.../builtin-tools` refused connection.
- Verified that the observed source path alone is sufficient to explain the missing mounted tools: no code path merges Business dynamic device tools into `raw_tool_schemas`, and no executor exists for device tool names.

## Known Gaps

- This ticket is diagnostic only; it does not implement the fix.
- Live production DB/service verification could not be repeated in the current Codex environment because `/opt/novaic` and local services are absent.

## Artifacts

- `.complex-problems/L20260508-201534/problems/P000/README.md`
- `.complex-problems/L20260508-201534/problems/P000/tickets/T000.md`
- Source pointers listed in this result.
