# 服务与 Handler 架构梳理

## 一、服务启动矩阵

| 服务 | 启动方式 | 实际执行的包 | 职责 |
|------|----------|--------------|------|
| **Runtime Orchestrator** | `novaic-runtime-orchestrator` / `main_runtime_orchestrator.py` | novaic-runtime-orchestrator | HTTP API：`/internal/*`（runtime 生命周期等） |
| **Gateway** | `novaic-gateway` / `main_gateway.py` | novaic-gateway | HTTP API：对外入口、消息队列、subagent 等 |
| **Tools Server** | `novaic-tools-server` / `main_tools.py` | novaic-tools-server | HTTP API：工具执行（`/internal/subagents/*/tools/*`） |
| **Queue Service** | `main_novaic.py queue-service` | novaic-agent-runtime | Task/Saga 队列管理 |
| **Watchdog** | `novaic-agent-runtime watchdog` | novaic-agent-runtime | 监控 sending 消息，触发 MessageProcess Saga |
| **Task Worker** | `novaic-agent-runtime task-worker` | novaic-agent-runtime | 认领并执行 Task（tool、llm、message、runtime、context 等） |
| **Saga Worker** | `novaic-agent-runtime saga-worker` | novaic-agent-runtime | 认领并执行 Saga（message_process、runtime_start、react_think 等） |
| **Health Worker** | `novaic-agent-runtime health` | novaic-agent-runtime | 回收超时 Task/Saga |

---

## 二、关键结论：谁在跑 Handler？

**Task Worker 和 Saga Worker 只从 `novaic-agent-runtime` 启动。**

- 启动命令：`novaic-agent-runtime task-worker` 或 `python main_novaic.py task-worker`
- 工作目录：`novaic-agent-runtime/`
- 导入：`from task_queue.handlers import get_all_topics` → **agent-runtime 的 handlers**

因此：

| 包 | task_queue/handlers | 是否被执行 |
|----|---------------------|------------|
| **novaic-agent-runtime** | ✅ 有 | ✅ **实际执行** |
| novaic-tools-server | 已删除 | task_queue 已移除（死代码） |
| novaic-runtime-orchestrator | ✅ 有 | ❌ **从不执行**（死代码） |

---

## 三、Tools Server 包的真实职责

Tools Server 包（novaic-tools-server）**只提供 HTTP API**：

- `main_tools.py` → FastAPI 应用
- 路由：`/internal/subagents/{agent_id}/{subagent_id}/tools/*`（工具注册、调用等）
- **不启动任何 Worker**

Tools Server 包内的 `task_queue/` 目录已删除（2025-03 确认死代码后移除）。

---

## 四、对「Tools Server 摘除 runtime」工作的影响

### 4.1 之前改动的实际影响

| 改动 | 影响范围 | 实际效果 |
|------|----------|----------|
| 移除 Tools Server 的 runtime/context handlers | novaic-tools-server | **无影响**（该包从不跑 worker） |
| Tools Server GatewayInternalClient 去掉 internal_url | novaic-tools-server | **无影响**（该 client 仅被 Tools Server 的 handlers 使用，而 handlers 不执行） |
| 移除 RUNTIME_ORCHESTRATOR_URL | novaic-tools-server | **有影响**：Tools Server 的 **API 层**（如 runtime_manager、executor）若调用该 client，会受影响。需单独核查。 |

### 4.2 架构决策：agent-runtime 允许内部调用 RO

**novaic-agent-runtime 允许在内部直连 RO**，可保留 RUNTIME_ORCHESTRATOR_URL，调用 get_runtime、get_or_create_runtime、append_context 等 runtime API。无需摘除。

### 4.3 Tools Server API 层

Tools Server 的 HTTP API 层（runtime_manager、executor、api）仅使用 gateway_url（subagent 维度 API），不依赖 RUNTIME_ORCHESTRATOR_URL。✅ 已确认。

---

## 五、总结

| 包 | 是否依赖 RO | 说明 |
|----|-------------|------|
| **novaic-tools-server** | ❌ 不依赖 | 仅 HTTP API，task_queue 已删除（死代码）；已移除 RUNTIME_ORCHESTRATOR_URL |
| **novaic-agent-runtime** | ✅ 允许调用 | Worker 实际执行者，直连 RO 的 runtime API |
