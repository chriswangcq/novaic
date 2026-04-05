# NovAIC 后端架构

> 最后更新: 2026-04-05

## 概览

NovAIC 后端采用**微服务 + 事件驱动**架构。所有服务部署在 `api.gradievo.com`（LLM Factory 除外），通过 HTTP 内部 API 互相通信。核心设计理念：

- **Gateway 是唯一数据权威** — 所有业务实体（agents、messages、config）存储在 Gateway 的 SQLite
- **Task Queue 驱动异步执行** — 消息处理、LLM 调用、工具执行全部通过 Saga 编排
- **Entangled 实时同步** — 前端通过 SSE 订阅实体变更，无需轮询

```
┌─────────────┐    SSE/WS     ┌──────────────┐
│  novaic-app  │◄────────────►│   Gateway     │ :19999
│  (Tauri/Web) │    REST      │  (FastAPI)    │
└─────────────┘               └──────┬───────┘
                                     │ HTTP internal
                    ┌────────────────┼────────────────┐
                    ▼                ▼                 ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Runtime     │ │ Queue Service │ │ Tools Server │
            │ Orchestrator  │ │              │ │              │
            │ :19993        │ │ :19997       │ │ :19998       │
            └──────────────┘ └──────┬───────┘ └──────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌───────────┐  ┌───────────┐  ┌───────────┐
              │ Watchdog   │  │ Saga      │  │ Task      │
              │            │  │ Workers×2 │  │ Workers×4 │
              └───────────┘  └───────────┘  └───────────┘
                                    │
                                    ▼ HTTP
                        ┌──────────────────────┐
                        │   LLM Factory        │ :19990
                        │ (newapi.gradievo.com) │
                        └──────────────────────┘
```

---

## 服务清单

| 服务 | 端口 | 部署位置 | 职责 |
|------|------|----------|------|
| **Gateway** | 19999 | api.gradievo.com | REST/SSE API、实体存储、Entangled 同步、鉴权 |
| **Runtime Orchestrator** | 19993 | api.gradievo.com | Runtime 生命周期、Subagent 状态协调、Context 存储 |
| **Queue Service** | 19997 | api.gradievo.com | 任务队列（tq_tasks）、Saga 编排（tq_sagas）、幂等控制 |
| **Tools Server** | 19998 | api.gradievo.com | MCP 工具注册/执行、chat_reply 等核心工具 |
| **File Service** | 19995 | api.gradievo.com | 文件上传/下载（novaic-storage-a） |
| **Watchdog** | — | api.gradievo.com | 轮询 sending 消息队列，创建 Saga |
| **Task Workers** | — | api.gradievo.com | 2 control + 2 execution，执行具体任务 |
| **Saga Workers** | — | api.gradievo.com | 2 个，编排多步 Saga |
| **Health** | — | api.gradievo.com | 健康检查、超时任务清理 |
| **Scheduler** | — | api.gradievo.com | 定期唤醒 Agent（SYSTEM_WAKE） |
| **LLM Factory** | 19990 | newapi.gradievo.com | LLM 代理、模型路由、重试、多 Provider 支持 |

---

## 数据存储

### gateway.db（Gateway SQLite）

业务数据的唯一来源，所有实体通过 EntityStore 管理。

| 表 | 用途 |
|----|------|
| `users` | 用户账号 |
| `agents` | Agent 定义（user_scoped） |
| `chat_messages` | 消息流（Stream 类型），含 status/read 队列控制字段 |
| `execution_logs` | 执行日志（Stream 类型） |
| `subagents` | Subagent 状态 |
| `agent_memory` | Agent 记忆 |
| `skills` | 技能定义 |
| `models` / `api_keys` | 模型和 API Key 配置 |
| `config` | 全局配置 |

### Runtime Orchestrator DB

| 表 | 用途 |
|----|------|
| `runtimes` | Runtime 实例（含 context JSON） |
| `subagent_context` | Subagent 运行状态 |

### queue.db（Queue Service SQLite）

| 表 | 用途 |
|----|------|
| `tq_tasks` | 任务队列（topic, status, payload） |
| `tq_sagas` | Saga 实例（type, status, context, steps） |
| `tq_idempotency_ledger` | 幂等控制（防重复执行） |

### llm_factory.db（LLM Factory SQLite）

| 表 | 用途 |
|----|------|
| `llm_logs` | LLM 调用日志（model, tokens, latency, request/response body） |
| `models` | 模型定义（UUID → provider + model_name） |
| `api_keys` | Provider API Key |
| `user_defaults` | 用户默认模型 |

---

## 核心子系统

### 1. EntityStore（实体存储引擎）

位置: `novaic-gateway/gateway/entity/store.py`

EntityStore 是 Gateway 的核心抽象层，对应前端 `createListStore` / `createFormStore`。每个实体通过 `EntityDef` 定义：

```python
MESSAGES = EntityDef(
    name="messages",              # 与前端 useStream("messages") 对应
    table="chat_messages",        # 实际 SQL 表名
    sync_type="stream",           # list（CRUD）或 stream（追加为主）
    user_scoped=False,            # True 时按 user_id 隔离
    parent=("agents", "agent_id", "id"),  # 级联鉴权
    key_params=["agent_id"],      # 路由参数
    default_not_in_filters={      # UI 查询自动排除的类型
        "type": ["SYSTEM_WAKE", "SUBAGENT_SEND", ...],
    },
    fields=[...],                 # 字段定义，驱动 DDL 和序列化
)
```

关键特性：

- **`fields` + DDL 管理**: `FieldDef` 声明字段类型，`ensure_schema()` 幂等建表/加列
- **`sync_type`**: `list`（普通 CRUD 同步）vs `stream`（游标分页、head_n 加载）
- **`user_scoped` + `parent`**: 多级鉴权。`user_scoped=True` 直接按 user_id 过滤；`user_scoped=False` 时通过 `parent` 级联到 user_scoped 的父实体验证归属
- **`default_not_in_filters`**: 默认在 `list()` / `list_stream()` 查询中排除指定值。用于 UI 查询去掉 SYSTEM_WAKE 等内部消息类型，避免 `head_n(50)` 全被内部消息占满。**内部队列查询需传 `skip_default_not_in=True` 绕过**
- **`serializer` / `deserializer`**: 读写钩子（如 messages 的 content JSON 解析）
- **CAS 操作**: `cas_update()` 原子更新，用于队列争抢（如 sending → sent）

### 2. Entangled（实时同步协议）

位置: `Entangled/packages/server-python/`

Gateway 继承 Entangled 的 EntityStore，通过 `_notify_change()` 在每次 CRUD 操作后自动广播变更事件。前端通过 SSE 订阅，实现：

- **增量同步**: 基于版本号的 op-log，只推送变更
- **Stream 特化**: `stream_append` / `stream_chunk` 事件支持聊天消息实时推送
- **Schema 协商**: 前端启动时获取 `/api/entangled/schema`，按 `syncContractVersion` 判断兼容性

### 3. Task Queue（任务队列 + Saga 编排）

位置: `novaic-agent-runtime/`

#### 架构角色

- **Queue Service** (19997): HTTP API 管理 tasks 和 sagas 的生命周期（创建、认领、完成、心跳）
- **Saga Worker**: 从 Queue Service 取出 saga，按 step 定义顺序发布 task
- **Task Worker**: 从 Queue Service 认领 task，执行对应 handler，返回结果

#### Worker 池划分

| 池 | 执行的 Topic |
|----|-------------|
| `control` | `saga.trigger`, `saga.decision`, `saga.parallel`（轻量编排逻辑） |
| `execution` | `llm.call`, `tool.execute`, `context.read`, `context.append`, `runtime.*` 等（实际业务） |

#### Saga 类型

| Saga | 触发条件 | 步骤 |
|------|----------|------|
| **MessageProcess** | Watchdog 发现 sending 消息 | claim → route → 判断是否需启动 Runtime → 触发 RuntimeStart |
| **RuntimeStart** | 新 Runtime 需要初始化 | init → MCP 注册 → set awake → 可选 cortex scope → 触发 ReactThink |
| **ReactThink** | Runtime 开始思考 | context.read → llm.call → context.append(响应) → decision → 触发 ReactActions |
| **ReactActions** | 有 tool_calls 需执行 | parallel(tool.execute×N) → save results → check new messages → 可能循环回 ReactThink |

#### 幂等性

- 每个 task 有 `idempotency_key`，通过 `tq_idempotency_ledger` 表防重复
- Saga 通过 `message_id` 作为幂等键，同一条消息不会创建两个 Saga

### 4. Watchdog（消息队列消费者）

位置: `novaic-agent-runtime/task_queue/watchdog_sync.py`

Watchdog 是连接 Gateway 消息表和 Task Queue 的桥梁：

```
                    Gateway DB                    Queue Service
                    ──────────                    ─────────────
                    chat_messages                 tq_sagas
                    status=sending                MessageProcess
                         │                              ▲
                         │  find_sending()               │
                         ▼  (skip_default_not_in=True)   │
                    ┌──────────┐  create saga   ┌──────────┐
                    │ Watchdog  │───────────────►│ Saga     │
                    │ (轮询)    │  confirm msg   │ Worker   │
                    └──────────┘───────────────► └──────────┘
                                 sending → sent
```

轮询间隔约 100ms。`find_sending()` 使用 `skip_default_not_in=True` 确保能看到所有类型的消息（包括 SUBAGENT_SEND 等内部类型）。

### 5. No-Tool-Warn 机制

位置: `novaic-agent-runtime/task_queue/sagas/react_think.py`

当 LLM 返回纯文本（无 tool_calls）时的纠错机制：

```
Round 1: LLM 返回纯文本（无 tool_calls）
  │
  ├─ retry_count < 1:
  │   注入合成 tool_calls:
  │     1. subagent_send(NO_TOOL_WARNING) → 创建 SUBAGENT_SEND 消息（status=sending）
  │     2. sleep(1s) → 等待
  │   ↓
  │   Watchdog confirm SUBAGENT_SEND → status=sent
  │   ↓
  │   ReactActions 完成 → 触发新的 ReactThink（Round 2）
  │   ↓
  │   context.read 获取到 warning 消息
  │   ↓
  │   LLM 看到 warning，这次应该调用 chat_reply
  │
  └─ retry_count >= 1:
      注入 subagent_rest → Agent 进入休眠
```

关键点：
- `subagent_send` 创建的消息初始状态为 `sending`
- Watchdog 的 `find_sending()` 必须能看到 SUBAGENT_SEND 类型（需要 `skip_default_not_in=True`）
- Watchdog confirm 后变为 `sent`，下一轮 `context.read` 通过 `get_unread_sent_messages` 取到 warning

### 6. LLM Factory（LLM 代理层）

位置: `novaic-llm-factory/`，部署在 `newapi.gradievo.com:19990`

统一的 LLM 调用入口，所有 Agent 的 LLM 请求都经过 Factory：

```
Runtime Worker                    LLM Factory                     LLM Provider
────────────────                  ───────────                     ────────────
FactoryLLMClient ──POST──►  /v1/chat/completions          ┌──► OpenAI API
  model=<UUID>              │                              │
  messages=[...]            ├─ resolve model (UUID→名称)   ├──► Moonshot/Kimi
  tools=[...]               ├─ load provider + API key     │
  max_tokens=4096           ├─ RetryExecutor               ├──► Anthropic
  x_factory={user_id,       │   ├─ 指数退避 + jitter       │
    agent_id, runtime_id}   │   └─ fallback providers      └──► Google
                            └─ log to llm_factory.db
```

特性：
- **模型解析**: 前端配置的是 UUID，Factory 解析为实际 provider + model_name
- **重试**: `RetryExecutor` 支持指数退避、可重试错误判断（429/5xx）、fallback 到备选 provider
- **Provider 适配**: OpenAI / Anthropic / Google 不同的 tool_choice 映射（`required` → Anthropic `any` / Google `ANY`）
- **调用日志**: 完整记录 request/response body、token 用量、耗时

---

## 消息处理全流程

用户发送一条消息到 Agent 回复的完整链路：

```
用户操作                           Gateway                          Queue System
────────                           ───────                          ────────────

1. 用户发送消息
   POST /api/agents/:id/chat
          │
          ▼
2. Gateway 创建 chat_message
   type=USER_MESSAGE
   status=sending
   ↓ Entangled 广播
   前端立即看到消息气泡
          │
          ▼
3. Watchdog 轮询 find_sending()  ─────────────────────────────────►  4. 创建 MessageProcess Saga
   发现 sending 消息                                                     │
   confirm → sending→sent                                               ▼
                                                                    5. claim + route_message
                                                                       → 获取/创建 Runtime
                                                                         │
                                                                         ▼
                                                                    6. RuntimeStart Saga
                                                                       init → MCP → awake
                                                                         │
                                                                         ▼
                                                                    7. ReactThink Saga
                                                                       ├─ context.read（获取历史+新消息）
                                                                       ├─ llm.call（通过 Factory）
                                                                       ├─ context.append（保存 LLM 响应）
                                                                       └─ decision（提取 tool_calls）
                                                                         │
                                                                         ▼
                                                                    8. ReactActions Saga
                                                                       ├─ parallel: tool.execute × N
                                                                       │   └─ chat_reply → Tools Server
                                                                       │       → POST /internal/.../chat/event
                                                                       │         type=AGENT_REPLY
                                                                       ├─ save results to context
                                                                       └─ check_new_messages
                                                                         │
          ┌───────────────────────────────────────────────────────────────┘
          ▼
9. Gateway 创建 AGENT_REPLY
   chat_message
   ↓ Entangled stream_append 广播
   前端显示 Agent 回复
```

---

## 部署架构

### 服务器

| 主机 | 域名 | 角色 |
|------|------|------|
| api.gradievo.com | api.gradievo.com | 主服务器：Gateway + Runtime + Queue + Workers |
| newapi.gradievo.com | newapi.gradievo.com | LLM Factory |
| relay.gradievo.com | relay.gradievo.com | QUIC Relay + 前端静态资源 |

### 部署命令

```bash
./deploy services    # 部署全部后端到 api.gradievo.com（rsync + start.sh 重启）
./deploy gateway     # 仅 Gateway + Entangled
./deploy factory     # LLM Factory 到 newapi.gradievo.com
./deploy frontend    # 前端 OTA 到 relay
./deploy relay       # QUIC 服务到 relay
./deploy all         # 全部
```

### 目录结构（服务器端）

```
/opt/novaic/
├── services/
│   ├── novaic-gateway/
│   ├── novaic-agent-runtime/
│   ├── novaic-runtime-orchestrator/
│   ├── novaic-tools-server/
│   ├── novaic-storage-a/
│   ├── novaic-cortex/
│   ├── novaic-shared-kernel/
│   ├── novaic-shared-runtime-common/
│   └── Entangled/
├── data/
│   ├── gateway.db
│   ├── queue.db
│   └── logs/
│       ├── gateway-YYYYMMDD.log
│       ├── watchdog-YYYYMMDD.log
│       ├── saga-worker-{1,2}.log
│       ├── task-worker-{control,execution}-{1,2}.log
│       ├── scheduler.log
│       └── health.log
└── start.sh          # 进程管理脚本
```

---

## 代码仓库结构

```
new-build-novaic/
├── novaic-gateway/           # Gateway 主服务
│   ├── gateway/
│   │   ├── api/              # REST 路由（公开 + internal）
│   │   ├── entity/           # EntityDef 定义 + EntityStore
│   │   │   ├── store.py      # EntityStore 引擎
│   │   │   ├── defs_stream.py   # messages, execution_logs（Stream 类型）
│   │   │   ├── defs_lazy.py     # agents, skills 等（List 类型）
│   │   │   └── ...
│   │   └── db/               # SQLite 初始化 + Repository
│   │       └── repositories/
│   │           └── message.py   # find_sending, confirm_message 等
│   ├── common/               # 共享工具
│   └── main_gateway.py       # 入口
│
├── novaic-agent-runtime/     # 运行时 + 任务系统
│   ├── task_queue/
│   │   ├── handlers/         # 按 topic 注册的 handler
│   │   │   ├── context_handlers.py   # context.read / append
│   │   │   ├── llm_handlers.py       # llm.call
│   │   │   ├── tool_handlers.py      # tool.execute
│   │   │   └── ...
│   │   ├── sagas/            # Saga 定义
│   │   │   ├── message_process.py    # 消息处理 Saga
│   │   │   ├── runtime_start.py      # Runtime 启动 Saga
│   │   │   ├── react_think.py        # ReAct Think（LLM 调用）
│   │   │   └── react_actions.py      # ReAct Actions（工具执行）
│   │   ├── factory_client.py         # LLM Factory 客户端
│   │   ├── topics.py                 # Task Topic 枚举
│   │   └── utils/
│   │       ├── trs_client.py         # context 消息展开（result_id → content）
│   │       ├── context.py            # sanitize_context（LLM 发送前清洗）
│   │       └── system_prompt.py      # 系统 prompt + NO_TOOL_WARNING
│   ├── queue_service/        # Queue Service HTTP 服务
│   ├── watchdog_sync.py      # Watchdog 主循环
│   └── main_novaic.py        # 统一入口（多模式启动）
│
├── novaic-runtime-orchestrator/   # Runtime 编排器
├── novaic-tools-server/           # 工具执行服务
├── novaic-llm-factory/            # LLM 代理
│   └── factory/
│       ├── routes/chat_routes.py  # /v1/chat/completions
│       ├── providers.py           # OpenAI/Anthropic/Google Provider
│       ├── retry.py               # RetryExecutor
│       └── db.py                  # llm_factory.db
│
├── novaic-cortex/            # Agent 工作区
├── novaic-storage-a/         # 文件服务
├── novaic-shared-kernel/     # 共享核心库
├── novaic-shared-runtime-common/  # 共享运行时库
├── Entangled/                # 实时同步协议
├── novaic-app/               # 前端（Tauri + React）
├── novaic-quic-service/      # QUIC Relay（Rust）
├── deploy                    # 统一部署脚本
└── docs/                     # 文档
```

---

## 常见排查路径

### Agent 不回复消息

1. **检查 sending 队列**: `SELECT * FROM chat_messages WHERE status='sending'`
2. **Watchdog 日志**: 是否找到消息？ → 检查 `find_sending()` 是否被 `default_not_in_filters` 过滤
3. **Saga 创建**: watchdog log 中是否有 "Created MessageProcess Saga"
4. **LLM 调用**: task-worker-execution log 中是否有 Factory POST，是否返回 200
5. **tool_calls**: LLM 是否返回了 tool_calls？ → 检查 Factory DB 的 `finish_reason`
6. **no-tool-warn**: 如果 LLM 无 tool_calls，检查 SUBAGENT_SEND 是否被 watchdog confirm 成 sent
7. **chat_reply**: 最终是否执行了 chat_reply → 检查是否有 AGENT_REPLY 消息

### LLM 调用失败

1. **Factory 健康**: `curl newapi.gradievo.com:19990/health`
2. **模型配置**: Gateway DB 中 model UUID 是否正确映射
3. **API Key**: Factory DB 中 key 是否有余额
4. **Factory 日志**: `llm_logs` 表查看 error 字段

### 消息被过滤

EntityStore 的 `default_not_in_filters` 会在 `list()` / `list_stream()` 中自动排除指定类型。内部队列查询（如 watchdog `find_sending`）必须传 `skip_default_not_in=True`。

---

## V2 架构演进：Sandbox-first + Cortex 统一入口

> **核心决策：**
> 1. **除技能控制外，所有工具在 Sandbox 内作为 CLI 执行** — LLM 的 tool list 极简（shell + skill_begin + skill_end）
> 2. **Cortex 是 agent 的唯一 API 入口** — Sandbox CLI 只认 Cortex，Cortex 代理转发业务调用到 Gateway
> 3. **Scope 对 agent 不可见** — Agent 只知道"技能"，scope 是 Cortex 内部实现
> 4. **Tools Server 退役** — 路由消失，业务逻辑回归 Gateway /internal/，MCP 内嵌 Worker

### 变更动机

1. **Tools Server 是多余代理层** — 80+ built-in tools 只是 Worker → ToolsServer → Gateway 的无逻辑转发
2. **结构化 tool call 太多降低 LLM 灵活性** — Agent 本质上在"操作一台电脑"，shell 是最自然的接口
3. **Cortex 有独立的领域边界** — 文件系统、执行沙箱、记忆管理是完整的认知基础设施，值得独立服务
4. **Sandbox 需要统一 API** — CLI 只能认一个地址，Cortex 做统一入口最干净

### V2 目标架构

```
                              用户
                               │
                               ▼
┌─────────────┐  SSE/REST  ┌───────────────────────────────────────┐
│  novaic-app  │◄──────────►│            Gateway :19999             │
│  (Tauri/Web) │            │                                       │
└─────────────┘             │  Auth(用户JWT) + DB + Entangled       │
                            │  /api/*      用户侧 API              │
                            │  /internal/* 业务 API (memory,chat..) │
                            │                                       │
                            └──┬───────────────────────────────▲────┘
                               │                               │
              ┌────────────────┼───────────────┐               │ Cortex 代理
              ▼                ▼                ▼               │ 业务调用
     ┌──────────────┐ ┌──────────────┐  ┌──────┴────────────────────────────┐
     │ Runtime Orch  │ │ Queue Service │  │          Cortex :19996            │
     │ :19993        │ │ :19997        │  │                                  │
     └──────────────┘ └───────┬───────┘  │  Agent 的唯一 API 入口            │
                              │          │                                  │
            ┌─────────────────┤          │  认知操作 (自己处理):             │
            │                 │          │    /v1/read, write, ls           │
            ▼                 ▼          │    /v1/scope/create, end         │
      ┌───────────┐  ┌──────────────┐   │    /v1/skill/begin, end, list   │
      │ Watchdog   │  │ Saga Workers │   │    /v1/shell → Sandbox          │
      └───────────┘  └──────┬───────┘   │    /v1/recall, tools             │
                            │           │                                  │
                     ┌──────▼────────┐  │  业务代理 (转发 Gateway):        │
                     │ Task Workers   │  │    /v1/proxy/chat               │
                     │   (3 tools)    │  │    /v1/proxy/search              │
                     │                │  │    /v1/proxy/memory              │
                     │  shell ────────┼──►   /v1/proxy/browser             │
                     │  skill_begin ──┼──►   /v1/proxy/screenshot          │
                     │  skill_end ────┼──►   /v1/proxy/notebook            │
                     │                │  │    /v1/proxy/task                │
                     │  Cortex Bridge │  │    /v1/proxy/mcp                │
                     │  MCP Client    │  │                                  │
                     └────────┬───────┘  │  Capability JWT (自签自验)       │
                              │          └──────────────┬───────────────────┘
                    ┌─────────▼──────────┐              │
                    │   LLM Factory      │              │ Sandbox.exec()
                    │   :19990           │              ▼
                    └────────────────────┘  ┌────────────────────────────────┐
                                           │  Sandbox (disposable, per exec) │
                                           │                                │
                                           │  $RO, $RW    ← S3 同步         │
                                           │  $NOVAIC_TOKEN ← Cortex 签发   │
                                           │  $NOVAIC_API   → Cortex :19996 │
                                           │                                │
                                           │  novaic chat "hello"      ─┐   │
                                           │  novaic search "JWT"       │   │
                                           │  novaic memory save k v    │→ 全│
                                           │  novaic browser nav url    │  部│
                                           │  novaic screenshot         │  经│
                                           │  novaic read /ro/...       │ Cor│
                                           │  novaic write /rw/...      │ tex│
                                           │  novaic recall            ─┘   │
                                           │  grep, python, curl  → 本地    │
                                           │                                │
                                           └────────────────────────────────┘
```

### LLM Tool List（极简 3 Tool）

Agent 只看到 **3 个结构化 tool**，其他一切在 shell 里完成：

```json
[
  {
    "name": "shell",
    "description": "在 Sandbox 中执行命令。所有操作通过 novaic CLI 完成。",
    "parameters": {"command": {"type": "string"}}
  },
  {
    "name": "skill_begin",
    "description": "开始一个技能。返回 instance_id，用于 skill_end。",
    "parameters": {"name": {"type": "string"}}
  },
  {
    "name": "skill_end",
    "description": "结束技能并提交报告。触发归档和记忆压缩。",
    "parameters": {"instance_id": {"type": "string"}, "report": {"type": "string"}}
  }
]
```

**Skill 生命周期：**

```
skill_begin("web-dev")
  → 返回 instance_id: "sk_abc123"（注入 agent context，下轮 LLM 可见）
  → 内部：自动创建 scope + 加载 SKILL.md + 注册工具

skill_end("sk_abc123", "JWT 问题已解决")
  → 校验：instance_id 存在 + LIFO 栈顶（无活跃子技能）
  → 校验通过 → { ok: true }，归档 scope + 记忆压缩 + 卸载
  → 校验失败 → { ok: false, warning: "..." }，技能保持活跃
```

**skill_end 校验失败是正常工具结果（不是异常）：** LLM 看到 warning 后会先关闭子技能再重试。

**嵌套：** 技能可以嵌套，LIFO 关闭（子先关）。Agent 只看到 instance_id 栈，不知道底层有 scope 树。

**为什么 skill_begin/end 不进 Sandbox：** 它们改变 agent 的运行状态（system prompt、tool 列表），Worker 需要在下一轮 LLM 调用前感知变化。

**Scope 对 agent 完全不可见：** 根 scope 由 Worker 自动创建/关闭，技能 scope 由 skill_begin/end 隐式管理。Agent 不需要知道 "scope" 这个概念。

### Agent 在 Sandbox 里的典型操作

```bash
# 回复用户
novaic chat "我找到了问题所在，是 JWT 过期导致的"

# 搜索
novaic search "JWT refresh token best practices" | jq '.results[:3]'

# 读写工作区
novaic read /ro/scopes/task-001/summary.md
novaic write /rw/scratch/findings.md "JWT 需要刷新机制"

# 记忆
novaic memory save auth_pattern "use short-lived JWT with refresh"
novaic memory recall auth

# 浏览器
novaic browser navigate https://docs.example.com/auth
novaic screenshot

# 组合操作
novaic search "error handling" | jq -r '.results[0].url' | xargs novaic browser navigate
novaic read /ro/scopes/_index.jsonl | jq -r 'select(.depth==0) | .name'

# 原生 shell
grep -rl "JWT" $RO/scopes/ | head -5
python3 $RW/analyze.py
curl -s https://api.example.com/status | jq .
```

### 组件职责边界

#### Gateway :19999 — "前台"

| 做 | 不做 |
|---|---|
| 用户认证 (签发/验证 **用户 JWT**) | Tool 调度 |
| DB CRUD (chat, memory, notebook, task) | S3 / Sandbox |
| 用户侧 HTTP API + Entangled 实时同步 | LLM 调用 |
| 业务 /internal/ API (供 Cortex 代理调用) | Capability JWT |
| 设备代理 (vmcontrol 转发) | |

Gateway 保持 **API + DB + Auth**，不碰 S3 和 Sandbox。Cortex 代理业务调用时，Gateway 视 Cortex 为可信内部调用方。

#### Cortex :19996 — "Agent 的操作系统"

| 做 | 不做 |
|---|---|
| **Agent 唯一 API 入口** | 用户认证 (用户 JWT) |
| Workspace (/ro + /rw on S3) | DB 直接操作 |
| Sandbox 一次性执行 | LLM 调用 |
| Compactor (记忆压缩 + Gem Fusion) | |
| Recall (system prompt 注入) | |
| Tool Definitions (文件化声明) | |
| **签发 + 验证 Capability JWT** | |
| **代理转发业务调用到 Gateway** | |

Cortex HTTP API：

```
── 认知操作（Cortex 自己处理）──
GET  /v1/read?path=              → Workspace.read()
POST /v1/write                   → Workspace.write()
GET  /v1/ls?path=                → Workspace.list_dir()
POST /v1/skill/begin             → 创建 scope + 加载 skill → 返回 instance_id
POST /v1/skill/end               → 归档 scope + 记忆压缩 + 卸载 skill
GET  /v1/skill/list              → list available skills
POST /v1/shell                   → Sandbox.exec()
GET  /v1/recall                  → Recall.generate()
GET  /v1/tools                   → load_tool_schemas()
POST /v1/token                   → 签发 Capability JWT (内部)

── 内部 Scope 管理（Worker 自动调用，agent 不可见）──
POST /v1/scope/create            → 创建根 scope (任务开始时)
POST /v1/scope/end               → 关闭根 scope (任务结束时)

── 业务代理（Cortex 转发到 Gateway）──
POST /v1/proxy/chat              → Gateway /internal/.../chat/event
POST /v1/proxy/search            → Gateway /internal/.../search
POST /v1/proxy/memory            → Gateway /internal/.../memory
POST /v1/proxy/notebook          → Gateway /internal/.../notebook
POST /v1/proxy/task              → Gateway /internal/.../tasks
POST /v1/proxy/browser           → Gateway /internal/.../vm/browser
POST /v1/proxy/screenshot        → Gateway /internal/.../vm/screenshot
POST /v1/proxy/keyboard          → Gateway /internal/.../vm/keyboard
POST /v1/proxy/mouse             → Gateway /internal/.../vm/mouse
POST /v1/proxy/mcp               → MCP Client (内嵌 Cortex 或 Worker)
```

所有端点 Capability JWT 鉴权。代理端点从 JWT claims 提取 `user_id` + `agent_id` 构造 Gateway 内部请求。

#### Task Worker — "编排层"

| 做 | 不做 |
|---|---|
| LLM 循环编排 (think → act) | 用户 HTTP API |
| **仅 3 个 tool 的 handler** | Tool Router (不再需要) |
| 根 scope 自动管理 (创建/关闭) | 数据库直接操作 |

Worker 极度简化 — 只需处理 3 个 tool call：

```python
async def handle_tool_execute(tool_name, args, ctx):
    if tool_name == "shell":
        return await cortex_client.shell(args["command"], ctx["token"])
    elif tool_name == "skill_begin":
        result = await cortex_client.skill_begin(args["name"], ctx["token"])
        # result.instance_id 注入 agent context，下轮 LLM 可见
        return result
    elif tool_name == "skill_end":
        return await cortex_client.skill_end(
            args["instance_id"], args["report"], ctx["token"])
    else:
        raise UnknownToolError(tool_name)

# 根 scope 由 Worker 自动管理（agent 不可见）：
async def on_task_start(ctx):
    scope = await cortex_client.scope_create("root", ctx["token"])
    ctx["root_scope_id"] = scope.id

async def on_task_end(ctx):
    await cortex_client.scope_end(ctx["root_scope_id"], "task completed", ctx["token"])
```

**不再需要 Tool Router。** Agent 不知道 scope 的存在——根 scope 由 Worker 自动管理，技能 scope 由 skill_begin/end 隐式管理。

### Cortex CLI 完整命令表

Sandbox 内预装 `novaic` CLI，`$NOVAIC_API` 指向 Cortex :19996：

```
── 认知操作 ──
novaic read <path>                           读取工作区文件
novaic write <path> [content | -]            写入文件
novaic ls <path>                             列出目录
novaic recall                                获取 fuzzy memory
novaic tools                                 列出当前可用工具

── 业务操作（Cortex 代理到 Gateway）──
novaic chat <message>                        回复用户
novaic search <query>                        搜索网页
novaic memory save <key> <value>             保存记忆
novaic memory recall <key>                   检索记忆
novaic memory delete <key>                   删除记忆
novaic memory list                           列出记忆命名空间
novaic notebook write <title> <content>      写笔记
novaic notebook read <id>                    读笔记
novaic notebook list                         列出笔记
novaic task create <title>                   创建任务
novaic task complete <id>                    完成任务

── 设备操作（Cortex 代理到 Gateway → vmcontrol）──
novaic browser navigate <url>                打开网页
novaic browser content                       获取页面内容
novaic screenshot                            截图
novaic keyboard type <text>                  键盘输入
novaic mouse click <x> <y>                   鼠标点击

── MCP 外部工具 ──
novaic mcp <tool_name> [args...]             调用 MCP 工具
```

**实现：** 单个 Python 脚本（零外部依赖），`$NOVAIC_API` → Cortex :19996，`$NOVAIC_TOKEN` → Capability JWT。

### JWT 双轨制

```
Gateway (:19999)                    Cortex (:19996)
  签发: 用户 JWT                      签发: Capability JWT
  密钥: JWT_SECRET                   密钥: CORTEX_JWT_SECRET (独立)
  claims: user_id, role              claims: user_id, agent_id,
  exp: 7 天                                  scope_id, permissions
  用途: /api/* 用户请求               exp: 30 分钟
  验证方: Gateway                    用途: /v1/* Cortex API (Worker + CLI)
                                     验证方: Cortex
```

Cortex 代理转发到 Gateway 时，使用服务间信任（内部 API key 或 mTLS），不传递 Capability JWT 给 Gateway。

### Tools Server 分解路线

| 原 Tools Server 职责 | 去向 | 说明 |
|---|---|---|
| Built-in tool 路由 | **不需要** | Worker 只有 3 个 tool，无需 router |
| Built-in tool 执行 | **Cortex 代理 → Gateway /internal/** | CLI 调 Cortex，Cortex 转发 |
| MCP 外部工具 | **Cortex /v1/proxy/mcp** 或 Worker 内嵌 | CLI 调 `novaic mcp` |
| Skill 列表 | **Cortex /ro/skills/** | 文件系统 |
| Subagent MCP context | **Worker 进程内存** | 随 Worker 生命周期 |

### 消息处理全流程 (V2)

```
用户发送消息 → Gateway → Watchdog → MessageProcess Saga
  → RuntimeStart Saga
      → Worker 自动调 Cortex /v1/scope/create (根 scope, agent 不可见)
      → Worker 调 Cortex /v1/token (获取 Capability JWT)
  → ReactThink Saga
      → context.read → llm.call(tools=[shell, skill_begin, skill_end])
      → LLM 返回: skill_begin("web-dev")
  → ReactActions Saga:
      │
      ├─ tool_call: skill_begin("web-dev")
      │   → Worker → Cortex /v1/skill/begin
      │     → 内部创建技能 scope + 加载 SKILL.md
      │     → 返回 instance_id: "sk_abc123" → 注入 agent context
      │
      ├─ tool_call: shell("novaic search 'JWT auth' | jq '.results[0]'")
      │   → Worker → Cortex /v1/shell
      │     → Sandbox: novaic search → Cortex /v1/proxy/search → Gateway
      │
      ├─ tool_call: shell("novaic chat '找到了：应该用 refresh token'")
      │   → Worker → Cortex /v1/shell
      │     → Sandbox: novaic chat → Cortex /v1/proxy/chat → Gateway
      │     → Gateway AGENT_REPLY → Entangled → 前端
      │
      └─ tool_call: skill_end("sk_abc123", "JWT 问题已解决")
          → Worker → Cortex /v1/skill/end
          → 内部：归档 scope + 记忆压缩 + 卸载 skill
  → RuntimeEnd Saga
      → Worker 自动调 Cortex /v1/scope/end (关闭根 scope, agent 不可见)
```

### V1 → V2 变更汇总

| 维度 | V1 | V2 |
|------|----|----|
| **LLM tool 数量** | 10+ 个结构化 tool | **3 个** (shell + skill_begin + skill_end) |
| **Agent 执行模型** | 结构化 tool call 为主 | **Shell-first (novaic CLI)** |
| **Scope** | Agent 显式管理 | **Agent 不可见** (内部自动管理) |
| **Tool 调用链** | Worker → ToolsServer → Gateway (3 跳) | Worker → Cortex → (自处理 \| 代理 Gateway) |
| **Cortex 角色** | Python library (嵌入 Worker) | **独立 HTTP 服务 + Agent 唯一 API 入口** |
| **Gateway** | API + DB + Auth | 不变（不膨胀） |
| **Worker 复杂度** | Tool Router + 80 tool 分类 | **3 个 handler + 自动 scope 管理** |
| **Sandbox** | 仅 shell 命令用 | **所有业务操作都在 Sandbox 内** |
| **Sandbox 鉴权** | 无 | Capability JWT (Cortex 自签自验) |
| **CLI** | 仅认知原语 | **完整：认知 + 业务 + 设备 + MCP** |
| **JWT** | Gateway 统一签发 | 双轨：Gateway 签用户 JWT，Cortex 签 capability JWT |

### 服务清单 (V2)

| 服务 | 端口 | 变化 | 职责 |
|------|------|------|------|
| **Gateway** | 19999 | 不变 | API + DB + Auth(用户JWT) + Entangled + 业务 /internal/ |
| **Cortex** | 19996 | **新增** | Agent 唯一 API：认知(自处理) + 业务(代理Gateway) + JWT |
| **Runtime Orchestrator** | 19993 | 不变 | Runtime 生命周期 |
| **Queue Service** | 19997 | 不变 | 任务队列 + Saga |
| **File Service** | 19995 | 不变 | 文件上传/下载 |
| **LLM Factory** | 19990 | 不变 | LLM 代理 |
| **Task Workers** | — | **极简化** (3 tool handler) | shell / skill_begin / skill_end → Cortex |
| ~~**Tools Server**~~ | ~~19998~~ | **退役** | ~~分解到 Cortex 代理 + CLI~~ |

### 部署目录 (V2)

```
/opt/novaic/
├── services/
│   ├── novaic-gateway/              ← 不变
│   ├── novaic-agent-runtime/        ← 极简化（去掉 Tool Router）
│   ├── novaic-runtime-orchestrator/
│   ├── novaic-cortex/               ← ★ 独立 HTTP 服务 + CLI + JWT + 代理
│   ├── novaic-storage-a/
│   ├── novaic-shared-kernel/
│   ├── novaic-shared-runtime-common/
│   └── Entangled/
│   ✕── novaic-tools-server/         ← 退役删除
├── data/
└── start.sh
```
