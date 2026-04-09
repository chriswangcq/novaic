> **文档说明**：服务启动与 **task_queue.handlers** 责任矩阵（现行对齐）；全栈图见 `docs/backend-architecture.md`。**batch12**：已对照 `main_novaic` / `start.sh` / `watchdog_sync` 修正 Gateway 行与 Watchdog saga 名。

# 服务与 Handler 架构梳理

> **2026-04 更新**：已与 `novaic-agent-runtime`、`HANDOVER.md`、`docs/agent-handoff-context.md` 对照。本父仓库 **不包含** `novaic-runtime-orchestrator/`、`novaic-tools-server/` 子目录；下文「历史」小节保留旧结论索引。  
> **深度核查（配置缺口、deploy 与脚本漂移、schema v63 等）**：`docs/architecture-verification-2026-04.md`。

---

## 一、服务启动矩阵（当前仓库可验证部分）

| 服务 | 启动方式 | 实际执行的包/入口 | 职责 |
|------|----------|-------------------|------|
| **Gateway** | **`novaic-gateway/main_gateway.py`**（与 `scripts/start.sh` 一致）；或 `novaic-agent-runtime/main_novaic.py gateway`（须能 import `main_gateway`，通常需 **`PYTHONPATH` 含 `novaic-gateway`**，否则易 ImportError） | `novaic-gateway` | 对外 `/api/*`、对内 `/internal/*`、认证、Entangled 客户端、VM/文件代理等 |
| **Entangled Service** | `entangled-service/main.py`（路径以部署为准） | `entangled-service` | 实体引擎 HTTP；agents/messages 等权威存储（Gateway 注册 schema） |
| **Cortex** | `python -m novaic_cortex.main_cortex`（默认 `CORTEX_PORT=19996`） | `novaic-cortex` | Workspace / Context / Sandbox HTTP API |
| **Queue Service** | `main_novaic.py queue-service --port …` | `novaic-agent-runtime/queue_service` | Task/Saga 队列 HTTP |
| **Watchdog** | `novaic-agent-runtime watchdog` | `novaic-agent-runtime` | 监控 sending 消息；需唤醒时启动 **`subagent_wake` Saga**（见 `task_queue/workers/watchdog_sync.py`；勿与旧名 MessageProcess 混用） |
| **Task Worker** | `novaic-agent-runtime task-worker` | `novaic-agent-runtime` | 认领并执行 Task（`task_queue/handlers`） |
| **Saga Worker** | `novaic-agent-runtime saga-worker` | `novaic-agent-runtime` | 认领并执行 Saga |
| **Health Worker** | `novaic-agent-runtime health` | `novaic-agent-runtime` | 回收超时 Task/Saga |
| **Scheduler** | `novaic-agent-runtime scheduler` | `novaic-agent-runtime` | 定时任务（如 SYSTEM_WAKE） |
| **VMControl** | `main_novaic.py vmcontrol` | Rust 二进制（见 `main_novaic.py`） | VM 控制 HTTP（默认端口与 Cortex 均为 19996 时需错开） |
| ~~**Runtime Orchestrator**~~ | — | — | **已从父仓库移除**；职责拆至 Gateway + Cortex + Agent-Runtime（`HANDOVER.md`） |
| **Tools Server（可选）** | 仅当设置 `NOVAIC_TOOLS_SERVER_SPLIT_REPO` 且该路径含 `main_tools.py`：`main_novaic.py tools-server` | **分拆仓库** | 本 monorepo **不含** `main_tools.py`；`HANDOVER.md` 记业务上工具由 Agent-Runtime + Cortex 为主 |

---

## 二、关键结论：谁在跑 `task_queue.handlers`？

**Task Worker 与 Saga Worker 只从 `novaic-agent-runtime` 启动。**

- 启动：`python main_novaic.py task-worker` / `saga-worker`（工作目录 `novaic-agent-runtime/`）
- 导入：`from task_queue.handlers import …` → **仅** `novaic-agent-runtime/task_queue/handlers/`

| 包 | 本仓库是否存在 | `task_queue/handlers` | 是否被执行 |
|----|----------------|------------------------|------------|
| **novaic-agent-runtime** | ✅ | ✅ 有 | ✅ **实际执行** |
| **novaic-runtime-orchestrator** | ❌ 无目录 | — | **不适用**（子模块已删除，非「有代码从不跑」） |
| **novaic-tools-server** | ❌ 无目录 | — | **不适用**；分拆仓若存在则为独立 FastAPI，与 worker handlers 无关 |

---

## 三、Tools Server（历史与现状）

**历史（分拆仓时代）**：独立 `main_tools.py` 可提供 `/internal/subagents/.../tools/*` 等 HTTP，**不**负责启动 Task/Saga Worker。

**当前父仓库**：

- `main_novaic.py` 中 `run_tools_server()` **要求** `NOVAIC_TOOLS_SERVER_SPLIT_REPO` 指向含 `main_tools.py` 的目录，否则直接报错（R016：monorepo 已移除内嵌 tools_server）。
- `HANDOVER.md`：**Tools Server 已退役**（工具执行由 Agent-Runtime `tool_handlers` + Cortex 接管）。

若仍维护独立 tools HTTP 进程，需在**分拆仓库**内单独对照路由与依赖；本文档不再断言该仓内文件结构。

---

## 四、与 Runtime Orchestrator 相关的旧讨论（归档）

以下条目针对**曾存在的** `novaic-tools-server` / RO 拆分改造，**仅供查旧 PR/讨论**；当前以 Gateway Internal API + Cortex HTTP 为准。

- 曾讨论「Tools Server API 是否依赖 `RUNTIME_ORCHESTRATOR_URL`」— RO 删除后由 Cortex / Gateway 路径替代。
- 曾讨论「agent-runtime 是否允许直连 RO」— RO 已不存在于本布局；Runtime 生命周期与 context 请查 `novaic-agent-runtime` 内对 Gateway `/internal/*` 与 Cortex 的 HTTP 调用。

---

## 五、总结

| 主题 | 当前结论 |
|------|----------|
| **Worker / Handler** | 仅 `novaic-agent-runtime` 进程执行 `task_queue.handlers` |
| **RO** | 非「死代码」，而是**子模块已从父仓库移除** |
| **Tools Server** | 父仓库无包；可选分拆仓 + 环境变量；业务默认不走独立 Tools Server |
| **权威文档** | 运行时关系以 `docs/agent-handoff-context.md`、代码 `main_gateway.py` / `main_novaic.py` 为准 |
