# NovAIC 服务拆分原理与调用拓扑

> 更新：2026-04-10

---

## 一、为什么这么拆？——单一职责 × 故障隔离 × 独立扩缩

### 核心原则

| 原则 | 含义 | 实际效果 |
|---|---|---|
| **单一职责** | 一个进程只做一件事 | Gateway 不管 QEMU，Task Worker 不管 Auth |
| **故障隔离** | 一个模块挂了不拖死全家 | VM 崩溃不影响消息收发、Agent 死循环不卡前端 |
| **独立扩缩** | 按瓶颈独立加机器 | 10 个 Agent 并发思考 → 加 Task Worker，不需要同时加 Gateway |
| **冷热分离** | 高频低延迟 vs 低频高耗时分开 | WS 推送(毫秒级) 和 LLM 推理(分钟级)不共享事件循环 |
| **安全边界** | 用户侧 vs 内部侧物理隔开 | Gateway 暴露公网；Worker/Cortex/Queue 只跑内网 |

---

## 二、当前实际服务清单（来自 main_novaic.py）

### 前端 × 1
| 服务 | 运行位置 | 职责 |
|---|---|---|
| **Tauri App** (Rust + React) | 用户本地桌面/手机 | UI 渲染、本地 SQLite 缓存（Entangled 客户端）、WS 连接 Gateway |

### 后端进程（由 Tauri sidecar 或部署脚本统一拉起）

| 进程 | 端口 | 职责 |
|---|---|---|
| **Gateway** | `19999` | API 网关 + Auth + Entity Proxy + Turn + File Proxy + AppBridge WS (signaling) |
| **Tools Server** | (独立 repo) | HTTP API for tools（替代旧 MCP Gateway） |
| **Queue Service** | `19997` | Saga 状态机 + 任务队列 + Worker 调度 |
| **Watchdog** | (worker) | 已弃用的兼容入口；生产不再承担定时唤醒职责 |
| **Saga Worker** | (worker) | Saga 流程编排（MessageProcess、RuntimeComplete、SubAgentCreate 等） |
| **Task Worker** | (worker) | 实际任务执行（ReactThink、ToolExec、SummarizeHistory 等） |
| **Health Worker** | (worker) | 超时回收（过期 Task/Saga 清理） |
| **Scheduler Worker** | (worker) | 唯一的定时唤醒轮询者（`due_wake -> scheduled_wake dispatch`） |
| **Cortex** | `19996` | 认知引擎（上下文组装 + 记忆 + 压缩 + 沙盒执行 + **GatewayProxy 工具代理**） |
| **LLM Factory** | `19994` | LLM 多提供商适配（OpenAI/Anthropic/本地模型路由） |
| **VMControl** | (Tauri内嵌Rust) | 唯一 runtime owner（QEMU/Scrcpy/adb/WebRTC），通过 typed CloudBridge WS 连 Device Service |
| **Storage-A** | `19995` | 文件服务（独立 repo） |

> ⚠️ **没有 Runtime Orchestrator（RO）**。原 RO 的职责已由 Saga Worker + Task Worker + Queue Session Coordinator 接管。`--runtime-orchestrator-url` 参数虽存在于 CLI 但已标记 `argparse.SUPPRESS`。

---

## 三、完整调用拓扑图

```
                                    ┌──────────────────┐
                                    │   Nginx Reverse  │
                                    │   Proxy (HTTPS)  │
                                    └────────┬─────────┘
                                             │ auth_request → /internal/auth/validate
                                             ▼
┌─────────────┐    WS(/api/app/ws)   ┌───────────────┐
│  Tauri App  │◄═══════════════════►│   Gateway      │◄══════════════════════════╗
│  (Frontend) │    REST(/api/*)      │   :19999       │                          ║
│  React +    │─────────────────────►│                │                          ║
│  Rust SQLite│                      │  ┌──────────┐  │                          ║
└─────────────┘                      │  │Entangled │  │                          ║
                                     │  │EntityStore│ │                          ║
     ┌──────────┐  CloudBridge WS    │  │(SQLite)  │  │                          ║
     │VMControl │◄══(Device Service)══│  └──────────┘  │                          ║
     │(用户本地) │  /internal/pc/ws   └──┬──────┬──────┘                          ║
     │WebRTC/VM │                       │      │                                ║
     └──────────┘                       │      │                                ║
                                        │      │                                ║
          ┌─────────────────────────────┘      └──────────────────────┐          ║
          │ HTTP (internal API)                                        │         ║
          ▼                                                            ▼         ║
   ┌──────────────┐                                             ┌──────────────┐ ║
   │ Queue Service │◄────── saga.create ──────────────────────  │ Cortex       │ ║
   │   :19997      │                                             │  :19996      │ ║
   │               │                                             │              │ ║
   │ Saga 状态机    │                                             │ 上下文组装    │ ║
   │ 任务队列      │                                             │ 沙盒执行     │ ║
   │ Worker调度    │                                             │ budget压缩   │ ║
   └──────┬────────┘                                             │              │ ║
          │                                                      │ GatewayProxy ╠═╝
          │ poll                                                 │ (工具代理)    │
    ┌─────┼──────────────────────┐                               │ memory/note  │
    │     │                      │                               │ qemu/shell   │
    ▼     ▼                      ▼                               │ subagent/...│
┌────────┐ ┌───────────┐  ┌───────────┐                          └──────────────┘
│Watchdog│ │Saga Worker│  │Task Worker│────── 调用 Cortex API ─────────┘
│        │ │           │  │           │
│监控     │ │MessageProc│  │ReactThink │────── 调用 LLM Factory ──┐
│sending │ │RuntimeComp│  │ToolExec   │                          │
│消息     │ │SubAgentCr │  │Summarize  │                          │
│→创Saga │ │           │  │           │                          ▼
└────────┘ └───────────┘  └─────┬─────┘                   ┌──────────────┐
                                │                          │  LLM Factory │
                                │ 回调 Gateway              │   :19994     │
                                │ 更新消息/SubAgent状态     │              │
                                └──────────────────────────│ OpenAI/Claude│
                                                           │ 本地模型路由  │
                                                           └──────────────┘
```

---

## 四、一条消息的完整生命周期

```
用户在 App 输入 "帮我写个脚本"
        │
        ▼
① Tauri App → POST /api/chat/send → Gateway
        │
        ▼
② Gateway: EntityStore.insert("chat_messages") → 写入 SQLite
   触发 Entangled WS 推送 → 前端实时显示 "发送中"
        │
        ▼
③ Queue Session Coordinator / Scheduler
   用户消息或定时唤醒经 `/api/queue/dispatch`
   创建或缓冲 MessageProcess / subagent_wake Saga
        │
        ▼
④ Saga Worker: 领取 Saga → 执行 MessageProcess 流程
   → Gateway: POST /internal/subagents/{id}/awake
   → Queue: 分发 "ReactThink" Task
        │
        ▼
⑤ Task Worker: 领取 ReactThink 任务
   → Gateway: GET /internal/agents/{id}/drive  (system prompt)
   → Gateway: GET /internal/agents/{id}/memory/all  (记忆)
   → Cortex: GET /context/{agent_id}/assemble  (组装上下文)
   → LLM Factory: POST /llm/chat  (请求模型推理)
        │
        ▼
⑥ LLM 返回 tool_call → Task Worker
   → Queue: 分发 "ToolExec" Task
   → 另一个 Task Worker 执行工具
   → 通过 CloudBridge → VmControl 执行命令
   → 结果返回 → 继续 ReactThink 循环
        │
        ▼
⑦ LLM 返回最终回复 → Task Worker 回调 Gateway
   → Gateway: POST /internal/agents/{id}/chat/event (type=AGENT_REPLY)
   → EntityStore.insert → Entangled WS 推送 → 前端实时显示回复
        │
        ▼
⑧ Saga Worker: RuntimeComplete Saga
   → Gateway: POST /internal/subagents/{id}/sleeping
   → Gateway: POST /internal/subagent/context/append (保存上下文)
```

---

## 五、拆分边界的核心依据

| 边界线 | 为什么在这里切 |
|---|---|
| Gateway ↔ Workers | Gateway 是**同步 HTTP**处理（毫秒级），Workers 是**长耗时推理**编排（秒~分钟级）。混在一起会阻塞 WS 推送 |
| Scheduler/Queue ↔ Workers | Scheduler 负责**发现**到期唤醒，Queue 负责**可靠调度**（Session Coordinator、重试、超时、持久化），Workers 负责**执行**。分开后任何一环崩溃不丢任务 |
| Saga Worker ↔ Task Worker | Saga 负责**流程编排**（状态机流转），Task 负责**原子执行**（单次 ReactThink/ToolExec）。分开后可独立扩缩：5 个 Task Worker + 1 个 Saga Worker |
| Workers ↔ Cortex | Workers 是**通用调度器**（不知道什么是上下文），Cortex 是**领域引擎**（上下文 + 记忆 + 工具代理）。Cortex 通过 `GatewayProxy` 把 12 类工具命令（memory/notebook/qemu/shell/subagent 等）代理转发到 Gateway。分开后 Cortex 可独立复用 |
| Device Service ↔ VMControl | 物理隔离——VMControl 跑在用户本地电脑上，Device Service 跑在云端。通过 typed CloudBridge WS 穿透 NAT。Gateway 只做 App 信令转发，不拥有 CloudBridge |
| Gateway ↔ LLM Factory | LLM Factory 是**无状态适配器**，可以独立横向扩展。不同用户用不同的 API Key，路由逻辑不应该污染 Gateway |
