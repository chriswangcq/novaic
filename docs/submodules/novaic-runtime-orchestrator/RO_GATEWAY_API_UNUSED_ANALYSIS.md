# RO gateway/api 与 novaic-gateway 重叠及未调用分析

> **已清理**：未使用的 internal 模块和 api 根目录文件已于 2025-03 删除。

## 一、RO 实际挂载的路由

RO 的 `main_runtime_orchestrator.py` 仅挂载：

```python
app.include_router(internal_router)  # prefix=/internal
```

即 **仅** `gateway/api/internal/*` 下的路由，前缀 `/internal`。

---

## 二、RO gateway/api 目录结构 vs 挂载情况

| 文件/目录 | 是否挂载 | 说明 |
|-----------|----------|------|
| **internal/** | ✅ 是 | 通过 internal_router 挂载 |
| routes.py | ❌ 否 | 未 include |
| agents.py | ❌ 否 | 未 include |
| vm.py | ❌ 否 | 未 include |
| devices.py | ❌ 否 | 未 include |
| vmcontrol.py | ❌ 否 | 未 include |
| skills.py | ❌ 否 | 未 include |
| chat_service.py | ❌ 否 | 未 include |
| internal_proxy.py | ❌ 否 | 未 include |
| runtime_orchestrator_forward.py | ❌ 否 | 未 include |

**结论**：`routes.py`、`agents.py`、`vm.py`、`devices.py`、`vmcontrol.py`、`skills.py`、`chat_service.py`、`internal_proxy.py`、`runtime_orchestrator_forward.py` 在 RO 中**从未挂载**，属于死代码（从 monolith 拆分遗留）。

---

## 三、internal/* 各模块：Gateway 是否提供 + 是否有人调用 RO

| 模块 | Gateway 是否提供 | 谁调用 | RO 是否被调用 |
|------|------------------|--------|----------------|
| **runtime** | ❌ 不提供 | agent-runtime ro_client | ✅ 是 |
| **subagent** | ✅ 提供 | agent-runtime 分流：gateway_client→Gateway, ro_client→RO | ✅ 是（ro_client 部分） |
| **agent** | ✅ 提供 | Tools Server、agent-runtime→Gateway | ❌ 否（全走 Gateway） |
| **message** | ✅ 提供 | agent-runtime gateway_client→Gateway | ❌ 否 |
| **llm** | ✅ 提供 | 前端 gateway_post→Gateway | ❌ 否 |
| **config** | ✅ 提供 | agent-runtime gateway_client→Gateway | ❌ 否 |
| **task** | ✅ 提供 | Tools Server、storage→Gateway | ❌ 否 |
| **vm** | ✅ 提供 | Tools Server→Gateway | ❌ 否 |
| **web** | ✅ 提供* | Tools Server→Gateway | ❌ 否 |
| **broadcast** | ✅ 提供 | 待确认 | ❌ 否 |
| **health** | ✅ 提供 | 待确认 | ❌ 否 |

\* Gateway 的 `internal_proxy` 未 include `web_router`，但 `gateway.api.internal` 中有 web 模块；若 Gateway 未单独挂载 web，则可能 404。

---

## 四、调用方与目标服务

| 调用方 | 目标 | 使用的 internal 路径 |
|--------|------|----------------------|
| **agent-runtime ro_client** | RO (19993) | /internal/runtimes/*, /internal/subagents/* (get/status/main/due-wake/hrl/lock/merge), /internal/agents/* (drive/info/notebook-summary) |
| **agent-runtime gateway_client** | Gateway (19999) | /internal/messages/*, /internal/chat/*, /internal/config/*, /internal/subagents/* (awake/sleeping/completed/check-and-clear) |
| **Gateway forward()** | RO | /internal/runtimes/latest, cancel-by-subagent, delete-by-subagent |
| **Tools Server** | Gateway | /internal/agents/*, /internal/web/*, /internal/subagents/*/tools 等 |
| **前端** | Gateway | /internal/debug/llm/call 等 |

---

## 五、RO 中实际被调用的 internal 模块

| 模块 | 被调用的路由 | 调用方 |
|------|--------------|--------|
| **runtime.py** | /runtimes/*（全部） | ro_client, Gateway forward |
| **subagent.py** | /subagents/due-wake, /subagents/{id}/main, /subagents/{id}/{sid}, /subagents/.../hrl, summary-lock, merge-history, /agents/{id}/drive, notebook-summary, info, increment-interaction | ro_client |

---

## 六、RO 中未被调用的 internal 模块（Gateway 已提供，无人调 RO）

| 模块 | 路由 | 说明 |
|------|------|------|
| **agent.py** | /agents/setup-complete, /agents/{id}/awake, /agents/{id}/sleep, /agents/{id}, /agents/{id}/memory/all, /agents/{id}/subagent/*, /agents/{id}/subagent/report | Tools Server、agent-runtime 均走 Gateway |
| **message.py** | /messages/*, /chat/*, /agents/{id}/interrupt | gateway_client→Gateway |
| **llm.py** | /debug/llm/call, /llm/compact-context | 前端→Gateway |
| **config.py** | /config/* | gateway_client→Gateway |
| **task.py** | /tasks/* | Tools Server、storage→Gateway |
| **vm.py** | /vm/*, /runtimes/{id}/vm-tools | Tools Server→Gateway |
| **web.py** | /web/search, /web/fetch | Tools Server→Gateway |
| **broadcast.py** | /broadcast/* | 待确认 |
| **health.py** | /health/stuck-sending | 待确认 |

---

## 七、总结

### 7.1 有人调用的 RO 代码（需保留）

- **runtime.py**：全部
- **subagent.py**：与 runtimes、HRL、summary-lock、merge、agents/drive 等相关的路由

### 7.2 已删除（Gateway 已提供）

- agent.py, message.py, llm.py, config.py, task.py, vm.py, web.py, broadcast.py, health.py

### 7.3 已删除（从未挂载）

- routes.py, agents.py, vm.py, devices.py, vmcontrol.py, skills.py, chat_service.py, internal_proxy.py, runtime_orchestrator_forward.py

### 7.4 数量估算

- **internal 中未使用**：约 9 个模块（agent, message, llm, config, task, vm, web, broadcast, health）
- **api 根目录未挂载**：约 9 个文件
- **合计**：约 18 个模块/文件在 RO 中未被使用，且多数在 novaic-gateway 中已有实现。
