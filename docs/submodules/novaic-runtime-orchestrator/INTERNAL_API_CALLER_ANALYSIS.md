# gateway.api.internal 调用方调研报告

## 一、问题

> gateway.api.internal 这些是不是全都应该废弃了？因为没人调用且 novaic-gateway 提供了 API。

## 二、结论摘要

**不应废弃。** novaic-runtime-orchestrator 的 `gateway.api.internal` 是 RO 的核心 HTTP 服务，被 **novaic-agent-runtime** 直接调用，与 novaic-gateway 的 internal API 职责不同、互不替代。

---

## 三、架构与职责划分

### 3.1 两个独立的 internal API 服务

| 服务 | 端口 | 路由入口 | 职责 |
|------|------|----------|------|
| **novaic-gateway** | 19999 | `gateway.api.internal_proxy` | Agent/SubAgent 元数据、消息队列、配置、VM、任务等 |
| **novaic-runtime-orchestrator** | 19993 | `gateway.api.internal` | Runtime 状态、SubAgent 运行时、消息认领、LLM、上下文等 |

### 3.2 路由对比

| 模块 | novaic-gateway | novaic-runtime-orchestrator |
|------|----------------|----------------------------|
| runtime | ❌ 已移除 | ✅ 完整 |
| subagent | ✅ 元数据/CRUD | ✅ 运行时状态 |
| message | ✅ 队列/发送 | ✅ claim/prepare/confirm |
| agent | ✅ 元数据 | ✅ info/drive/notebook |
| llm | ✅ | ✅ |
| config | ✅ | ✅ |
| vm, task, web, broadcast, health, self_drive | 部分 | 部分 |

Gateway 的 internal_proxy 明确说明：`runtime_router removed`，`/internal/runtimes/*` 由 RO 独占。

---

## 四、调用方分析

### 4.1 谁调用 RO 的 /internal/*（19993）？

| 调用方 | 方式 | 说明 |
|--------|------|------|
| **novaic-agent-runtime TaskWorker** | `ro_client = RuntimeOrchestratorClient(RUNTIME_ORCHESTRATOR_URL)` | 直接 HTTP 调用 RO |
| **novaic-agent-runtime SagaWorker** | 同上 | 同上 |
| **novaic-agent-runtime Watchdog** | 同上 | 同上 |
| **novaic-gateway** | `get_runtime_orchestrator_client().forward(...)` | 出站调用 RO（如 runtimes/latest、cancel-by-subagent） |

**agent-runtime 对 ro_client 的典型调用**（来自 grep）：

- `runtime_handlers`: `ro_client.get_runtime`, `ro_client.update_runtime`
- `message_handlers`: `ro_client.get_subagent_status`, `ro_client.get_or_create_runtime`
- `context_handlers`: `ro_client.get_runtime`, `ro_client.append_context`
- `summary_handlers`: `ro_client.acquire_summary_lock`, `ro_client.get_hrl`, `ro_client.atomic_merge_history`
- `llm_handlers`: `ro_client.get_runtime`
- `subagent_handlers`: 通过 `SubAgentBusiness(ro_client=...)`
- `mcp`: `ro_client.get_runtime`, `ro_client.update_runtime`
- `watchdog_sync`: `ro_client.increment_drive_interaction`

### 4.2 谁调用 Gateway 的 /internal/*（19999）？

| 调用方 | 目标 | 说明 |
|--------|------|------|
| **novaic-tools-server** | GATEWAY_URL | executor 的 memory/notebook/quadrant-tasks 等 |
| **novaic-agent-runtime** | GATEWAY_URL | llm_handlers 的 `/internal/config/llm/agent/{id}` |
| **novaic-agent-runtime** | TOOLS_SERVER_URL | tool_handlers 的 `/internal/subagents/.../tools` |
| **novaic-runtime-orchestrator** | GATEWAY_URL | 部分逻辑需 Gateway（如 subagent/main、context/append） |

### 4.3 调用路径示意

```
                    ┌─────────────────────────────────────────┐
                    │         novaic-agent-runtime              │
                    │  (TaskWorker, SagaWorker, Watchdog)       │
                    └─────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │ RO (19993)    │  │ Gateway       │  │ Tools Server  │
            │ /internal/*   │  │ (19999)       │  │               │
            │ runtimes,     │  │ /internal/*   │  │ /internal/*   │
            │ subagents,    │  │ config,       │  │ tools         │
            │ messages,     │  │ agents...     │  │               │
            │ llm, etc.     │  │               │  │               │
            └──────────────┘  └──────────────┘  └──────────────┘
                    ▲                 ▲
                    │                 │
                    │         ┌───────┴───────┐
                    │         │   Gateway     │
                    └─────────│ forward()     │
                              │ 出站调 RO     │
                              └──────────────┘
```

---

## 五、关键结论

1. **RO 的 gateway.api.internal 有明确调用方**：agent-runtime 的 ro_client 直接访问 RO 的 19993 端口。
2. **Gateway 不提供 RO 的等价 API**：`/internal/runtimes/*`、`/internal/subagents/*`（运行时）、`/internal/messages/*`（claim/prepare）等均在 RO 实现，Gateway 已移除对应代理。
3. **两者职责不同**：
   - Gateway：Agent/SubAgent 元数据、消息队列、配置、VM 等
   - RO：Runtime 状态、SubAgent 运行时、消息认领与准备、LLM 调用、上下文等

---

## 六、可考虑的清理（非废弃）

### 6.1 RO 内的 maybe_forward 死代码

RO 启动时设置 `set_runtime_orchestrator_process(True)`，`maybe_forward_to_runtime_orchestrator` 始终返回 `None`，相关分支为死代码。可按 [RESEARCH-gateway-forward-to-ro.md](../../docs/RESEARCH-gateway-forward-to-ro.md) 建议删除。

### 6.2 个别可能未使用的端点

需逐端点确认，例如：

- `self_drive` 相关（Drive 自驱已废弃）
- `/internal/rt/*` 下的 quadrant-tasks、growth-log 等（见 [RESEARCH-tools-internal-rt-calls.md](../../docs/RESEARCH-tools-internal-rt-calls.md)）

---

## 七、总结

| 问题 | 结论 |
|------|------|
| RO 的 gateway.api.internal 是否没人调用？ | **否**，agent-runtime 通过 ro_client 大量调用 |
| gateway 是否已提供等价 API？ | **否**，Gateway 已移除 runtime 相关代理，RO 独占 |
| 是否应整体废弃？ | **否**，RO 的 internal API 是核心服务，不可废弃 |

建议：保留 RO 的 gateway.api.internal，仅对已确认的废弃功能（如 Drive 自驱）及 maybe_forward 等死代码做局部清理。
