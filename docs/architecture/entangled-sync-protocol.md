# Entangled 同步协议与数据流

Entangled 是 Novaic 平台的实时数据同步中枢（:19900），负责服务端实体状态与客户端 SQLite 缓存之间的双向同步。

## 协议总览

```
┌─────────────────────────────┐          ┌─────────────────────────────┐
│         服务端               │          │         客户端 (Tauri)       │
│                             │          │                             │
│  ┌───────────┐              │   WS     │  ┌───────────────┐          │
│  │ Business  │──HTTP写入──► │◄────────►│  │ entangled-    │          │
│  │ / Cortex  │              │  Sync    │  │ client (Rust) │          │
│  └───────────┘              │  Proto   │  └───────┬───────┘          │
│                             │          │          │                  │
│  ┌───────────┐              │          │  ┌───────▼───────┐          │
│  │ Entangled │              │          │  │ SQLite Cache  │          │
│  │  :19900   │              │          │  └───────┬───────┘          │
│  └───────────┘              │          │          │ Tauri Event      │
│                             │          │  ┌───────▼───────┐          │
│                             │          │  │ React (Query) │          │
│                             │          │  └───────────────┘          │
└─────────────────────────────┘          └─────────────────────────────┘
```

## 服务端

Entangled 服务端核心职责：

| 职责 | 说明 |
|------|------|
| 实体注册 | 维护 Entity Schema 定义，决定每种实体的同步行为 |
| 连接管理 | 管理所有 WS 连接，处理认证、心跳、断线重连 |
| 变更广播 | 当实体状态变化时，计算 delta 并推送给订阅方 |
| 全量同步 | 新连接或断线重连时提供 full sync 帧 |

### Entity Schema

每个实体通过 Schema 定义其同步合约：

```json
{
  "entity": "message",
  "idField": "id",
  "keyParams": ["conversation_id"],
  "syncType": "List",
  "capabilities": ["read", "list", "action"]
}
```

| 字段 | 说明 |
|------|------|
| `entity` | 实体名称，全局唯一标识 |
| `idField` | 主键字段名 |
| `keyParams` | 列表查询时的过滤参数（构成缓存 key） |
| `syncType` | 存储类型：`List` / `Form` / `Stream` |
| `capabilities` | 支持的操作：`read`、`list`、`action`、`create`、`update`、`delete` |

### 三种存储类型

| 类型 | 用途 | 特征 |
|------|------|------|
| **List** | 消息列表、Agent 列表等 | 有序集合，支持分页、过滤 |
| **Form** | Agent 配置、用户设置等 | 单对象，通过 id 直接获取 |
| **Stream** | Agent 执行日志、实时事件等 | 只追加流，支持 prepend 帧 |

## 客户端

### Rust 侧：entangled-client crate

核心组件：**AuthProvider trait**（TauriAuthProvider 从共享 RwLock 读取 JWT）、**WsTransport**（内置指数退避自动重连）、**Connection Manager**（管理 Entangle/Disentangle + 心跳）、**SQLite Cache**（按 `entity + keyParams` 索引，支持增量/全量写入）。

### React 侧：TanStack Query 绑定

| 配置项 | 值 | 原因 |
|--------|-----|------|
| `staleTime` | `Infinity` | 数据由服务端推送更新，客户端不主动轮询 |
| 失效触发 | `entities_changed` Tauri 事件 | Rust 侧收到 Sync 帧写入 SQLite 后触发 |
| 数据获取 | Tauri IPC `entity_list` / `entity_get` | 从本地 SQLite 读取，零网络延迟 |

## WS 消息格式

### 客户端 → 服务端

| 消息类型 | 用途 | Payload 示例 |
|---------|------|-------------|
| `Entangle` | 订阅实体同步 | `{ entity: "message", params: { conversation_id: "xxx" } }` |
| `Disentangle` | 取消订阅 | `{ entity: "message", params: { conversation_id: "xxx" } }` |
| `Action` | 执行写操作 | `{ entity: "message", action: "send", data: { ... } }` |
| `Pong` | 心跳响应 | `{ }` |

### 服务端 → 客户端

| 消息类型 | 用途 | Payload 示例 |
|---------|------|-------------|
| `Sync` | 数据同步帧 | `{ entity: "message", frame: "delta", data: [...] }` |
| `Ack` | 操作确认 | `{ action_id: "xxx", status: "ok" }` |
| `Schema` | 实体 Schema 推送 | `{ entities: [ ... ] }` |
| `Ping` | 心跳探测 | `{ }` |
| `Push` | 服务端主动推送事件 | `{ event: "agent_status_changed", data: { ... } }` |

### Sync 帧类型

| 帧类型 | 触发场景 | 内容 |
|--------|---------|------|
| `full` | 首次 Entangle、断线重连 | 实体完整数据集 |
| `delta` | 实体局部变更 | 仅包含变更的字段/记录 |
| `prepend` | Stream 类型新事件 | 追加到流头部的新记录 |

## 悲观写入 + 乐观展示

Entangled 采用悲观写入策略——客户端写操作必须经服务端确认后才最终生效，同时在 UI 层可做乐观展示以提升体验。

### 写入路径

```
React dispatch → Tauri IPC entangled_method → WS Action → 服务端处理
    → Ack + Sync(delta) → entangled-client → SQLite 写入（原子事务）
    → Tauri Event entities_changed → React Query invalidate → UI 更新
```

### 读取路径

`React useQuery → Tauri IPC entity_list/entity_get → SQLite 本地查询 → 返回渲染`。完全本地完成，零网络延迟，新鲜度由服务端 Sync 帧保证。

## 实体注册与同步合约

系统当前注册了 15 个实体，覆盖 Agent 管理、对话消息、设备控制等核心业务域：

| 实体 | syncType | keyParams | 说明 |
|------|----------|-----------|------|
| agent | List | — | Agent 列表 |
| agent_detail | Form | agent_id | Agent 详情配置 |
| conversation | List | agent_id | 对话列表 |
| message | List | conversation_id | 消息列表 |
| task | List | agent_id | 任务记录 |
| task_detail | Form | task_id | 任务详情 |
| device | List | — | 设备列表 |
| device_detail | Form | device_id | 设备详情 |
| tool | List | agent_id | 工具配置 |
| skill | List | agent_id | 技能配置 |
| run_log | Stream | task_id | 日志流 |
| notification | List | — | 通知 |
| user_setting | Form | — | 设置 |
| workspace | List | — | 工作空间 |
| member | List | workspace_id | 成员 |

每个实体的同步合约由 Schema 严格约束，客户端只能执行 `capabilities` 中声明的操作。
