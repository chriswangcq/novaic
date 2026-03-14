# novaic-runtime-orchestrator Task Queue 使用范围全面梳理

> **已删除**：task_queue 目录及相关调用已于 2025-03 移除。本文档保留分析结论供参考。

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          novaic-app (Tauri 主进程)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  启动的进程：                                                                     │
│  • novaic-runtime-orchestrator (19993)  ← 仅 HTTP 服务，无 Worker                 │
│  • novaic-agent-runtime:                                                         │
│    - queue-service (19997)                                                       │
│    - task-worker × N, saga-worker × N                                            │
│    - watchdog, scheduler                                                          │
│  • novaic-gateway (19999)                                                         │
│  • novaic-tools-server (19998)                                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

调用关系：
  agent-runtime 使用两个 HTTP 客户端：
  • gateway_client (GATEWAY_URL=19999) → /internal/messages*, /internal/chat*, 
    /internal/config*, /internal/subagents*, /internal/agents/* (大部分)
  • ro_client (RUNTIME_ORCHESTRATOR_URL=19993) → /internal/runtimes*, 
    /internal/subagents* (HRL/lock/merge), /internal/agents/* (drive, info, notebook-summary)
```

---

## 二、task_queue 目录结构（已删除）

原 `task_queue/` 目录已移除，包含 client、saga、topics、business、utils 等。

---

## 三、task_queue 在 RO 内的使用位置

### 3.1 直接导入 task_queue 的模块

| 文件 | 导入内容 | 用途 |
|------|----------|------|
| `gateway/api/internal/runtime.py` | `task_queue.utils.multimodal` | 导入但**未使用**（仅注释提及 process_multimodal） |
| `gateway/api/internal/llm.py` | `sanitize_context`, `process_multimodal_messages` | `/internal/debug/llm/call`, `/internal/llm/compact-context` |
| `gateway/api/internal/message.py` | `GatewayInternalClient`, `build_wake_message` | `/internal/messages/inject-wake` |
| `gateway/api/skills.py` | `GatewayInternalClient`, `build_system_prompt`, `build_wake_message` | `/api/agents/{id}/prompts-preview` |

### 3.2 business 层

`task_queue/business/*`（RuntimeBusiness, MessageBusiness, LLMBusiness, SubAgentBusiness, MCPBusiness）**未被 gateway 任何路由导入**，仅在 business 自身和 docstring 中出现。

---

## 四、关键发现：谁调用 RO 的哪些路由？

### 4.1 agent-runtime 的请求路由

agent-runtime 的 `GatewayInternalClient` 按路径分发：

- **gateway_client**（发往 Gateway 19999）：`/internal/messages*`, `/internal/chat*`, `/internal/config*`, `/internal/subagents*`, `/internal/agents/*`（除 drive/info/notebook-summary 等）
- **ro_client**（发往 RO 19993）：`/internal/runtimes*`, `/internal/subagents*`（HRL、lock、merge 等）, `/internal/agents/*`（drive, info, notebook-summary, increment-interaction）

### 4.2 实际调用 RO 的路径

| 路径 | 调用方 | 是否使用 task_queue |
|------|--------|---------------------|
| `/internal/runtimes/*` | agent-runtime ro_client | 否 |
| `/internal/subagents/*` | agent-runtime ro_client | 否 |
| `/internal/agents/*` (drive, info 等) | agent-runtime ro_client | 否 |
| `/internal/messages/*` | **无**（发往 Gateway） | - |
| `/internal/llm/*` | **无**（发往 Gateway） | - |
| `/internal/debug/llm/call` | 前端 gateway_post → Gateway | - |

### 4.3 结论：RO 中使用 task_queue 的路由几乎不被调用

| 路由 | 使用 task_queue | 实际调用方 | 结论 |
|------|-----------------|------------|------|
| `/internal/messages/inject-wake` | GatewayInternalClient, build_wake_message | **无**（scheduler 调 gateway_client → Gateway） | **死代码** |
| `/internal/debug/llm/call` | sanitize_context, process_multimodal_messages | 前端 → **Gateway**（非 RO） | **死代码** |
| `/internal/llm/compact-context` | 同上 | 需确认 | 可能死代码 |
| `/api/agents/{id}/prompts-preview` | build_system_prompt, build_wake_message | **未挂载**（skills 未 include 到 RO app） | **死代码** |

### 4.4 RO 的 app 挂载情况

`main_runtime_orchestrator.py` 仅挂载：

```python
app.include_router(internal_router)  # prefix=/internal
```

`gateway/api/skills.py` 的 router（prefix=/api）**未**被 include，故 `/api/agents/{id}/prompts-preview` 在 RO 中**不存在**。

---

## 五、task_queue 各模块调用情况汇总

| 模块 | 被谁导入 | 是否被实际执行 |
|------|----------|----------------|
| **client.GatewayInternalClient** | message.py, skills.py | 否（对应路由不被调用或未挂载） |
| **utils.system_prompt** | message.py, skills.py | 否 |
| **utils.context** (sanitize, process_multimodal) | llm.py | 否（llm 路由不被 RO 调用） |
| **utils.multimodal** | runtime.py | 否（导入未使用） |
| **business/** | 无 | 否 |
| **client.TaskQueueClient, SagaClient** | 无 | 否（RO 不跑 Worker） |

---

## 六、与其他服务的调用关系

| 服务 | 是否调用 RO | 是否触发 RO 的 task_queue |
|------|-------------|---------------------------|
| **novaic-agent-runtime** | 是（ro_client → /internal/runtimes, subagents, agents） | 否（这些路由不用 task_queue） |
| **novaic-gateway** | 是（client.forward 出站调 RO） | 否 |
| **novaic-tools-server** | 否（用 GATEWAY_URL） | - |
| **novaic-app 前端** | 否（gateway_post → Gateway） | - |

---

## 七、总结

### 7.1 实际被使用的 task_queue 代码

**无。** 在 RO 中，所有使用 task_queue 的代码路径均未被其他服务触发。

### 7.2 原因

1. **路由归属**：`/internal/messages/*`、`/internal/llm/*` 等由 agent-runtime 的 gateway_client 发往 **Gateway**，不经过 RO。
2. **skills 未挂载**：`gateway/api/skills.py` 未 include 到 RO 的 app，`/api/agents/{id}/prompts-preview` 在 RO 中不存在。
3. **前端**：`/internal/debug/llm/call` 通过 gateway_post 发往 **Gateway**，不经过 RO。

### 7.3 已执行清理

1. **已删除**：`task_queue/` 整个目录
2. **已修改**：runtime.py 移除 multimodal 导入；llm.py 移除 preprocess；message.py 使用简单 fallback；skills.py prompts-preview 返回占位
3. **职责**：RO 不再包含 task_queue，实际生效逻辑在 **novaic-gateway** 和 **novaic-agent-runtime** 中。
