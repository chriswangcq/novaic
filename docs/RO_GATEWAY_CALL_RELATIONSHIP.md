# RO 与 Gateway 调用关系梳理

> 2025-03 更新，基于当前代码

---

## 一、架构概览

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
            │ RO (19993)   │  │ Gateway       │  │ Tools Server  │
            │ /internal/*  │  │ (19999)       │  │ (20002)       │
            │ runtimes     │  │ /internal/*   │  │               │
            │ subagents    │  │ subagents     │  │               │
            └──────────────┘  │ messages      │  └──────────────┘
                    ▲        │ agents        │
                    │        │ config, vm... │
                    │        └──────────────┘
                    │                │
                    └────────────────┘
                        互相调用
```

- **RO**：Runtime 状态、SubAgent 运行时、上下文、LLM 等
- **Gateway**：Agent/SubAgent 元数据、消息队列、配置、VM、任务等
- **agent-runtime**：同时调用 RO 和 Gateway，按路径分发

---

## 二、Gateway → RO 调用

### 2.1 启动依赖

**Gateway 无需强依赖 RO 启动**。当前 `check_runtime_orchestrator_health()` 是历史遗留，可移除。

- 所有 Gateway → RO 的业务调用（spawn、cancel、delete）均由 **Worker 触发的 internal API** 发起
- 启动阶段 Gateway 不会调用 RO
- Workers 在「所有服务健康检查通过」后才启动，届时 RO 已就绪

### 2.2 业务调用（RuntimeOrchestratorClient.forward）

| 入口 | 方法 | RO 路径 | 场景 |
|------|------|---------|------|
| subagent spawn (share_context) | GET | `/internal/runtimes/latest/{agent_id}/{parent_subagent_id}` | 获取父 SubAgent 的 context 用于子 SubAgent 初始化 |
| agent subagent spawn (share_context) | GET | `/internal/runtimes/latest/{agent_id}/{parent_subagent_id}` | 同上 |
| agent subagent merge (share_context) | GET | `/internal/runtimes/latest/{agent_id}/{target_subagent_id}` | 合并 target 的 context |
| subagent cancel | POST | `/internal/runtimes/cancel-by-subagent` | 取消 SubAgent 时通知 RO 取消对应 Runtime |
| subagent delete | POST | `/internal/runtimes/delete-by-subagent` | 删除 SubAgent 时通知 RO 删除对应 Runtime |
| agent subagent cancel | POST | `/internal/runtimes/cancel-by-subagent` | 同上 |

**调用位置**：
- `gateway/api/internal/subagent.py`：spawn、cancel、delete
- `gateway/api/internal/agent.py`：agent_subagent_spawn、agent_subagent_merge、agent_subagent_cancel

**说明**：上述入口均由 **agent-runtime (Worker)** 调用 Gateway internal API 触发，启动阶段不会发生。

---

## 三、RO → Gateway 调用

### 3.1 唯一调用：context 同步

| 时机 | 调用 | Gateway 路径 | 说明 |
|------|------|--------------|------|
| RO append_context 成功后 | 异步 task | `POST {GATEWAY_URL}/internal/subagents/{agent_id}/{subagent_id}/context/append` | 将 context 增量推送到 Gateway，供 history API 使用 |

**位置**：`novaic-runtime-orchestrator/gateway/api/internal/runtime.py` 第 297、317–336 行

**逻辑**：
- agent-runtime 调用 RO 的 `POST /internal/runtimes/{id}/context/append`
- RO 写入本地 DB 后，`asyncio.create_task(_push_context_to_gateway(...))` 异步推送到 Gateway
- Gateway 的 `POST /internal/subagents/{agent_id}/{subagent_id}/context/append` 接收并写入 subagent_context
- Best-effort，失败仅打 log，不阻塞 RO 主流程

**依赖**：RO 需配置 `GATEWAY_URL`，否则跳过推送。

---

## 四、agent-runtime 的分发逻辑

agent-runtime 的 `UnifiedInternalClient` / `TaskQueueClient` 按路径选择目标：

| 路径模式 | 目标 | 说明 |
|----------|------|------|
| `/internal/runtimes/*` | RO (RUNTIME_ORCHESTRATOR_URL) | Runtime 状态、context、advance 等 |
| `/internal/subagents/*`（部分） | RO | 运行时状态、status、hrl、merge-history 等 |
| `/internal/subagents/*`（部分） | Gateway | 元数据 CRUD、context/append（Gateway 实现） |
| `/internal/messages/*` | Gateway | 消息队列、claim、confirm 等 |
| `/internal/agents/*` | 混合 | drive、info → RO；其他 → Gateway |
| `/internal/config/*` | Gateway | LLM 配置等 |

---

## 五、总结

| 方向 | 调用数 | 主要用途 |
|------|--------|----------|
| **Gateway → RO** | 启动 1 次 + 业务若干 | 健康检查；spawn 时拉 context；cancel/delete 时通知 RO |
| **RO → Gateway** | 每次 context append | 将 context 增量同步到 Gateway，供 history 展示 |

**依赖关系**：
- Gateway 启动**不依赖** RO（业务调用由 Worker 触发，Worker 启动时 RO 已就绪）
- RO 运行**弱依赖** Gateway（context 推送失败不影响 RO 主流程，仅影响 history 展示）
