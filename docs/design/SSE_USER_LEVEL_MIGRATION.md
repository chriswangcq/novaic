# SSE 改为 User 维度改造方案

## 现状

### 当前逻辑（Agent 维度）

- **Chat SSE**：`/api/chat/messages?agent_id=xxx`，每个 agent 一条连接
- **Logs SSE**：`/api/logs/stream?agent_id=xxx`，每个 agent 一条连接
- **前端**：`SyncService.switchAgent(agentId)` 时：
  1. `disconnect()` 断开当前 SSE
  2. `msgService.load(agentId)` + `logService.load(agentId)` 从 DB/服务端拉数据
  3. `connectChat(agentId)` + `connectLogs(agentId)` 建立新连接

**问题**：切换 agent 必断连重连，连接数随 agent 数增长，后端需为每个 (user_id, agent_id) 维护订阅。

---

## 目标

- **SSE 以 User 维度**：一个用户一条长连接（或 Chat + Logs 各一条，但都不带 agent_id）
- **后端持续连接**：登录后建立，登出前不断开
- **事件持续写入 DB**：收到事件即写入 IndexedDB，不依赖当前选中的 agent
- **切换 agent 无重连**：只读 DB + 可选 delta sync，不重建 SSE

---

## 改造方案

### 一、后端（novaic-gateway）

#### 1. 新增 User 维度 SSE 端点

| 端点 | 说明 |
|------|------|
| `GET /api/user/chat/stream` | 用户级 Chat SSE，无 agent_id 参数 |
| `GET /api/user/logs/stream` | 用户级 Logs SSE，无 agent_id 参数 |

或合并为单一多路复用流：

| 端点 | 说明 |
|------|------|
| `GET /api/user/stream` | 用户级统一流，同时推送 chat + logs 事件 |

#### 2. sse_state.py 改造

**当前**：`(user_id, agent_id)` → 订阅者集合

**改造后**：`user_id` → 订阅者集合（每个用户一个 queue）

```python
# 新增：user-level 订阅
_chat_subscribers_user: Dict[str, asyncio.Queue] = {}  # subscriber_id -> queue
_chat_index_user: Dict[str, Set[str]] = {}  # user_id -> {subscriber_ids}

def register_chat_subscriber_user(subscriber_id: str, user_id: str) -> asyncio.Queue:
    queue = asyncio.Queue(maxsize=100)
    _chat_subscribers_user[subscriber_id] = (user_id, queue)
    _chat_index_user.setdefault(user_id, set()).add(subscriber_id)
    return queue
```

**广播逻辑**：`broadcast_chat_message` 时，除现有 `(user_id, agent_id)` 订阅外，同时推给该 `user_id` 的所有 user-level 订阅者。消息体已含 `agent_id`，前端可据此路由。

#### 3. 兼容策略

- 保留现有 `/api/chat/messages?agent_id=xxx`、`/api/logs/stream?agent_id=xxx`，供旧版前端或特殊场景使用
- 新前端优先使用 user-level 端点

---

### 二、前端（novaic-app）

#### 1. SSEManager 改造

```typescript
// 改造前
connectChat(agentId: string, handlers)   // agent 维度
connectLogs(agentId: string, handlers)

// 改造后
connectUserStream(handlers: UserStreamHandlers)  // user 维度，无 agentId
// 或保持 connectChat/connectLogs 但去掉 agentId 参数，URL 改为 /api/user/chat/stream
```

**UserStreamHandlers**：事件体含 `agent_id`，由 handler 内部解析并调用 `msgService.handleIncoming(agentId, msg)` 等。

#### 2. SyncService 改造

```typescript
// 改造前
async switchAgent(agentId: string) {
  this.disconnect();
  await Promise.all([this.msgService.load(agentId), this.logService.load(agentId)]);
  await this.connectChat(agentId);
  await this.connectLogs(agentId);
}

// 改造后
async switchAgent(agentId: string) {
  // 不断开 SSE
  await Promise.all([this.msgService.load(agentId), this.logService.load(agentId)]);
  // SSE 已在 connectUserStream() 时建立，无需重连
}

// 新增：登录后调用一次
connectUserStream() {
  this.sse.connectUserStream({ ...handlers });
}

// 登出时调用
disconnect() {
  this.sse.disconnect();
}
```

#### 3. 生命周期

| 时机 | 动作 |
|------|------|
| 用户登录 / App 初始化完成 | `SyncService.connectUserStream()` |
| 切换 Agent | `switchAgent(agentId)`，仅 load，不断连 |
| 用户登出 | `SyncService.disconnect()` |

#### 4. 事件路由

SSE 事件格式不变，仍含 `agent_id`：

- Chat：`AGENT_REPLY` 等，消息体有 `agent_id` 或可从 `message_id` 推断
- Logs：`log_entry`、`log_batch` 等，`data.agent_id` 已存在

前端收到后：

```typescript
onAgentReply: async (msg) => {
  const agentId = msg.agent_id ?? inferFromMessage(msg);
  await this.msgService.handleIncoming(agentId, msg);  // 写入 DB
}
```

---

### 三、数据流（改造后）

```
用户登录
    │
    ▼
connectUserStream() ──► 建立 /api/user/chat/stream + /api/user/logs/stream
    │
    │  (后端持续推送该用户所有 agent 的事件)
    ▼
SSE 事件到达 ──► 解析 agent_id ──► msgService.handleIncoming(agentId, msg)
    │                                    │
    │                                    ▼
    │                              messageRepo.putMessages() ──► DB
    │                                    │
    │                                    ▼
    │                              notifyMessageChange() ──► useMessagesFromDB refetch
    │
    └──► logService.handleIncoming(agentId, entry) ──► logRepo.putLogs() ──► DB
                                                           │
                                                           ▼
                                                     useLogsFromDB refetch

切换 Agent
    │
    ▼
switchAgent(agentId) ──► msgService.load(agentId) + logService.load(agentId)
    │                    (从 DB 读 + delta sync，不依赖 SSE)
    │
    └──► 不断开 SSE，数据可能已通过 SSE 写入 DB
```

---

### 四、实施步骤

1. **后端**：在 sse_state 中增加 user-level 订阅，新增 `/api/user/chat/stream`、`/api/user/logs/stream`（或 `/api/user/stream`）
2. **后端**：在 broadcast 逻辑中同时推给 user-level 订阅者
3. **前端**：SSEManager 支持 user-level 连接（无 agent_id）
4. **前端**：SyncService 在 init 时 connectUserStream，switchAgent 时不再 disconnect/reconnect
5. **前端**：App 启动流程中，在用户初始化完成后调用 connectUserStream
6. **测试**：多 agent 切换、多 tab、登出重连等场景

---

### 五、实施完成（2026-03）

- **分离流**：采用两条 `/api/user/chat/stream`、`/api/user/logs/stream`
- **Chat 消息体**：`AGENT_REPLY`、`STATUS_UPDATE` 等已包含 `agent_id`（broadcast_chat_message 注入）
- **初次连接历史**：user-level 不推送初始数据，完全依赖前端的 load + delta sync

### 六、待确认（已解决）

1. ~~合并流 vs 分离流~~ → 分离流
2. ~~Chat 消息体 agent_id~~ → 已包含
3. ~~初次连接历史~~ → 依赖 load

### 七、Agent 维度 SSE 已移除（2026-03）

- 后端：删除 `/api/chat/messages`、`/api/chat/events`、`/api/logs/stream`
- sse_state：仅保留 user-level 订阅，notify_* 自动从 agent_id 解析 user_id
- 前端：删除 connectChat、connectLogs，仅使用 connectUserStream
