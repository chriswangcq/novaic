# common.http.clients and mcp_client Usage Analysis

Analysis of `common.http.clients` (internal_client, internal_async_client, external_async_client) and `mcp_client` usage in **novaic-tools-server** and **novaic-agent-runtime**, with reachability from main entry points.

---

## 1. novaic-tools-server: common.http.clients

**Entry:** `main_tools.py` → FastAPI app with `router` + `internal_router` from `tools_server.api`

| File | Import | Call Chain | Reachable from Entry? | Conclusion |
|------|--------|------------|------------------------|------------|
| `tools_server/executor.py` | `internal_async_client` | main_tools → api (router) → `call_subagent_tool` → `_execute_tool_for_context` → `ToolExecutor.execute` → `_execute_builtin` → `_get_http_client()` | Yes | **LIVE** |
| `tools_server/trs.py` | `internal_client` | main_tools → api → `call_subagent_tool` → `_execute_tool_for_context` → `push_tool_result_to_trs` | Yes | **LIVE** |
| `tools_server/api.py` | `internal_client` | main_tools → api → `_get_tools_for_context` (GET `/internal/subagents/{agent_id}/{subagent_id}/tools`) | Yes | **LIVE** |
| `tools_server/tool_context_manager.py` | `internal_client`, `internal_async_client` | main_tools lifespan → `init_tool_context_manager`, `restore_from_gateway`; api routes → `create`, `persist`, `restore` | Yes | **LIVE** |
| `tools_server/tool_result_adapter.py` | `internal_async_client` | main_tools → api → executor → `_adapt_tool_result` | Yes | **LIVE** |
| `mcp_client/mcp_client.py` | `external_async_client` | main_tools → api → tool_context_manager → `ToolRegistry.discover_all_tools` → `MCPClient` (discovery) | Yes | **LIVE** |

**Summary:** All `common.http.clients` usages in novaic-tools-server are reachable from `main_tools.py` via mounted routes or lifespan.

---

## 2. novaic-agent-runtime: common.http.clients

**Entries:** `main_novaic.py`, `main_task.py`, `main_saga.py`, `queue_service/main.py`

| File | Import | Call Chain | Reachable from Entry? | Conclusion |
|------|--------|------------|------------------------|------------|
| `task_queue/client.py` | `internal_client` (from `common.http`) | main_novaic/main_task → `TaskWorkerSync`; main_saga → `SagaWorkerSync`; run_health → `HealthWorkerSync`; run_watchdog → `WatchdogSync`; run_scheduler → `SchedulerWorkerSync`; `TaskQueueClient`, `GatewayBusinessClient`, `RuntimeOrchestratorClient`, `SagaClient` all use it | Yes | **LIVE** |
| `task_queue/business/mcp.py` | `internal_client` | main_novaic/main_task → `TaskWorkerSync` → `handle_mcp_create` / `handle_mcp_destroy` → `MCPBusiness` | Yes | **LIVE** |
| `task_queue/handlers/llm_handlers.py` | `internal_client` | main_novaic/main_task → `TaskWorkerSync` → `handle_llm_*` | Yes | **LIVE** |
| `task_queue/handlers/summary_handlers.py` | `internal_client` | main_novaic/main_task → `TaskWorkerSync` → `handle_summary_*` | Yes | **LIVE** |
| `task_queue/workers/health_worker_sync.py` | `internal_client` | main_novaic run_health → `HealthWorkerSync` | Yes | **LIVE** |
| `task_queue/utils/trs_sdk.py` | `internal_client` | main_novaic/main_saga → `SagaWorkerSync` → `react_actions` saga → `get_trs_client().create_from_raw` | Yes | **LIVE** |

**queue_service:** Does **not** use `common.http.clients`. Uses `common.db` and local queue/saga logic only.

**Summary:** All `common.http.clients` usages in novaic-agent-runtime are reachable from main entries (main_novaic, main_task, main_saga, health worker).

---

## 3. mcp_client in novaic-tools-server

| Module | Usage | Invoked by Live Requests? | Conclusion |
|--------|-------|---------------------------|------------|
| `tools_server/executor.py` | `MCPServerConnection` type, `external_mcp_client` param | API creates `ToolExecutor(context, manager)` without `external_mcp_client`; external tool calls return "MCP client not configured". Import used for type hint only | **LIVE** (import/type) but external MCP execution path **DEAD** for API |
| `tools_server/tool_context_manager.py` | `ToolRegistry` (uses `MCPClient`) | `register_subagent_tools` → `start_discovery` → `_discover_tools` → `ToolRegistry.discover_all_tools` → `MCPClient` | **LIVE** |
| `tools_server/api.py` | Path `mcp_client/skills/` | `_get_skills_directory()` returns `Path(__file__).parent.parent / "mcp_client" / "skills"`; filesystem path only, no Python import | N/A (path only) |

**Summary:** `mcp_client` is used for MCP tool discovery via `ToolRegistry` in `tool_context_manager`. Executor’s `external_mcp_client` path is not used by the API (no client passed).

---

## 4. Skills in novaic-tools-server (mcp_client/skills)

| Route | Mounted? | Handler |
|-------|-----------|---------|
| `GET /internal/subagents/{agent_id}/{subagent_id}/skills` | Yes | `get_subagent_skills` → `_list_skills()` |
| `GET /internal/subagents/{agent_id}/{subagent_id}/skills/{skill_name}` | Yes | `get_subagent_skill` → `_get_skill_content(skill_name)` |

**Mounting:** Both routes are on `internal_router` (prefix `/internal`), which is included in `main_tools.py` via `app.include_router(internal_router)`.

**Skills source:** `_list_skills()` reads from `mcp_client/skills/` (filesystem). Each subdirectory with `SKILL.md` is listed. No `mcp_client` Python module import for skills.

**Conclusion:** Skills routes are mounted and live.

---

## Summary Table (per-import)

| Repo | File | Import | Reachable? | Conclusion |
|------|------|--------|------------|------------|
| tools-server | executor.py | internal_async_client | Yes | LIVE |
| tools-server | trs.py | internal_client | Yes | LIVE |
| tools-server | api.py | internal_client | Yes | LIVE |
| tools-server | tool_context_manager.py | internal_client, internal_async_client | Yes | LIVE |
| tools-server | tool_result_adapter.py | internal_async_client | Yes | LIVE |
| tools-server | mcp_client/mcp_client.py | external_async_client | Yes | LIVE |
| agent-runtime | task_queue/client.py | internal_client | Yes | LIVE |
| agent-runtime | task_queue/business/mcp.py | internal_client | Yes | LIVE |
| agent-runtime | task_queue/handlers/llm_handlers.py | internal_client | Yes | LIVE |
| agent-runtime | task_queue/handlers/summary_handlers.py | internal_client | Yes | LIVE |
| agent-runtime | task_queue/workers/health_worker_sync.py | internal_client | Yes | LIVE |
| agent-runtime | task_queue/utils/trs_sdk.py | internal_client | Yes | LIVE |

**No DEAD code paths found** for `common.http.clients` in either repo. All imports are reachable from main entries or mounted routes.
