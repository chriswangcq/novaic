# 施工计划：Runtime 清理 + Subagent 维度 Tool 上下文

基于前期调研，Gateway 和 Tools Server 去除 runtime 概念，统一改为 subagent 维度。RO 不改。

---

## 一、目标

1. **Gateway**：删除 runtime 代理，实现 subagent 维度的 tool-context API
2. **Tools Server**：去除 runtime 概念，全部改为 agent_id + subagent_id
3. **RO**：不改（继续用 runtime_id 内部流转，调用 Tools Server 时传 agent_id + subagent_id）

---

## 二、Tools Server 当前调用 Gateway 的 Runtime API（4 处）

| # | 方法 | 路径 | 调用位置 | 用途 |
|---|------|------|----------|------|
| 1 | GET | `/internal/runtimes/{runtime_id}` | api.py `_lazy_hydrate_runtime` | 懒加载 runtime 上下文 |
| 2 | GET | `/internal/runtimes/{runtime_id}` | executor.py `session_state` | 获取 runtime + subagent 合并信息 |
| 3 | POST | `/internal/runtimes/{runtime_id}/tool-ports` | runtime_manager.py `_persist_tool_ports` | 持久化 tool_ports |
| 4 | GET | `/internal/runtimes/with-tools` | runtime_manager.py `restore_from_gateway` | 启动恢复带 tool_ports 的上下文 |

---

## 三、Phase 1：Gateway 实现 Subagent 维度 API

### 3.1 数据层

- **方案**：在 `subagents` 表新增 `tool_ports` 列（或新建 `subagent_tool_ports` 表）
- **迁移**：v42 新增 `subagents.tool_ports TEXT`（JSON）
- **Repository**：`SubAgentRepository` 增加 `set_tool_ports(agent_id, subagent_id, ports)`、`get_tool_ports(agent_id, subagent_id)`、`list_with_tool_ports()`

### 3.2 新增 API（Gateway internal）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/internal/subagents/{agent_id}/{subagent_id}/tool-context` | 返回 `{agent_id, subagent_id, tool_ports}`，供 Tools Server 懒加载 |
| PATCH | `/internal/subagents/{agent_id}/{subagent_id}/tool-ports` | 持久化 tool_ports，body: `{ports: {...}}` |
| GET | `/internal/subagents/with-tools` | 返回 `{subagents: [{agent_id, subagent_id, tool_ports}, ...]}`，供 Tools Server 启动恢复 |

### 3.3 实现位置

- `novaic-gateway/gateway/api/internal/subagent.py` 或新建 `gateway/api/internal/tool_context.py`

---

## 四、Phase 2：Tools Server 改为 Subagent 维度

### 4.1 RuntimeManager → SubAgentToolContext

| 改动项 | 说明 |
|--------|------|
| 主键 | `runtime_id` → `subagent_key = f"{agent_id}:{subagent_id}"` |
| RuntimeContext | 重命名为 `SubAgentToolContext`，保留 `agent_id`、`subagent_id`、`ports`，`runtime_id` 可选（兼容旧调用） |
| create | `create(agent_id, subagent_id, ports)` |
| get | `get(agent_id, subagent_id)` |
| delete | `delete(agent_id, subagent_id)` |

### 4.2 API 调用 Gateway 的改动

| 原调用 | 新调用 |
|--------|--------|
| `GET gateway/internal/runtimes/{runtime_id}` | `GET gateway/internal/subagents/{agent_id}/{subagent_id}/tool-context` |
| `POST gateway/internal/runtimes/{runtime_id}/tool-ports` | `PATCH gateway/internal/subagents/{agent_id}/{subagent_id}/tool-ports` |
| `GET gateway/internal/runtimes/with-tools` | `GET gateway/internal/subagents/with-tools` |

### 4.3 Tools Server 内部 API（供 RO 调用）

RO 调用 Tools Server 时传 `agent_id` + `subagent_id`，不再传 `runtime_id`：

| 原 API | 新 API |
|--------|--------|
| `POST /internal/runtimes` body: `{runtime_id, agent_id, subagent_id, ports}` | `POST /internal/subagents/{agent_id}/{subagent_id}/tools/register` body: `{ports}` |
| `DELETE /internal/runtimes/{runtime_id}` | `DELETE /internal/subagents/{agent_id}/{subagent_id}/tools` |
| `GET /internal/runtimes/{runtime_id}/tools` | `GET /internal/subagents/{agent_id}/{subagent_id}/tools` |
| `POST /internal/runtimes/{runtime_id}/tools/call` | `POST /internal/subagents/{agent_id}/{subagent_id}/tools/call` |

### 4.4 涉及文件

- `tools_server/api.py`：路由改为 subagent 维度
- `tools_server/runtime_manager.py`：改为 SubAgentToolContextManager
- `tools_server/executor.py`：ToolExecutor 接收 `agent_id`、`subagent_id`，`session_state` 调用新 Gateway API
- `task_queue/handlers/tool_handlers.py`：ctx 传 agent_id、subagent_id
- `task_queue/handlers/llm_handlers.py`：调用 Tools Server 新路径
- `task_queue/sagas/*`：idempotency_key、tool_event_key 改用 `agent_id:subagent_id`

---

## 五、Phase 3：RO 调用 Tools Server 的改动

RO 的 MCP client 调用 Tools Server 时，改为传 `agent_id` + `subagent_id`：

| 原调用 | 新调用 |
|--------|--------|
| `create_runtime_tools(runtime_id, agent_id, subagent_id, ports)` | `create_subagent_tools(agent_id, subagent_id, ports)` → `POST /internal/subagents/{agent_id}/{subagent_id}/tools/register` |
| `destroy_runtime_tools(runtime_id)` | `destroy_subagent_tools(agent_id, subagent_id)` → `DELETE /internal/subagents/{agent_id}/{subagent_id}/tools` |
| `call_runtime_tool(runtime_id, tool_name, args)` | `call_subagent_tool(agent_id, subagent_id, tool_name, args)` → `POST /internal/subagents/{agent_id}/{subagent_id}/tools/call` |
| `list_runtime_tools(runtime_id)` | `list_subagent_tools(agent_id, subagent_id)` → `GET /internal/subagents/{agent_id}/{subagent_id}/tools` |

**涉及**：`novaic-runtime-orchestrator/task_queue/business/mcp.py`、`task_queue/client.py`

**agent-runtime** 同理（若有独立 MCP 调用 Tools Server）。

---

## 六、Phase 4：Gateway 删除 Runtime 代理

在 Phase 1～3 完成后：

1. 删除 `novaic-gateway/gateway/api/internal/runtime.py` 中所有 runtime 代理路由
2. 删除或精简 `helpers.py` 中 `resolve_runtime_ids`、`get_runtime_context`（若无其他引用）
3. 清理 `RuntimeRepository`、`agent_runtimes` 表相关逻辑（可选：保留表结构做兼容，或后续迁移删除）

---

## 七、施工顺序与依赖

```
Phase 1 (Gateway)     →  Phase 2 (Tools Server)  →  Phase 3 (RO)  →  Phase 4 (Gateway 清理)
实现 subagent API         改调用 Gateway + 内部 API    改 MCP client      删除 runtime 代理
```

| 阶段 | 任务 | 预估 |
|------|------|------|
| Phase 1 | Gateway DB 迁移 + 3 个 subagent API | 0.5d |
| Phase 2 | Tools Server 内部改造 + 调用 Gateway 新 API | 1d |
| Phase 3 | RO/agent-runtime MCP client 改调用 | 0.5d |
| Phase 4 | Gateway 删除 runtime 代理 | 0.5d |

---

## 八、回滚与兼容

- Phase 1 可与现有 runtime 代理并存，通过新路径验证
- Phase 2 完成后，旧 Tools Server API 可保留一段时间，RO 逐步切到新 API
- Phase 4 前确认无其他服务调用 Gateway 的 `/internal/runtimes/*`、`/internal/rt/*`

---

## 九、验收标准

1. Tools Server 启动后能通过 `GET /internal/subagents/with-tools` 恢复上下文
2. 工具执行流程：RO → Tools Server（subagent 维度）→ Gateway（tool-context）正常
3. Gateway 不再暴露 `/internal/runtimes/*`、`/internal/rt/*`
4. Tools Server 代码中无 `runtime_id` 作为主键或 API 参数
