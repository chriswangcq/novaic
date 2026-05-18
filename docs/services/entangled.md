# Entangled 实体同步

## 概述与职责

Entangled 是 Novaic 平台的实时实体同步服务，运行在端口 `:19900`，基于 WebSocket 协议构建。它负责将服务端的实体状态变更实时推送到前端客户端，实现数据的双向同步，是前端实时体验的核心基础设施。

核心职责包括：

- 定义实体 Schema 和 Store 类型
- 通过 WebSocket 协议实现实体的实时双向同步
- 管理客户端的实体订阅关系
- 在连接建立时推送 Schema 定义

## Entity Schema 与 Store 类型

Entangled 通过 Entity Schema 定义同步实体的结构和行为，每个实体关联一种 Store 类型来决定其数据管理方式。

### 3 种 Store 类型

| Store 类型 | 数据结构 | 适用场景 | 同步行为 |
|------------|----------|----------|----------|
| `List` | 有序列表 | 设备列表、Agent 列表、技能列表 | 支持增/删/改/排序，全量或增量同步 |
| `Form` | 单一对象 | 当前用户信息、系统设置 | 整体替换或字段级更新 |
| `Stream` | 追加流 | 聊天消息、日志流 | 仅追加，支持历史回溯 |

### 15 个注册实体

系统注册了 15 种需要实时同步的实体：

| 实体 | Store 类型 | 说明 |
|------|------------|------|
| `users` | List | 团队用户列表 |
| `agents` | List | Agent 列表 |
| `devices` | List | 设备列表 |
| `skills` | List | 技能列表 |
| `api-keys` | List | API 密钥列表 |
| `models` | List | 模型配置列表 |
| `messages` | Stream | 会话消息流 |
| `sessions` | List | 会话列表 |
| `tasks` | List | 任务列表 |
| `notifications` | Stream | 通知流 |
| `files` | List | 文件列表 |
| `workspaces` | List | 工作空间列表 |
| `device-pools` | List | 设备池列表 |
| `current-user` | Form | 当前用户信息 |
| `settings` | Form | 系统设置 |

## WS 同步协议

Entangled 定义了一套完整的 WebSocket 消息协议，分为客户端消息和服务端消息两组：

### 客户端 → 服务端消息

| 消息类型 | 说明 | 载荷 |
|----------|------|------|
| `Entangle` | 订阅实体 | `{ entity: string, params?: object }` |
| `Disentangle` | 取消订阅 | `{ entity: string }` |
| `Action` | 执行实体操作 | `{ entity: string, action: string, payload: object }` |

### 服务端 → 客户端消息

| 消息类型 | 说明 | 载荷 |
|----------|------|------|
| `Sync` | 实体数据同步 | `{ entity: string, data: object, type: "full"\|"delta" }` |
| `Ack` | 操作确认 | `{ action_id: string, status: "ok"\|"error", error?: string }` |
| `Schema` | Schema 定义推送 | `{ entities: EntitySchema[] }` |
| `Ping` | 心跳探测 | `{ timestamp: number }` |

### 协议流程

```
客户端                                服务端
  │                                      │
  │── WebSocket 连接建立 ────────────────►│
  │◄── Schema（所有实体定义） ───────────│  连接后立即推送
  │                                      │
  │── Entangle("agents") ──────────────►│  订阅 agents 实体
  │◄── Sync("agents", full, [...]) ─────│  全量推送当前数据
  │                                      │
  │    ... Agent 数据变更 ...             │
  │◄── Sync("agents", delta, {...}) ────│  增量推送变更
  │                                      │
  │── Action("agents", "create", {}) ──►│  客户端创建操作
  │◄── Ack(action_id, "ok") ───────────│  确认操作成功
  │◄── Sync("agents", delta, {...}) ────│  推送变更给所有订阅者
  │                                      │
  │── Disentangle("agents") ──────────►│  取消订阅
  │                                      │
  │◄── Ping ────────────────────────────│  定期心跳
  │── Pong ────────────────────────────►│
```

### 同步语义

- **Entangle 后首次同步**：服务端发送 `full` 类型的 Sync，包含实体完整数据。
- **后续变更**：服务端发送 `delta` 类型的 Sync，仅包含变更部分。
- **多客户端**：同一实体的变更会广播给所有订阅了该实体的客户端。
- **Action 操作**：客户端通过 Action 消息触发服务端操作，服务端通过 Ack 确认。

## 服务端架构

Entangled 服务端的内部架构分为三层：

### 连接管理层

- 管理 WebSocket 连接的建立和断开
- 维护连接到订阅关系的映射表
- 处理心跳检测和超时断连

### 订阅路由层

- 维护实体到订阅者列表的映射
- 当实体数据变更时，查找所有订阅者并推送
- 支持带参数的订阅过滤（如只订阅特定 session 的 messages）

### 数据同步层

- 监听 Business 服务的实体变更事件
- 将变更事件转换为 Sync 消息格式
- 管理全量快照和增量计算

```
Business 变更事件
    ↓
数据同步层（变更事件 → Sync 消息）
    ↓
订阅路由层（查找订阅者）
    ↓
连接管理层（WebSocket 发送）
    ↓
前端客户端
```

## 依赖关系

```
Entangled
├── Business — 监听实体变更事件
└── Redis    — 连接状态和订阅关系缓存（多实例部署时）
```

Entangled 被前端 App 直接连接，是前端获取实时数据的唯一通道。
