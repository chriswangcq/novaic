# NovAIC 服务拆分原理与调用拓扑

> 更新：2026-04-10

---

## 一、为什么这么拆？——单一职责 × 故障隔离 × 独立扩缩

### 核心原则

| 原则 | 含义 | 实际效果 |
|---|---|---|
| **单一职责** | 一个进程只做一件事 | Gateway 不管 QEMU，Runtime 不管 Auth |
| **故障隔离** | 一个模块挂了不拖死全家 | VM 崩溃不影响消息收发、Agent 死循环不卡前端 |
| **独立扩缩** | 按瓶颈独立加机器 | 10 个 Agent 并发思考 → 加 Worker，不需要同时加 Gateway |
| **冷热分离** | 高频低延迟 vs 低频高耗时分开 | WS 推送(毫秒级) 和 LLM 推理(分钟级)不共享事件循环 |
| **安全边界** | 用户侧 vs 内部侧物理隔开 | Gateway 暴露公网；Worker/Cortex/Queue 只跑内网 |

### 拆分决策矩阵

```
                    用户直连？
                   ╱         ╲
                 YES          NO
                 ╱              ╲
            Gateway          内部服务
           (公网入口)        (仅内网)
                              ╱   ╲
                         长耗时?   短耗时?
                          ╱          ╲
                   需要队列/Saga    直接 HTTP
                      ╱                ╲
              Queue Service        Cortex / Factory
              + Worker               (无状态 API)
```

---

## 二、拆完后各服务及其职责

### 前端 × 1
| 服务 | 运行位置 | 职责 |
|---|---|---|
| **Tauri App** (Rust + React) | 用户本地桌面 | UI 渲染、本地 SQLite 缓存（Entangled 客户端）、WS 连接 Gateway |

### 后端 × 6（由 Tauri 或部署脚本统一拉起）

| 服务 | 端口 | 语言 | 职责 |
|---|---|---|---|
| **Gateway** | `19999` | Python/FastAPI | API 网关 + Auth + Entangled 数据宿主 + CloudBridge + AppBridge WS |
| **Queue Service** | `19997` | Python | Saga 状态机 + 任务队列 + Worker 调度 |
| **Runtime Orchestrator** | `19998` | Python | Agent 思考链编排（Watchdog + 消息处理 + SubAgent 管理） |
| **Cortex** | `19996` | Python/FastAPI | 认知引擎（上下文组装 + 记忆 + 压缩 + 沙盒执行） |
| **LLM Factory** | `19994` | Python/FastAPI | LLM 多提供商适配（OpenAI/Anthropic/本地模型路由） |
| **VmControl** | (Tauri内嵌) | Rust | 本地设备管理（QEMU/Scrcpy/adb/QMP），通过 CloudBridge 连 Gateway |

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
│  Tauri App  │◄═══════════════════►│   Gateway      │
│  (Frontend) │    REST(/api/*)      │   :19999       │
│  React +    │─────────────────────►│                │
│  Rust SQLite│                      │  ┌──────────┐  │
└─────────────┘                      │  │Entangled │  │
                                     │  │EntityStore│ │
     ┌──────────┐  CloudBridge WS    │  │(SQLite)  │  │
     │VmControl │◄═══════════════════│  └──────────┘  │
     │(用户本地) │  /internal/pc/ws   └──┬──┬──┬───────┘
     │QEMU/ADB  │                       │  │  │
     └──────────┘                       │  │  │
                                        │  │  │
            ┌───────────────────────────┘  │  └──────────────────┐
            │ HTTP                         │ HTTP                │ HTTP
            ▼                              ▼                     ▼
  ┌──────────────┐              ┌──────────────┐       ┌──────────────┐
  │   Runtime    │              │    Queue     │       │   Cortex     │
  │ Orchestrator │              │   Service    │       │   :19996     │
  │   :19998     │              │   :19997     │       │              │
  │              │              │              │       │ 上下文组装    │
  │ Watchdog     │──dispatch──►│ Saga 状态机   │       │ 记忆Recall   │
  │ 消息处理      │              │ 任务队列     │       │ 沙盒执行     │
  │ SubAgent     │              │ Worker调度   │       │ budget压缩   │
  └──────┬───────┘              └──────┬───────┘       └──────────────┘
         │                             │                       ▲
         │                         Worker(s)                   │
         │                         ┌───┴───┐                   │
         │                         │ think  │───────────────────┘
         │                         │ tool   │        调用 Cortex API
         │                         │ reply  │
         │                         └───┬───┘
         │                             │
         │                             ▼
         │                     ┌──────────────┐
         └────────────────────►│  LLM Factory │
              回调 Gateway      │   :19994     │
              更新消息状态       │              │
                               │ OpenAI/Anthropic│
                               │ 本地模型路由    │
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
③ Gateway → POST /internal/agent/process → Runtime Orchestrator
        │
        ▼
④ RO (Watchdog) 检测到新消息 → 创建 Saga
   → POST /api/sagas → Queue Service
        │
        ▼
⑤ Queue Service: Saga 状态机 → 分发 "think" 任务
   Worker 领取任务
        │
        ▼
⑥ Worker: 调用 Cortex API
   → GET /context/{agent_id}/assemble  (组装上下文)
   → POST /llm/chat → LLM Factory  (请求模型推理)
        │
        ▼
⑦ LLM 返回 tool_call → Worker 回调 Gateway
   → POST /internal/agent/tool_result
   Gateway: EntityStore.insert("execution_logs")
        │
        ▼
⑧ Worker 通过 CloudBridge → VmControl 执行命令
   VmControl: subprocess 跑 bash 脚本
   结果返回 → Worker → 继续 think 循环
        │
        ▼
⑨ LLM 返回最终回复 → Worker 回调 Gateway
   Gateway: EntityStore.insert("chat_messages", type="AGENT_REPLY")
   Entangled WS 推送 → 前端实时显示回复
```

---

## 五、拆分边界的核心依据

| 边界线 | 为什么在这里切 |
|---|---|
| Gateway ↔ Runtime | Gateway 是**同步 HTTP**处理（毫秒级），Runtime 是**长耗时推理**编排（秒~分钟级）。混在一起会阻塞 WS 推送 |
| Runtime ↔ Queue | Runtime 负责**业务决策**（该不该 think、该不该 rest），Queue 负责**可靠执行**（重试、超时、持久化）。分开后 Runtime 崩溃不丢任务 |
| Queue ↔ Cortex | Queue 是**通用调度器**（不知道什么是 Agent），Cortex 是**领域引擎**（只知道上下文和记忆）。分开后 Cortex 可以被其他项目复用 |
| Gateway ↔ VmControl | 物理隔离——VmControl 跑在用户本地电脑上，Gateway 跑在云端。通过 CloudBridge WS 穿透 NAT |
| Gateway ↔ LLM Factory | LLM Factory 是**无状态适配器**，可以独立横向扩展。不同用户用不同的 API Key，路由逻辑不应该污染 Gateway |
