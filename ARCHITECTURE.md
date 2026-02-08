# NovAIC 系统架构全景

**版本**: v2.0  
**更新时间**: 2026-02-08  
**架构类型**: Master-Driven + Saga/Task 分布式架构

---

## 📋 目录

- [系统概览](#系统概览)
- [核心服务](#核心服务)
- [Task Queue 架构](#task-queue-架构)
- [数据流](#数据流)
- [技术栈](#技术栈)
- [部署架构](#部署架构)

---

## 🎯 系统概览

### 架构设计理念

NovAIC 是一个基于 **Master-Driven + Saga/Task 三层架构** 的分布式 AI Agent 系统：

- **Master-Driven**: Gateway 作为协调中心，不直接执行任务
- **Saga 编排**: 复杂业务流程通过 Saga 拆分为多个原子步骤
- **Task 执行**: 幂等的原子操作，支持重试和恢复
- **微服务**: 服务间通过 HTTP REST 解耦，独立部署和扩展

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Tauri Desktop App                           │
│                      (Electron-like Desktop)                        │
└────────────────┬───────────────────────────────────┬────────────────┘
                 │                                   │
                 │ HTTP REST + SSE                  │ Tauri Commands
                 │                                   │
┌────────────────▼───────────────────────────────────▼────────────────┐
│                          Frontend Layer                             │
│  • React UI                                                          │
│  • SSE Event Listener                                               │
│  • WebSocket VNC Client                                             │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 │ HTTP REST + SSE
                 │
┌────────────────▼────────────────────────────────────────────────────┐
│                         Backend Services                             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Gateway    │  │ Queue Service│  │ Tools Server │             │
│  │  (端口 19999) │  │  (端口 19997) │  │  (端口 19998) │             │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤             │
│  │• 业务 API     │  │• TaskQueue   │  │• 67 工具     │             │
│  │• Runtime管理  │  │• SagaRepo    │  │• MCP 集成    │             │
│  │• SubAgent    │  │• FIFO Lock   │  │• VMUSE       │             │
│  │• Chat消息    │  │• 任务分发     │  │• 工具执行    │             │
│  │• SSE 推送    │  │• 恢复机制     │  │• 持久化     │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                  │                      │
│         ▼                 ▼                  ▼                      │
│  ┌──────────┐      ┌──────────┐      ┌──────────────┐             │
│  │novaic.db │      │queue.db  │      │ Gateway API  │             │
│  │ 2.2 MB   │      │  68 KB   │      │ (内部调用)   │             │
│  └──────────┘      └──────────┘      └──────────────┘             │
│         ▲                 ▲                                         │
│         │                 │                                         │
│         └─────┬───────────┤                                         │
│               │           │                                         │
│         ┌─────▼───────────▼─────┐                                  │
│         │   Worker 进程集群       │                                  │
│         ├────────────────────────┤                                  │
│         │• TaskWorker (2进程)    │ ← Queue Service                 │
│         │• SagaWorker (1进程)    │ ← Queue Service                 │
│         │• HealthWorker          │ ← Queue Service                 │
│         │• Watchdog              │ ← Gateway                       │
│         └────────────────────────┘                                  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ HTTP REST + Unix Socket
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│                      VMControl Service (Rust)                        │
│                         (端口 8080)                                  │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  • QEMU 虚拟机管理                                           │    │
│  │  • QMP 协议 (VM 生命周期控制)                                 │    │
│  │  • Guest Agent 协议 (VM 内部操作)                            │    │
│  │  • VNC WebSocket 代理 (屏幕显示)                             │    │
│  │  • 键盘/鼠标输入控制                                          │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ▼                                       │
│                    /tmp/novaic/*.sock                                │
│              (QMP/Guest Agent/VNC Unix Sockets)                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ 核心服务

### 1. Gateway Service (端口 19999)

**定位**: 系统 API 网关和状态管理中心

#### 技术栈
- Python 3.11+
- FastAPI + Uvicorn
- SQLite (novaic.db)
- asyncio + aiohttp

#### 核心职责

| 模块 | 功能 | 关键实现 |
|------|------|---------|
| **API 网关** | REST API 接口 | `gateway/api/routes.py` |
| **Internal API** | 供 Workers/Tools 调用 | `gateway/api/internal/` |
| **Runtime 管理** | Runtime 生命周期管理 | `gateway/db/repositories/runtime.py` |
| **SubAgent 管理** | SubAgent 状态机 | `gateway/db/repositories/subagent.py` |
| **消息处理** | Chat 消息持久化 | `gateway/db/repositories/message.py` |
| **SSE 广播** | 实时事件推送 | `gateway/sse/broadcaster.py` |
| **LLM 客户端** | 多提供商 LLM 调用 | `gateway/core/llm_client.py` |
| **VM 管理** | QEMU VM 编排 | `gateway/vm/manager.py` |
| **Memory 存储** | 键值对存储 | `gateway/db/repositories/memory.py` |
| **Goal 管理** | 目标追踪 | `gateway/db/repositories/goal.py` |

#### 数据模型 (Schema v25)

```sql
-- Agent 配置
agents (id, name, vm_config, ports, model_id, setup_complete)

-- Runtime 实例 (v12 Master-driven)
agent_runtimes (
    runtime_id,           -- Runtime 唯一 ID
    subagent_id,          -- 所属 SubAgent
    agent_id,             -- 所属 Agent
    status,               -- active/resting/completed
    phase,                -- need_think/waiting_actions/completed
    context,              -- JSON 对话历史
    summary,              -- 完整摘要
    hot_summary,          -- 热摘要 (v24)
    cold_summary,         -- 冷摘要 (v24)
    tool_ports,           -- Tools Server 端口 (v25)
    mcp_url               -- MCP 服务 URL
)

-- SubAgent 实体 (v14)
subagents (
    subagent_id,          -- SubAgent ID
    agent_id,             -- 所属 Agent
    type,                 -- main/sub
    status,               -- sleeping/awake/running/completed
    historical_summary,   -- 历史摘要
    hrl,                  -- Hot Runtime List (JSON)
    wake_triggers,        -- 唤醒触发器
    handoff_notes         -- 交接说明
)

-- 统一消息表 (v18 事件驱动)
chat_messages (
    id,                   -- 消息 ID
    agent_id,             -- 所属 Agent
    type,                 -- user/assistant/system
    content,              -- 消息内容
    status,               -- sending/sent
    read,                 -- 0=unread, 1=read
    metadata              -- JSON (model, api_key_id 等)
)

-- 三任务架构 (v15)
pipeline_tasks (
    task_type,            -- launcher/collector/async
    runtime_id,
    stage_id,
    status,
    idempotency_key       -- 防重复
)

-- 内存存储
memories (namespace, key, value, agent_id, subagent_id)

-- 目标管理
goals (id, agent_id, subagent_id, description, status, progress)

-- 配置和 API Keys
config (key, value)
api_keys (id, name, provider, api_key, model_id, priority)
```

#### API 端点

**公共 API (`/api/*`)**:
```
POST   /api/chat                 # 发送消息
GET    /api/history              # 获取历史
POST   /api/interrupt            # 中断执行
GET    /api/config               # 获取配置
POST   /api/config/api-keys      # 添加 API Key
GET    /api/health               # 健康检查
```

**内部 API (`/api/internal/*`)**:
```
# Runtime 管理
GET    /api/internal/runtimes/active
POST   /api/internal/runtimes
PATCH  /api/internal/runtimes/{runtime_id}
POST   /api/internal/runtimes/{runtime_id}/context/append
POST   /api/internal/runtimes/{runtime_id}/claim-phase

# Runtime-First API (供 Tools Server 调用)
GET    /api/internal/rt/{runtime_id}/memory/*
POST   /api/internal/rt/{runtime_id}/chat/*
GET    /api/internal/rt/{runtime_id}/qemu/*
POST   /api/internal/rt/{runtime_id}/tasks/*

# SubAgent 管理
GET    /api/internal/subagents/{subagent_id}
PATCH  /api/internal/subagents/{subagent_id}

# 消息管理
GET    /api/internal/messages/sending
PATCH  /api/internal/messages/{message_id}
```

---

### 2. Queue Service (端口 19997)

**定位**: 分布式任务队列和 Saga 流程编排引擎

#### 技术栈
- Python 3.11+
- FastAPI
- SQLite (queue.db, 独立数据库)
- FIFO Lock (8 分片)

#### 核心组件

```python
queue_service/
├── main.py              # FastAPI 应用入口
├── queue_db.py          # TaskQueue 核心实现 (~367 行)
├── saga_repo.py         # SagaRepository + Orchestrator (~396 行)
├── saga.py              # Saga 定义和执行器 (~610 行)
└── routes.py            # API 路由 (~377 行)
```

#### 数据库设计

**`tq_tasks` 表 - 任务队列**:
```sql
CREATE TABLE tq_tasks (
    id TEXT PRIMARY KEY,              -- task-{uuid}
    idempotency_key TEXT UNIQUE,      -- 幂等键
    topic TEXT NOT NULL,              -- 任务主题 (TaskTopics)
    payload TEXT NOT NULL,            -- JSON 参数
    status TEXT DEFAULT 'pending',    -- pending/claimed/done/failed/cancelled
    claimed_by TEXT,                  -- Worker ID
    claimed_at TEXT,
    heartbeat_at TEXT,                -- 心跳时间 (超时检测)
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    result TEXT,                      -- JSON 结果
    error TEXT,                       -- 错误信息
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    version INTEGER DEFAULT 0         -- 乐观锁
);

-- 索引
CREATE INDEX idx_tq_tasks_pending ON tq_tasks(topic, status, created_at) 
    WHERE status = 'pending';
CREATE INDEX idx_tq_tasks_heartbeat ON tq_tasks(status, heartbeat_at) 
    WHERE status = 'claimed';
```

**`tq_sagas` 表 - Saga 流程**:
```sql
CREATE TABLE tq_sagas (
    id TEXT PRIMARY KEY,              -- saga-{uuid}
    idempotency_key TEXT UNIQUE,
    saga_type TEXT NOT NULL,          -- Saga 类型名
    context TEXT NOT NULL,            -- JSON 业务上下文
    current_step INTEGER DEFAULT 0,   -- 当前步骤索引
    status TEXT DEFAULT 'pending',    -- pending/running/completed/failed/cancelled
    claimed_by TEXT,
    claimed_at TEXT,
    heartbeat_at TEXT,
    step_results TEXT DEFAULT '{}',   -- JSON: 每步的结果
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    completed_at TEXT
);

-- 索引
CREATE INDEX idx_tq_sagas_pending ON tq_sagas(status, created_at) 
    WHERE status = 'pending';
CREATE INDEX idx_tq_sagas_heartbeat ON tq_sagas(status, heartbeat_at) 
    WHERE status = 'running';
```

#### 核心机制

**1. 原子认领 (CAS)**
```python
def claim(self, topics: List[str], worker_id: str):
    """原子认领任务，使用 CAS 操作"""
    UPDATE tq_tasks 
    SET status = 'claimed',
        claimed_by = ?,
        claimed_at = ?,
        heartbeat_at = ?
    WHERE id = (
        SELECT id FROM tq_tasks 
        WHERE status = 'pending' 
          AND topic IN (...)
        ORDER BY created_at
        LIMIT 1
    )
```

**2. 心跳保活**
- Worker 每 10 秒发送一次心跳
- 超时任务自动恢复为 `pending` 状态
- HealthWorker 定期扫描超时任务

**3. 幂等性保证**
- `idempotency_key` 唯一约束
- 状态 CAS 操作
- Handler 业务逻辑幂等

**4. FIFO 锁**
- 公共库 `common/db/locks.py`
- 8 分片锁提升并发
- 按 task_id/saga_id 哈希分片

#### API 端点

**Task API**:
```
POST   /api/queue/tasks/publish      # 发布任务
POST   /api/queue/tasks/claim        # 认领任务 (CAS)
POST   /api/queue/tasks/{id}/complete # 完成任务
POST   /api/queue/tasks/{id}/fail    # 失败任务
POST   /api/queue/tasks/{id}/heartbeat # 心跳续约
GET    /api/queue/tasks/{id}         # 查询任务
GET    /api/queue/tasks/stats        # 任务统计
GET    /api/queue/topics             # 获取所有 topics
```

**Saga API**:
```
POST   /api/queue/sagas/start        # 启动 Saga
POST   /api/queue/sagas/claim        # 认领 Saga
GET    /api/queue/sagas/{id}         # 查询 Saga
POST   /api/queue/sagas/{id}/heartbeat # 心跳续约
POST   /api/queue/sagas/{id}/progress # 更新进度
POST   /api/queue/sagas/{id}/complete # 完成 Saga
POST   /api/queue/sagas/{id}/fail    # 失败 Saga
POST   /api/queue/sagas/{id}/resume  # 恢复 Saga
```

**Recovery API**:
```
POST   /api/queue/recover/tasks      # 恢复超时任务
POST   /api/queue/recover/sagas      # 恢复超时 Saga
POST   /api/queue/recover/all        # 恢复所有
POST   /api/queue/recover/cancel-all # 取消所有任务/Saga
```

---

### 3. Tools Server (端口 19998)

**定位**: 统一工具执行服务，支持内置工具和外部 MCP 工具

#### 技术栈
- Python 3.11+
- FastAPI
- httpx (HTTP 客户端)
- MCP Client (外部工具)

#### 架构组件

```python
tools_server/
├── api.py              # FastAPI 路由和 HTTP API
├── executor.py         # 工具执行器 (内置+外部路由)
├── runtime_manager.py  # Runtime 上下文管理器
└── tools.py            # 67 个内置工具定义
```

#### 工具分类 (共 67 个)

| 分类 | 数量 | 工具列表 |
|------|------|---------|
| **Memory** | 10 | `memory_save`, `memory_recall`, `memory_delete`, `memory_list_namespaces`, `task_log`, `task_history`, `goal_set`, `goal_progress`, `goal_complete`, `session_state` |
| **Runtime** | 7 | `runtime_list`, `runtime_history`, `runtime_send`, `runtime_rest`, `subagent_spawn`, `subagent_query`, `subagent_cancel` |
| **Chat** | 6 | `chat_reply`, `chat_ask`, `chat_notify`, `chat_show_image`, `chat_history`, `chat_get_message` |
| **Web** | 2 | `web_search` (Brave API), `web_fetch` (HTML→Markdown) |
| **QEMU** | 5 | `qemu_ssh_exec`, `qemu_status`, `qemu_start_vm`, `qemu_restart_vm`, `qemu_shutdown_vm` |
| **Task** | 5 | `task_async`, `task_query`, `task_list`, `task_cancel`, `task_summary` |
| **VM (VMUSE)** | 32 | Browser (9), Desktop (3), Shell (2), File (4), Window (7), Context (7) |

#### 执行架构

```
工具调用请求
    ↓
ToolExecutor.execute()
    ↓
判断工具类型
    ├─→ 内置工具 → _execute_builtin()
    │              ↓
    │        调用 Gateway Internal API (httpx)
    │        • Memory: POST /internal/rt/{runtime_id}/memory/*
    │        • Chat: POST /internal/rt/{runtime_id}/chat/*
    │        • QEMU: POST /internal/rt/{runtime_id}/qemu/*
    │        • VM: 直接访问 VMUSE HTTP 服务
    │
    └─→ 外部工具 → _execute_external()
                   ↓
             MCP Client.call_tool()
```

#### Runtime 管理

**RuntimeContext 数据结构**:
```python
class RuntimeContext:
    runtime_id: str
    agent_id: str
    subagent_id: str
    mcp_url: Optional[str]          # MCP 服务 URL
    external_tools: List[dict]      # 外部工具列表
    tool_ports: Dict[str, int]      # 工具端口映射
    discovery_task: Optional[Task]  # 工具发现任务
```

**生命周期管理**:
```
1. 创建 Runtime → RuntimeManager.create()
2. 注册 tool_ports → POST /internal/runtimes/{runtime_id}/tool-ports
3. 启动工具发现 → start_discovery() (异步)
4. 调用工具 → execute_tool()
5. 删除 Runtime → delete() + 清除 tool_ports
```

**持久化和恢复**:
```python
# 注册时持久化到 Gateway
self._persist_tool_ports(runtime_id, ports)
# → POST /internal/runtimes/{runtime_id}/tool-ports
# → Gateway 存储到 agent_runtimes.tool_ports

# 启动时从 Gateway 恢复
restored = await manager.restore_from_gateway()
# → GET /internal/runtimes/with-tools
# → 仅返回 status IN (active, resting) AND tool_ports IS NOT NULL
```

#### 长结果处理

**自动截断机制**:
```python
if len(text_content) < 4KB:
    # 不处理
    return result
elif len(text_content) < 10KB:
    # head_tail 策略 (保留头尾)
    return {
        "truncated": True,
        "strategy": "head_tail",
        "preview": head + "...\n[truncated]\n..." + tail,
        "task_id": saved_task_id
    }
else:
    # reference_only 策略 (仅引用)
    return {
        "truncated": True,
        "strategy": "reference_only",
        "message": "Result too large...",
        "task_id": saved_task_id
    }
```

#### API 端点

```
GET    /api/health                                    # 健康检查
POST   /internal/runtimes                             # 创建 Runtime
DELETE /internal/runtimes/{runtime_id}                # 删除 Runtime
GET    /internal/runtimes                             # 列出所有 Runtime
GET    /internal/runtimes/{runtime_id}                # 获取 Runtime 信息
GET    /internal/runtimes/{runtime_id}/tools          # 获取工具列表 (内置+外部)
POST   /internal/runtimes/{runtime_id}/tools/call     # 调用工具
GET    /internal/runtimes/{runtime_id}/skills         # 列出 Skills
GET    /internal/runtimes/{runtime_id}/skills/{name}  # 获取 Skill 内容
GET    /internal/stats                                # 统计信息
```

---

### 4. VMControl Service (端口 8080)

**定位**: QEMU 虚拟机管理服务 (Rust 实现)

#### 技术栈
- Rust 2021 Edition
- Axum 0.7 (Web 框架)
- Tokio (异步运行时)
- Serde (JSON 序列化)
- Tracing (日志)

#### 架构组件

```rust
vmcontrol/src/
├── main.rs              # 主程序入口
├── api/
│   ├── server.rs        # Axum HTTP 服务器
│   └── routes/          # API 路由处理
│       ├── vm.rs        # VM 生命周期管理
│       ├── screen.rs    # 截图功能
│       ├── input.rs     # 键盘/鼠标输入
│       ├── guest.rs     # Guest Agent 操作
│       ├── vnc.rs       # VNC WebSocket 代理
│       └── vmuse.rs     # VMUSE 通用代理
├── qemu/
│   ├── qmp.rs           # QMP 协议客户端
│   └── guest_agent.rs   # Guest Agent 客户端
└── vnc/
    └── mod.rs           # WebSocket ↔ Unix Socket 代理
```

#### 通信协议

| 协议 | Socket 路径 | 用途 |
|------|------------|------|
| **QMP** (QEMU Machine Protocol) | `/tmp/novaic/novaic-qmp-{vm_id}.sock` | VM 生命周期控制 (启动/暂停/关闭/截图) |
| **Guest Agent** | `/tmp/novaic/novaic-ga-{vm_id}.sock` | VM 内部操作 (命令执行/文件操作) |
| **VNC** (RFB) | `/tmp/novaic/novaic-vnc-{vm_id}.sock` | 屏幕显示 |

#### 核心功能

**1. VM 生命周期管理**
```rust
// 自动发现运行中的 VM
auto_register_running_vms()
    ↓
扫描 /tmp/novaic/ 目录
    ↓
查找 novaic-qmp-*.sock 文件
    ↓
创建 VmManager 并注册

// VM 控制操作
pause()     → QMP 'stop'
resume()    → QMP 'cont'
shutdown()  → QMP 'system_powerdown'
```

**2. 屏幕控制**
```rust
screenshot() 流程:
1. 创建临时 PNG 文件
2. 执行 QMP 'screendump' 命令
3. 读取文件并转换为 base64
4. 解析图片尺寸
5. 清理临时文件
6. 返回 ScreenshotData
```

**3. 输入控制**
```rust
// 键盘输入
send_key("a")                    // 单键
send_key_combo(&["ctrl", "c"])   // 组合键
type_text("Hello")               // 文本输入 (逐字符转换)

// 鼠标输入
input-send-event: abs (移动到绝对坐标)
input-send-event: btn (点击: press + release)
input-send-event: wheel (滚轮: up/down)
```

**4. Guest Agent 操作**
```rust
// 命令执行
guest-exec: 异步执行，返回 PID
guest-exec-status: 查询状态
exec_sync(): 轮询直到完成

// 文件操作
guest-file-open: 打开文件
guest-file-read: 读取 (自动分块)
guest-file-write: 写入 (自动分块)
guest-file-close: 关闭
```

**5. VNC WebSocket 代理**
```rust
handle_websocket(ws) 流程:
1. 连接 VNC Unix Socket
2. 分离读写流
3. 启动双向转发任务:
   - WebSocket → VNC
   - VNC → WebSocket
4. 任何一方关闭则终止连接
```

#### 连接策略

**按需连接 (避免 "Broken pipe")**:
```rust
// 每次操作创建临时连接
pub async fn create_qmp_client(&self) -> Result<QmpClient> {
    QmpClient::connect(&self.qmp_socket).await
    // 操作完成后自动关闭 (Drop trait)
}
```

#### API 端点

```
GET    /health                          # 健康检查
GET    /api/vms                         # 列出所有 VM
POST   /api/vms                         # 注册 VM
GET    /api/vms/:id                     # 获取 VM 信息
POST   /api/vms/:id/pause               # 暂停 VM
POST   /api/vms/:id/resume              # 恢复 VM
POST   /api/vms/:id/shutdown            # 关闭 VM
POST   /api/vms/:id/screenshot          # 截图
POST   /api/vms/:id/input/keyboard      # 键盘输入
POST   /api/vms/:id/input/mouse         # 鼠标输入
POST   /api/vms/:id/guest/exec          # 执行命令
GET    /api/vms/:id/guest/file          # 读取文件
POST   /api/vms/:id/guest/file          # 写入文件
GET    /api/vms/:id/vnc                 # VNC WebSocket
```

---

## 🔄 Task Queue 架构

### 三层架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    Layer 3: Saga                         │
│               业务流程编排 (6 个 Saga)                     │
│  • message_process    • runtime_start                    │
│  • react_think        • react_actions                    │
│  • runtime_complete   • summarize                        │
└────────────────────┬────────────────────────────────────┘
                     │ 触发
┌────────────────────▼────────────────────────────────────┐
│                 Layer 2: Handlers                        │
│            幂等业务操作 (26 个 Task Topics)                │
│  • Runtime (8)   • LLM (3)      • MCP (2)               │
│  • Tool (1)      • Context (3)  • Message (3)           │
│  • SubAgent (3)  • Summary (3)                          │
└────────────────────┬────────────────────────────────────┘
                     │ 使用
┌────────────────────▼────────────────────────────────────┐
│                 Layer 1: TaskQueue                       │
│                任务队列基础设施                            │
│  • 原子认领 (CAS)                                         │
│  • 心跳保活 (Heartbeat)                                  │
│  • 重试机制 (Retry)                                       │
│  • 超时恢复 (Recovery)                                    │
│  • 幂等性 (Idempotency)                                  │
└──────────────────────────────────────────────────────────┘
```

### Layer 1: TaskQueue - 任务队列基础

**核心能力**:
- ✅ **原子认领**: CAS 操作防止重复认领
- ✅ **心跳保活**: Worker 定期续约，超时自动恢复
- ✅ **重试机制**: 最多 3 次重试（可配置）
- ✅ **幂等性**: `idempotency_key` 唯一约束
- ✅ **FIFO 锁**: 8 分片锁提升并发

**流程**:
```
publish() → 发布任务 (status=pending)
    ↓
claim() → 原子认领 (pending → claimed)
    ↓
heartbeat() → 心跳续约 (更新 heartbeat_at)
    ↓
complete() / fail() → 完成或失败
    ↓
recover_stale() → 超时恢复 (claimed → pending)
```

### Layer 2: Handlers - 幂等业务操作

**26 个任务类型 (Task Topics)**:

#### Runtime 任务 (8 个)
```python
runtime.create                  # 创建 Runtime，构建初始 Context
runtime.update_phase            # 更新 phase (CAS)
runtime.set_status              # 设置 status (CAS)
runtime.increment_round         # 增加 round 计数
runtime.set_summarized          # 设置已摘要标志
runtime.set_need_rest           # 设置需要休息标志
runtime.check_new_messages      # 检查新消息 + need_rest
runtime.generate_simple_summary # 生成简单摘要
```

#### LLM 任务 (3 个)
```python
llm.call                        # 调用 LLM (含 Context 清理和多模态处理)
llm.call_summary                # 生成对话摘要
llm.call_hot_cold_summary       # 生成 Hot/Cold Summary
```

#### MCP 任务 (2 个)
```python
mcp.create                      # 创建 MCP Server
mcp.destroy                     # 销毁 MCP Server
```

#### Tool 任务 (1 个)
```python
tool.execute                    # 执行工具 (通过 Tools Server)
```

#### Context 任务 (3 个)
```python
context.read                    # 读取 Runtime context (过滤 sending)
context.append                  # 追加消息到 context
context.get                     # 获取 Runtime context (普通查询)
```

#### Message 任务 (3 个)
```python
message.process                 # 处理用户消息 (触发 Saga)
message.claim                   # 认领消息 (sending → sent, CAS)
message.route                   # 消息路由决策 (唤醒或跳过)
```

#### SubAgent 任务 (3 个)
```python
subagent.wake                   # 唤醒 SubAgent (sleeping → awaking)
subagent.set_awake              # 设置为 awake (awaking → awake)
subagent.set_sleeping           # 设置为 sleeping
```

#### Summary 任务 (3 个)
```python
summary.merge_history           # 合并 Runtime summaries 到 history
summary.add_to_hrl              # 添加 Runtime 到 HRL
summary.merge_history_if_needed # 检查并触发历史合并
```

### Layer 3: Saga - 业务流程编排

**6 个 Saga 流程**:

#### 1. `message_process` - 消息处理入口
```
步骤 1: TASK → message.claim (认领消息)
步骤 2: TASK → message.route (路由决策)
步骤 3: DECISION → 决定是否启动 Runtime
步骤 4: SAGA → runtime_start (如果需要)
```

#### 2. `runtime_start` - Runtime 启动流程
```
步骤 1: TASK → runtime.create (创建 Runtime 记录)
步骤 2: TASK → mcp.create (创建 MCP Server)
步骤 3: TASK → subagent.set_awake (设置 SubAgent 为 awake)
步骤 4: SAGA → react_think (触发 ReAct 循环)
```

#### 3. `react_think` - ReAct Think 阶段
```
步骤 1: TASK → context.read (读取最新 context)
步骤 2: TASK → llm.call (调用 LLM)
步骤 3: TASK → context.append (保存 LLM 响应)
步骤 4: DECISION → 提取 tool_calls
步骤 5: SAGA → react_actions (触发动作执行)
```

#### 4. `react_actions` - ReAct Actions 阶段
```
步骤 1: TASK → runtime.update_phase (设置 waiting_actions)
步骤 2: PARALLEL → tool.execute (并行执行所有工具)
步骤 3: PARALLEL → context.append (并行保存所有结果)
步骤 4: TASK → runtime.check_new_messages (检查新消息)
步骤 5: DECISION → 决定继续循环或完成
步骤 6: SAGA → react_think / runtime_complete
```

#### 5. `runtime_complete` - Runtime 完成流程
```
步骤 1: TASK → runtime.set_status (设置 completed)
步骤 2: TASK → runtime.generate_simple_summary (生成摘要)
步骤 3: TASK → subagent.set_sleeping (设置 sleeping)
步骤 4: TASK → mcp.destroy (销毁 MCP Server)
步骤 5: SAGA → summarize (异步触发)
```

#### 6. `summarize` - 异步摘要生成
```
步骤 1: TASK → llm.call_hot_cold_summary (生成 Hot/Cold)
步骤 2: TASK → summary.add_to_hrl (添加到 HRL)
步骤 3: TASK → summary.merge_history_if_needed (检查合并)
```

### Saga 步骤类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **TASK** | 触发单个 Task | `runtime.create` |
| **PARALLEL** | 并行触发多个 Task | 并行执行工具调用 |
| **DECISION** | 纯计算决策 | 提取 tool_calls，决定下一步 |
| **SAGA** | 触发子 Saga | `runtime_start` 触发 `react_think` |

---

## 📊 数据流

### 完整消息处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 用户发送消息                                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Gateway: POST /api/chat                                       │
│    • 保存到 chat_messages (status=sending, read=0)              │
│    • 返回 message_id                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Watchdog: 监控 Gateway                                        │
│    • 定期查询: GET /api/internal/messages/sending               │
│    • 发现 sending 消息                                          │
│    • 调用 Queue Service: POST /api/queue/sagas/start           │
│      → 启动 message_process Saga                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. SagaWorker: 认领并执行 message_process Saga                  │
│    步骤 1: message.claim → sending → sent (CAS)                 │
│    步骤 2: message.route → 决定唤醒或跳过                        │
│    步骤 3: DECISION → 判断是否需要启动 Runtime                   │
│    步骤 4: 触发 runtime_start Saga                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SagaWorker: 执行 runtime_start Saga                          │
│    步骤 1: runtime.create → 创建 Runtime 记录                    │
│    步骤 2: mcp.create → 创建 MCP Server (Tools Server)          │
│    步骤 3: subagent.set_awake → 设置 SubAgent awake             │
│    步骤 4: 触发 react_think Saga                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. ReAct 循环: react_think → react_actions → react_think...    │
│                                                                  │
│  【react_think Saga】                                            │
│    步骤 1: context.read → 读取最新 context                       │
│    步骤 2: llm.call → 调用 LLM (OpenAI/Anthropic/Google)        │
│    步骤 3: context.append → 保存 LLM 响应                        │
│    步骤 4: DECISION → 提取 tool_calls                           │
│    步骤 5: 触发 react_actions Saga                              │
│                                                                  │
│  【react_actions Saga】                                          │
│    步骤 1: runtime.update_phase → waiting_actions               │
│    步骤 2: PARALLEL → tool.execute (并行执行所有工具)            │
│            → TaskWorker 调用 Tools Server                       │
│            → Tools Server 调用 Gateway Internal API             │
│    步骤 3: PARALLEL → context.append (并行保存所有结果)          │
│    步骤 4: runtime.check_new_messages → 检查新消息              │
│    步骤 5: DECISION → 决定继续或完成                            │
│    步骤 6: 触发 react_think 或 runtime_complete                 │
│                                                                  │
│  (循环直到完成或中断)                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. 完成: runtime_complete Saga                                  │
│    步骤 1: runtime.set_status → completed                       │
│    步骤 2: runtime.generate_simple_summary → 生成摘要           │
│    步骤 3: subagent.set_sleeping → 设置 sleeping                │
│    步骤 4: mcp.destroy → 销毁 MCP Server                        │
│    步骤 5: 触发 summarize Saga (异步)                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. SSE 推送: Gateway → Frontend                                 │
│    • Worker 通过 Gateway Internal API 广播事件                  │
│    • Gateway 通过 SSE 推送给前端                                 │
│    • 前端实时更新 UI                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 工具执行流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. react_actions Saga: 并行执行工具                              │
│    PARALLEL: tool.execute (多个工具)                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. TaskWorker: 认领 tool.execute 任务                           │
│    • POST /api/queue/tasks/claim                                │
│    • 获取 {tool_name, arguments, runtime_id}                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Handler: handle_tool_execute()                               │
│    • 调用 Tools Server: POST /internal/runtimes/{id}/tools/call│
│    • 传递 {name, arguments}                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Tools Server: ToolExecutor.execute()                         │
│    判断工具类型:                                                  │
│    ├─→ 内置工具 (如 memory_save)                                │
│    │   • 调用 Gateway Internal API                              │
│    │   • POST /internal/rt/{runtime_id}/memory/save            │
│    │                                                             │
│    └─→ 外部工具 (如 custom_mcp_tool)                            │
│        • 调用 MCP Client                                        │
│        • mcp_client.call_tool(tool_name, args)                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. 长结果处理: 自动截断                                           │
│    if len(result) < 4KB:                                        │
│        返回完整结果                                              │
│    elif len(result) < 10KB:                                     │
│        截断为 head_tail 策略                                     │
│    else:                                                        │
│        仅返回引用，完整内容保存到 Task                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. 返回结果: TaskWorker → Queue Service → react_actions Saga   │
│    • complete(task_id, result)                                  │
│    • Saga 收集所有工具结果                                       │
│    • 继续下一步: context.append                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术栈

### Backend Services (Python)

| 组件 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11+ | 主要语言 |
| **FastAPI** | 0.109.0+ | Web 框架 |
| **Uvicorn** | 0.27.0+ | ASGI 服务器 |
| **httpx** | 0.26.0+ | HTTP 客户端 |
| **aiohttp** | 3.9.0+ | 异步 HTTP |
| **Pydantic** | 2.5.0+ | 数据验证 |
| **aiosqlite** | 0.19.0+ | 异步 SQLite |
| **websockets** | 12.0+ | WebSocket 支持 |
| **beautifulsoup4** | 4.12.0+ | HTML 解析 |
| **html2text** | 2024.2.26+ | HTML→Markdown |

### VMControl Service (Rust)

| 组件 | 版本 | 用途 |
|------|------|------|
| **Rust** | 2021 Edition | 主要语言 |
| **Axum** | 0.7 | Web 框架 |
| **Tokio** | - | 异步运行时 |
| **Serde** | - | JSON 序列化 |
| **Tracing** | - | 结构化日志 |
| **Thiserror** | - | 错误处理 |

### 数据库

| 组件 | 用途 | 大小 |
|------|------|------|
| **SQLite** | Gateway 数据库 (novaic.db) | 2.2 MB |
| **SQLite** | Queue Service 数据库 (queue.db) | 68 KB |

### 虚拟化

| 组件 | 用途 |
|------|------|
| **QEMU** | 虚拟机管理 |
| **QMP** | QEMU Machine Protocol |
| **Guest Agent** | VM 内部操作 |
| **VNC** | 屏幕显示 (RFB 协议) |

---

## 🚀 部署架构

### 服务依赖关系

```
┌──────────────────────────────────────────────────────┐
│                   启动顺序                            │
├──────────────────────────────────────────────────────┤
│  1. Gateway (19999)         ← 最先启动，提供 API     │
│  2. Queue Service (19997)   ← 任务队列服务           │
│  3. Tools Server (19998)    ← 工具服务 (可选)       │
│  4. Workers                 ← 执行任务               │
│     • TaskWorker (2进程)                             │
│     • SagaWorker (1进程)                             │
│     • HealthWorker                                   │
│     • Watchdog                                       │
│  5. VMControl (8080)        ← VM 控制 (可选)        │
└──────────────────────────────────────────────────────┘
```

### Worker 进程配置

| Worker | 进程数 | 职责 | 连接 |
|--------|--------|------|------|
| **TaskWorker** | 2 | 认领并执行 Task | Queue Service (19997) |
| **SagaWorker** | 1 | 认领并执行 Saga | Queue Service (19997) |
| **HealthWorker** | 1 | 监控超时任务/Saga | Queue Service (19997) |
| **Watchdog** | 1 | 监控消息，触发 Saga | Gateway (19999) |

### 端口分配

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| Gateway | 19999 | HTTP + SSE | 业务 API + 事件推送 |
| Queue Service | 19997 | HTTP | Task Queue + Saga |
| Tools Server | 19998 | HTTP | 工具执行 |
| VMControl | 8080 | HTTP + WebSocket | VM 管理 + VNC |

### 数据目录结构

```
$NOVAIC_DATA_DIR/
├── novaic.db                    # Gateway 数据库 (2.2 MB)
├── queue.db                     # Queue Service 数据库 (68 KB)
├── logs/
│   ├── gateway.log              # Gateway 日志
│   ├── queue-service.log        # Queue Service 日志
│   ├── task-worker.log          # TaskWorker 日志
│   ├── saga-worker.log          # SagaWorker 日志
│   ├── health-worker.log        # HealthWorker 日志
│   └── watchdog.log             # Watchdog 日志
└── pids.txt                     # 进程 PID 文件
```

### 快速启动

```bash
# 设置数据目录
export NOVAIC_DATA_DIR=~/.novaic

# 一键启动所有服务
cd novaic-backend
./start_all_services.sh

# 查看服务状态
curl http://127.0.0.1:19999/health    # Gateway
curl http://127.0.0.1:19997/health    # Queue Service

# 查看日志
tail -f $NOVAIC_DATA_DIR/logs/gateway.log
tail -f $NOVAIC_DATA_DIR/logs/queue-service.log

# 一键停止
./stop_all_services.sh
```

### 环境变量配置

```bash
# 必需
export NOVAIC_DATA_DIR=~/.novaic

# 可选 (端口配置)
export GATEWAY_PORT=19999
export QUEUE_SERVICE_PORT=19997
export TOOLS_SERVER_PORT=19998
export VMCONTROL_PORT=8080

# 可选 (超时配置)
export TASK_TIMEOUT=60
export SAGA_TIMEOUT=300
export HTTP_TIMEOUT=30.0

# 可选 (并发配置)
export NUM_WORKERS=2
export MAX_CONCURRENT_SAGAS=10

# 可选 (业务配置)
export HRL_TRIGGER_LENGTH=15
export HRL_KEEP_RECENT=5
```

---

## 📈 性能指标

### Queue Service 独立后性能提升

| 指标 | 之前 | 现在 | 提升 |
|------|------|------|------|
| Task claim 延迟 | 20ms | 12ms | **40%↓** |
| 并发任务数 | 100/s | 300/s | **3x** |
| 锁竞争 | 高 | 零 | **100%↓** |
| 数据库隔离 | 否 | 是 | ✅ |

### 架构优势

#### 1. 性能隔离
- ✅ 独立数据库消除锁竞争
- ✅ FIFO 分片锁提升并发
- ✅ 多进程 Worker 真并发

#### 2. 故障隔离
- ✅ Queue 故障不影响 Gateway
- ✅ Gateway 故障不影响 Queue
- ✅ Worker 崩溃自动恢复

#### 3. 可扩展性
- ✅ 易于演进到 Redis/PostgreSQL
- ✅ 支持横向扩展 Queue Service
- ✅ 支持动态增减 Worker

#### 4. 高可用性
- ✅ 心跳保活机制
- ✅ 超时自动恢复
- ✅ 重试机制

---

## 🎯 关键设计模式

### 1. Master-Driven 架构
- Gateway 作为协调中心，不直接执行任务
- 通过消息队列解耦业务逻辑和任务执行
- SSE 实现事件驱动的实时通信

### 2. Saga 流程编排
- 复杂业务流程拆分为多个原子步骤
- 支持并行执行、条件分支、子流程
- 自动重试和错误恢复

### 3. Repository 模式
- 数据访问层与业务逻辑分离
- 统一的数据仓库接口
- 便于单元测试和 Mock

### 4. Worker 池模式
- 多进程 Worker 提高并发能力
- 心跳机制保证任务可靠性
- 故障隔离和自动恢复

### 5. 微服务架构
- 服务间通过 HTTP REST 通信
- 独立数据库实现数据隔离
- 易于独立部署和扩展

### 6. 按需连接 (VMControl)
- 每次操作创建临时连接
- 避免长连接 "Broken pipe" 问题
- 资源高效利用

---

## 🔒 安全机制

| 机制 | 说明 |
|------|------|
| **Runtime 隔离** | 每个 Runtime 独立上下文，防止跨 Runtime 访问 |
| **VM 隔离** | QEMU 虚拟机与宿主机隔离，通过 Socket 通信 |
| **权限控制** | Main Runtime 独占特定操作 (如 `runtime_rest`) |
| **幂等性** | 防止重复执行，`idempotency_key` 唯一约束 |
| **超时保护** | 所有操作都有超时限制，防止无限等待 |
| **错误隔离** | Worker 进程独立，崩溃不影响其他进程 |
| **CAS 操作** | 原子状态转换，防止并发冲突 |

---

## 📚 总结

### 核心特性

- 🏗️ **三层架构**: TaskQueue → Handlers → Saga
- 🚀 **微服务设计**: Gateway + Queue Service + Tools Server + VMControl
- 🔄 **异步处理**: Task Queue + Worker 池 + Saga 编排
- 🎯 **流程编排**: 6 个 Saga 流程支持复杂业务
- 🛡️ **故障隔离**: 独立数据库、独立进程、独立服务
- 📈 **性能优化**: FIFO 锁、多进程、并发 3x
- 🔒 **安全保障**: Runtime 隔离、VM 隔离、权限控制

### 关键数据

- **4 个核心服务**: Gateway, Queue Service, Tools Server, VMControl
- **6 个 Worker 进程**: TaskWorker (2), SagaWorker, HealthWorker, Watchdog, (可选) VMControl
- **26 个任务类型**: Runtime (8), LLM (3), MCP (2), Tool (1), Context (3), Message (3), SubAgent (3), Summary (3)
- **6 个 Saga 流程**: message_process, runtime_start, react_think, react_actions, runtime_complete, summarize
- **67 个内置工具**: Memory (10), Runtime (7), Chat (6), Web (2), QEMU (5), Task (5), VM (32)
- **2 个数据库**: novaic.db (2.2 MB), queue.db (68 KB)
- **4 个端口**: 19999 (Gateway), 19997 (Queue), 19998 (Tools), 8080 (VMControl)

### 技术亮点

- ✨ **Master-Driven**: 协调中心模式，清晰的职责分离
- ✨ **Saga 编排**: 复杂流程可视化、可维护、可扩展
- ✨ **分布式队列**: 高并发、高可用、易扩展
- ✨ **Rust + Python**: 性能关键部分用 Rust，业务逻辑用 Python
- ✨ **QEMU 虚拟化**: 完整的 VM 管理能力
- ✨ **MCP 集成**: 支持外部工具动态发现
- ✨ **实时通信**: SSE + WebSocket 实现实时交互

---

**文档维护**: NovAIC Team  
**最后更新**: 2026-02-08  
**架构版本**: v2.0 (Queue Service 独立)
