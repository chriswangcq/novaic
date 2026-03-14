# RO gateway/api/internal API 调用验证

> 验证 `novaic-runtime-orchestrator/gateway/api/internal/` 提供的 API 是否被实际调用。

---

## 一、结论：**有被调用**

RO 的 internal API 由 **agent-runtime** 的 `ro_client` 和 **Gateway** 的 `client.forward()` 调用，目标为 RO 服务（默认 19993）。

---

## 二、调用方与路由

### 2.1 agent-runtime → RO（ro_client 直连）

`RuntimeOrchestratorClient` 使用 `RUNTIME_ORCHESTRATOR_URL`（RO 地址），直接请求 RO。

| 调用位置 | ro_client 方法 | RO 路由 |
|----------|----------------|---------|
| runtime_business | get_subagent_runtime, create_runtime, set_runtime_status, advance_round, get_runtime, set_runtime_summarized, set_runtime_need_rest | /internal/runtimes/* |
| message_business | append_context, get_runtime, get_subagent_runtime | /internal/runtimes/*, /internal/subagents/* |
| message_handlers | get_subagent_status, get_or_create_runtime | /internal/subagents/*, /internal/runtimes/* |
| summary_handlers | acquire_summary_lock, get_hrl, get_runtime, get_subagent, atomic_merge_history, release_summary_lock, add_to_hrl, get_summary_lock | /internal/subagents/* |
| subagent business | get_subagent, get_subagent_status | /internal/subagents/* |
| mcp business | get_runtime, update_runtime | /internal/runtimes/* |
| llm business | get_runtime, update_runtime, set_runtime_hot_cold_summary | /internal/runtimes/* |
| context_handlers | get_runtime, append_context | /internal/runtimes/* |
| runtime_handlers | update_runtime, get_runtime | /internal/runtimes/* |
| tool_handlers | get_runtime | /internal/runtimes/* |
| llm_handlers | get_runtime | /internal/runtimes/* |
| system_prompt | get_agent_info, get_agent_drive, get_agent_state, get_main_subagent | /internal/agents/*, /internal/subagents/* |
| watchdog | increment_drive_interaction | /internal/agents/* |

### 2.2 Gateway → RO（client.forward）

Gateway 作为客户端调用 RO：

| 场景 | 路径 |
|------|------|
| spawn/status/cancel 解析 runtime_id | GET /internal/runtimes/latest/{agent_id}/{subagent_id} |
| 取消 subagent | POST /internal/runtimes/cancel-by-subagent |
| 删除 subagent | POST /internal/runtimes/delete-by-subagent |

---

## 三、路由分发说明

**GatewayInternalClient._request** 按路径分发：

- `/internal/subagents*` → **gateway_client**（Gateway 19999）
- `/internal/runtimes*` → **ro_client**（RO 19993）
- `/internal/agents/drive`、`/info`、`/notebook-summary`、`/drive/increment-interaction` → **ro_client**（RO）

业务代码中直接使用 `ro_client.xxx()` 时，会绕过 `_request`，直接打到 RO。

---

## 四、RO 当前保留路由与调用对应

| RO 路由 | 调用方 |
|---------|--------|
| POST /runtimes/batch | ro_client.get_runtimes_by_ids |
| POST /runtimes/cancel-by-subagent | Gateway forward |
| POST /runtimes/delete-by-subagent | Gateway forward |
| GET /runtimes/{id} | ro_client.get_runtime |
| POST /runtimes | ro_client.create_runtime |
| POST /runtimes/get-or-create | ro_client.get_or_create_runtime |
| PATCH /runtimes/{id} | ro_client.update_runtime |
| POST /runtimes/{id}/advance | ro_client.advance_round |
| POST /runtimes/{id}/context/append | ro_client.append_context |
| POST /runtimes/{id}/set-status | ro_client.set_runtime_status |
| POST /runtimes/{id}/summarized | ro_client.set_runtime_summarized |
| POST /runtimes/{id}/hot-cold-summary | ro_client.set_runtime_hot_cold_summary |
| POST /runtimes/{id}/need-rest | ro_client.set_runtime_need_rest |
| GET /runtimes/subagent/{agent_id}/{subagent_id} | ro_client.get_subagent_runtime |
| GET /runtimes/latest/{agent_id}/{subagent_id} | Gateway forward |
| GET /subagents/{agent_id}/main | ro_client.get_main_subagent |
| GET /subagents/{agent_id}/{subagent_id} | ro_client.get_subagent |
| GET /subagents/{agent_id}/{subagent_id}/status | ro_client.get_subagent_status |
| GET/POST .../hrl, .../summary-lock/*, .../merge-history | ro_client |
| GET /agents/{agent_id}/drive | ro_client.get_agent_drive |
| GET /agents/{agent_id}/notebook-summary | ro_client.get_notebook_summary |
| POST /agents/{agent_id}/drive/increment-interaction | ro_client.increment_drive_interaction |
| GET /agents/{agent_id}/info | ro_client.get_agent_info |

---

## 五、总结

RO 的 `gateway/api/internal/` 提供的 API **有被实际调用**，主要来自：

1. **agent-runtime**：task_queue 中的 business、handlers、workers 通过 `ro_client` 调用 RO
2. **Gateway**：spawn、cancel、delete 等流程通过 `client.forward()` 调用 RO
