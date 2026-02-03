# NovAIC 系统架构 (v17)

## 总体架构

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Tauri Desktop App                                   │
│  (负责启动所有进程、管理生命周期、提供前端 UI)                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌───────────────────┐   ┌───────────────────────────┐   ┌───────────────────────┐
│     Gateway       │   │       MCP Gateway         │   │     Service Workers   │
│    (19999)        │   │        (19998)            │   │                       │
├───────────────────┤   ├───────────────────────────┤   ├───────────────────────┤
│ • REST API        │   │ • MCPManager              │   │ • Launcher Service    │
│ • SQLite DB       │   │ • Agent Shared MCP        │   │ • Collector Service   │
│ • Internal API    │   │ • Runtime MCP             │   │ • Async Service       │
│ • SSE Events      │   │ • Aggregate Gateway       │   │ • Health Service      │
│ • VM Management   │   │ • Tool Discovery          │   │                       │
└───────────────────┘   └───────────────────────────┘   └───────────────────────┘
        │                               │                       │
        └───────────────────────────────┴───────────────────────┘
                                        │
                            ┌───────────┴───────────┐
                            │     SQLite Database   │
                            │  (pipeline_tasks,     │
                            │   subagents, runtimes,│
                            │   agents, messages)   │
                            └───────────────────────┘
```

## 仓库结构

```
novaic/
├── novaic-app/          # Tauri 桌面应用
│   ├── src/             # React 前端
│   └── src-tauri/       # Rust 后端 (进程管理)
│
├── novaic-gateway/      # 核心后端服务
│   ├── api/             # REST API 路由
│   ├── db/              # 数据库 schema + repositories
│   ├── services/        # Three-Task Services
│   ├── mcp_servers/     # Runtime MCP 定义
│   ├── mcp_gateway/     # Aggregate Gateway
│   ├── sdk/             # Gateway Client SDK
│   ├── worker/          # 执行器 (think, tool_call)
│   └── *_main.py        # 各服务入口
│
├── novaic-vm/           # VM 管理 + MCP 工具服务
│   ├── src/novaic_mcp_vmuse/
│   │   └── tools/       # browser, desktop, shell...
│   └── scripts/         # VM 管理脚本 (create, start, stop...)
│
└── dev-guide/           # 开发文档
```

## 进程模型

Tauri 负责启动 6 个独立进程：

| 进程 | 入口 | 端口 | 职责 |
|------|------|------|------|
| **Gateway** | `main.py` | 19999 | REST API、SQLite、SSE、VM 管理 |
| **MCP Gateway** | `mcp_main.py` | 19998 | MCP 服务管理、Aggregate Gateway |
| **Launcher** | `launcher_main.py` | - | 处理 launcher 任务 |
| **Collector** | `collector_main.py` | - | 处理 collector 任务 |
| **Async** | `async_main.py` | - | 处理 async 任务 (think, tool_call) |
| **Health** | `health_main.py` | - | 健康检查、超时回收 |

```bash
# Tauri 启动顺序
1. Gateway (先启动，提供 DB 和 API)
2. MCP Gateway (依赖 Gateway URL)
3. Launcher Service (依赖 Gateway URL)
4. Collector Service (依赖 Gateway URL)
5. Async Service (依赖 Gateway URL)
6. Health Service (依赖 Gateway URL)
```

## Three-Task Architecture

### 核心概念

所有业务逻辑通过三种任务类型协作完成：

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Launcher   │ ───► │    Async    │ ───► │  Collector  │
│  (准备逻辑)  │      │  (纯执行)    │      │  (后处理)   │
└─────────────┘      └─────────────┘      └─────────────┘
      │                                          │
      │              下一阶段                      │
      └────────────────────────────────────────►┘
```

| 任务类型 | 职责 | 特点 |
|---------|------|------|
| **Launcher** | 准备逻辑 + 创建 async 任务 + 创建 collector | 幂等、可重入 |
| **Async** | 纯执行（LLM 调用、MCP 工具） | 无状态、可并行 |
| **Collector** | 等待 async 完成 + 后处理 + 触发下一个 launcher | 幂等、原子 |

### Stage 流转

一个完整的 Agent 对话循环：

```
用户发消息
     │
     ▼
┌─────────────┐     ┌─────────────┐
│  monitor    │ ──► │  monitor    │ ── 检测消息，唤醒 SubAgent
│  _launcher  │     │  _collector │
└─────────────┘     └─────────────┘
                           │
                           ▼
┌─────────────┐     ┌─────────────┐
│  runtime    │ ──► │  runtime    │ ── 创建 Runtime + MCP 服务
│  _launcher  │     │  _collector │
└─────────────┘     └─────────────┘
                           │
                           ▼
┌─────────────┐     ┌───────────┐     ┌─────────────┐
│   think     │ ──► │   async   │ ──► │   think     │ ── 调用 LLM
│  _launcher  │     │  (think)  │     │  _collector │
└─────────────┘     └───────────┘     └─────────────┘
                                             │
              ┌──────────────────────────────┘
              │ (如果有 tool_call)
              ▼
┌─────────────┐     ┌───────────┐     ┌─────────────┐
│  actions    │ ──► │   async   │ ──► │  actions    │ ── 执行 MCP 工具
│  _launcher  │     │(tool_call)│     │  _collector │
└─────────────┘     └───────────┘     └─────────────┘
                                             │
              ┌──────────────────────────────┘
              │ (如果 LLM 返回 done)
              ▼
┌─────────────┐     ┌───────────┐     ┌─────────────┐
│ summarize   │ ──► │   async   │ ──► │ summarize   │ ── 生成总结
│  _launcher  │     │(summarize)│     │  _collector │
└─────────────┘     └───────────┘     └─────────────┘
                                             │
                                             ▼
                                     SubAgent → sleeping
```

### pipeline_tasks 表

```sql
CREATE TABLE pipeline_tasks (
    id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,        -- launcher, collector, async
    task_subtype TEXT NOT NULL,     -- monitor_launcher, think, tool_call...
    
    runtime_id TEXT NOT NULL,       -- Runtime 标识
    stage_id TEXT NOT NULL,         -- Stage 标识 (一组任务)
    agent_id TEXT NOT NULL,
    
    status TEXT DEFAULT 'pending',  -- pending, executing, done, failed
    args TEXT DEFAULT '{}',         -- JSON: 任务参数
    result TEXT,                    -- JSON: 执行结果
    
    -- Collector 专用
    expected_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    
    -- Claim 机制
    claimed_by TEXT,
    claimed_at TEXT,
    heartbeat_at TEXT,
    
    -- 幂等性
    idempotency_key TEXT UNIQUE,
    
    created_at TEXT,
    updated_at TEXT
);
```

## 通信关系

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Frontend (Tauri UI)                             │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        Gateway (19999)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  /api/*           REST API (Agents, Messages, Sessions)              │ │
│  │  /internal/*      内部 API (Services 使用)                            │ │
│  │  /mcp/*           MCP 代理 (转发到 MCP Gateway)                       │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
         │                              │
         │ HTTP /internal/*             │ HTTP /mcp/*
         ▼                              ▼
┌─────────────────────┐     ┌──────────────────────────────────────────────┐
│  Service Workers    │     │              MCP Gateway (19998)              │
│  ┌───────────────┐  │     │  ┌────────────────────────────────────────┐  │
│  │ Launcher      │  │     │  │  Agent Shared MCP (local, memory, vm)  │  │
│  │ Collector     │  │     │  │  Runtime MCP (per-runtime)             │  │
│  │ Async         │  │     │  │  Aggregate Gateway (聚合多个 MCP)       │  │
│  │ Health        │  │     │  └────────────────────────────────────────┘  │
│  └───────────────┘  │     └──────────────────────────────────────────────┘
└─────────────────────┘
```

### 关键原则

1. **Services 只与 Gateway 通信** - 所有 DB 操作通过 Gateway Internal API
2. **MCP 管理通过 Gateway 代理** - Gateway 转发到 MCP Gateway
3. **MCP 工具直接调用** - Async Worker 直接调用 MCP Gateway 执行工具

## 核心数据模型

### Agent → SubAgent → Runtime 层级

```
Agent (用户创建的 AI 助手)
  │
  └── SubAgent (对话实体)
        │ • Main SubAgent (主对话)
        │ • Sub SubAgent (异步子任务)
        │
        └── Runtime (一次完整对话)
              │ • status: running → completed
              │ • phase: need_think → thinking → ...
              │
              └── MCP Server (工具能力)
                    • Runtime MCP (per-runtime)
                    • Agent Shared MCP
```

### 状态机

```
SubAgent Status:
  sleeping ──► awake ──► running ──► completed/failed ──► sleeping
     ▲                                                       │
     └───────────────────────────────────────────────────────┘

Runtime Status:
  running ──► completed/failed/cancelled
    │
    └── Phase: need_think → thinking → waiting_actions
                                            → completed
                                            → need_think (下一轮)
```

## MCP 服务架构

```
┌────────────────────────────────────────────────────────────────────┐
│                       MCP Gateway (19998)                          │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Agent Shared MCP (per-agent, 所有 Runtime 共享)                    │
│  ├── local MCP        - 文件系统操作                                │
│  ├── memory MCP       - 记忆存储                                   │
│  └── vmuse MCP        - VM 工具 (browser, desktop, shell)          │
│                                                                    │
│  Runtime MCP (per-runtime)                                         │
│  ├── subagent_spawn   - 启动子 Agent                               │
│  ├── subagent_query   - 查询子 Agent 状态                          │
│  ├── subagent_cancel  - 取消子 Agent                               │
│  ├── context_request  - 请求更多上下文                              │
│  └── ...                                                           │
│                                                                    │
│  Aggregate Gateway (聚合入口)                                       │
│  └── /aggregate/{agent_id}/{runtime_id}                            │
│      └── 合并 Agent Shared + Runtime MCP 的所有工具                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## 目录结构详解

### novaic-gateway/services/

```
services/
├── base.py                 # TaskWorker 基类
├── gateway_client.py       # Gateway API 客户端
│
├── launcher_worker.py      # Launcher 任务处理器
├── launchers/              # Launcher 实现
│   ├── monitor.py          #   检测消息，唤醒 SubAgent
│   ├── runtime.py          #   创建 Runtime + MCP
│   ├── think.py            #   准备 LLM 上下文
│   ├── actions.py          #   准备 tool_call 任务
│   └── summarize.py        #   准备 summary 任务
│
├── collector_worker.py     # Collector 任务处理器
├── collectors/             # Collector 实现
│   ├── monitor.py          #   触发 runtime_launcher
│   ├── runtime.py          #   触发 think_launcher
│   ├── think.py            #   处理 LLM 结果，触发 actions/summarize
│   ├── actions.py          #   收集工具结果，触发 think/summarize
│   └── summarize.py        #   完成对话，设置 SubAgent sleeping
│
├── async_worker.py         # Async 任务处理器
└── executors/              # Async 执行器
    ├── think.py            #   调用 LLM
    ├── tool_call.py        #   调用 MCP 工具
    └── summarize.py        #   生成对话总结
```

## 端口分配

| 端口 | 服务 | 说明 |
|------|------|------|
| 19999 | Gateway | REST API + Internal API |
| 19998 | MCP Gateway | MCP 服务管理 |
| 20000+ | VM SSH | 动态分配 |
| 20005+ | VM VNC | 动态分配 |
