# NovAIC 接手技术文档

> 指挥中心 — 新人接手与项目理解指南

---

## 1. 项目概览

### 1.1 是什么

NovAIC 是一个**桌面端 AI Agent 系统**，具备：

- **多 Agent 管理**：支持多个 AIC Agent，每个 Agent 有 Main SubAgent 和可派生的 Sub SubAgent
- **ReAct 循环**：Think → Tools → Think，支持并行工具调用
- **VM 与移动设备**：QEMU 虚拟机、Android 设备控制
- **工具生态**：60+ 内置工具（Memory、Runtime、Chat、Web、VM、Mobile 等）

### 1.2 架构类型

- **Master-Driven**：Gateway 作为协调中心
- **Saga/Task**：业务流程用 Saga 编排，原子操作用 Task 执行
- **Split 多仓库**：各服务独立 repo，由 Tauri 应用统一拉起

---

## 2. 仓库与职责

| 仓库 | 职责 | 技术栈 |
|------|------|--------|
| **novaic-app** | Tauri 桌面壳 + React 前端 | Rust, TypeScript, React, Vite |
| **novaic-gateway** | API 网关、Agent/SubAgent、DB | Python, FastAPI, SQLite |
| **novaic-runtime-orchestrator** | Runtime 编排、主 Agent 流程 | Python, FastAPI, SQLite |
| **novaic-tools-server** | 工具执行、MCP 集成 | Python, FastAPI |
| **novaic-agent-runtime** | Queue Service、Task/Saga Worker | Python |
| **novaic-storage-a** | File Service | Python |
| **novaic-storage-b** | Tool Result Service | Python |
| **novaic-mcp-vmuse** | VM 内 MCP 工具 | Python |
| **novaic-control-plane** | 指挥中心、跨 repo 协调 | Markdown, 流程 |

---

## 3. 核心概念

### 3.1 Agent

- 每个 Agent 有唯一 `agent_id`
- 每个 Agent 有一个 **Main SubAgent**（`main-{agent_id[:8]}`）
- 可派生子任务，产生 **Sub SubAgent**（`sub-{uuid}`）

### 3.2 Runtime

- 每个 SubAgent 有多个 Runtime（`runtime_id`）
- Runtime 状态：`active` / `resting` / `completed`
- 每个 Runtime 对应一次 ReAct 会话

### 3.3 Task & Saga

- **Task**：原子操作，如 `runtime.create`、`tool.execute`
- **Saga**：多步骤流程，如 `message_process`、`react_think`、`react_actions`
- 由 Worker 进程从 Queue Service 拉取并执行

### 3.4 工具执行

- 工具由 **Tools Server** 统一执行
- 内置工具：HTTP 调 Gateway / vmcontrol
- 外部工具：MCP 客户端
- 结果存入 **TRS**（Tool Result Service），返回 `result_id` 供 LLM 使用

---

## 4. 数据流速览

```
用户 → 前端 → Gateway API
  → chat_messages (DB)
  → message_process Saga
  → runtime_start → react_think
  → llm.call (OpenAI/Anthropic)
  → react_actions → tool.execute
  → Tools Server → Gateway/vmcontrol
  → TRS 存储
  → context.append
  → 下一轮或 runtime_complete
```

---

## 5. 接手检查清单

### 5.1 环境

- [ ] Python 3.11+，各 repo 有 `.venv`
- [ ] Node.js 18+
- [ ] Rust + Cargo
- [ ] 能成功执行 `./scripts/build-dmg.sh`
- [ ] **iOS 构建**（可选）：Xcode、Apple Developer；`cd novaic-app && ./scripts/build-and-install-ios.sh`，详见项目根 `HANDOVER.md` 第四节

### 5.2 理解

- [ ] 阅读 `novaic/ARCHITECTURE.md`
- [ ] 阅读 `novaic-control-plane/docs/DEV_GUIDE.md`
- [ ] 跑通一次完整流程：创建 Agent → 发消息 → 观察 Execute Log

### 5.3 调试

- [ ] 知道数据目录：`~/Library/Application Support/com.novaic.app/`
- [ ] 知道日志位置：`logs/` 下各服务日志
- [ ] 会用 curl 调 API、用 sqlite3 查 DB

---

## 6. 关键文件索引

| 关注点 | 文件路径 |
|--------|----------|
| 架构总览 | `novaic/ARCHITECTURE.md` |
| 开发指南 | `novaic-control-plane/docs/DEV_GUIDE.md` |
| 待办 | `novaic-control-plane/BACKLOG.md` |
| 工具定义 | `novaic-*/common/tools/definitions.py` |
| 工具执行 | `novaic-tools-server/tools_server/executor.py` |
| TRS 解析 | `novaic-agent-runtime/task_queue/utils/trs_sdk.py` |
| SubAgent 状态 | `novaic-gateway/gateway/api/internal/agent.py` |
| Saga 定义 | `novaic-agent-runtime/task_queue/sagas/` |
| 前端 Store | `novaic-app/src/store/index.ts` |
| 前端 API | `novaic-app/src/services/api.ts` |

---

## 7. 常见坑

1. **B2 Split**：Gateway 与 Runtime Orchestrator 职责分离，Gateway 管 Agent/SubAgent，RO 管 Runtime
2. **result_id 必传**：每个 tool_call 必须有 result_id，失败时也需推 TRS 存 error
3. **subagent_id 格式**：Main 为 `main-{agent_id[:8]}`，Sub 为 `sub-{uuid}`
4. **TRS display_files**：必须是 `{url, filename, modality}`，否则校验失败

---

## 8. 相关链接

- [Round 模板](rounds/round-template/) — 新 Round 模板
- [Related Repositories](../README.md#related-repositories) — 各仓库地址
