# Subagent 前后端交互参考

> 修改前后端交互时参考本文档，确保接口一致。

---

## 架构概览

```
前端 (React)
    ↓ invoke / fetch
Tauri (Rust)
    ↓ HTTP
Gateway (FastAPI, 端口 19999)
    ↓
数据库 (SQLite)
```

---

## API 调用方式

### 方式 1：通过 Tauri（大部分 API）

```typescript
// 前端 services/api.ts
const result = await invoke('gateway_get', { path: '/api/xxx' });
const result = await invoke('gateway_post', { path: '/api/xxx', body: data });
```

### 方式 2：直接 HTTP（SSE 和部分 API）

```typescript
// 前端 store/index.ts
const GATEWAY_URL = 'http://127.0.0.1:19999';
const eventSource = new EventSource(`${GATEWAY_URL}/api/chat/messages?agent_id=${id}`);
```

---

## 核心 API 对应表

### 聊天相关

| 前端调用 | 后端端点 | 说明 |
|----------|----------|------|
| `api.sendChatMessage(content, { agent_id })` | `POST /api/chat/send` | 发送消息 |
| `api.getChatHistory({ agent_id, limit })` | `GET /api/chat/history` | 获取历史 |
| `api.getChatMessage(id, agent_id)` | `GET /api/chat/message/{id}` | 获取单条 |
| `EventSource(/api/chat/messages)` | SSE | 实时消息 |

### 执行日志相关

| 前端调用 | 后端端点 | 说明 |
|----------|----------|------|
| `api.getLogEntries({ agent_id, subagent_id })` | `GET /api/logs/entries` | 获取日志 |
| `api.getLogSubagents(agent_id)` | `GET /api/logs/subagents` | 获取 subagent 列表 |
| `api.clearLogs(agent_id)` | `GET /api/logs/clear` | 清空日志 |
| `EventSource(/api/logs/stream)` | SSE | 实时日志 |

### Agent 相关

| 前端调用 | 后端端点 | 说明 |
|----------|----------|------|
| `api.listAgents()` | `GET /api/agents` | 获取列表 |
| `api.getAgent(id)` | `GET /api/agents/{id}` | 获取单个 |
| `api.createAgent(data)` | `POST /api/agents` | 创建 |
| `api.updateAgent(id, data)` | `PATCH /api/agents/{id}` | 更新 |
| `api.deleteAgent(id)` | `DELETE /api/agents/{id}` | 删除 |

---

## 修改 API 时的检查清单

### 新增/修改后端 API

- [ ] 在 `main_gateway.py` 或 `gateway/api/*.py` 添加端点
- [ ] 参数验证（必填参数检查）
- [ ] 返回格式与前端期望一致
- [ ] 更新本文档

### 新增/修改前端 API 调用

- [ ] 在 `services/api.ts` 添加函数
- [ ] 在 `types/index.ts` 添加类型
- [ ] 参数名与后端一致
- [ ] 处理错误情况

---

## 重要规则

### 1. agent_id 必填

所有与 Agent 相关的 API **必须**在请求中传入 `agent_id`：

```python
# 后端：必须检查 agent_id
agent_id = data.get("agent_id")
if not agent_id:
    raise HTTPException(status_code=400, detail="agent_id is required")
```

```typescript
// 前端：调用时必须传 agent_id
await api.sendChatMessage(content, { agent_id: currentAgentId });
```

### 2. 参数名一致性

前端发送的字段名必须与后端接收的一致：

```typescript
// 前端发送
{ input_data: {...}, result_data: {...} }

// 后端接收时要兼容
input_data = data.get("input_data") or data.get("input")
```

### 3. SSE 事件名一致

前端监听的事件名必须与后端推送的一致：

```python
# 后端推送
{"event": "logs_updated", "agent_id": "xxx"}
```

```typescript
// 前端监听
eventSource.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.event === 'logs_updated') { ... }
};
```

---

## 数据流示例：发送消息

```
1. 用户输入消息，点击发送
   ↓
2. 前端 store.sendMessage(content)
   ↓
3. 前端 api.sendChatMessage(content, { agent_id })
   ↓
4. Tauri invoke('gateway_post', { path: '/api/chat/send', body })
   ↓
5. 后端 POST /api/chat/send
   ↓
6. 后端写入 chat_messages 表
   ↓
7. 后端推送 SSE 到 _chat_subscribers
   ↓
8. 前端 EventSource 收到消息
   ↓
9. 前端 addMessage 更新 UI
```

---

## 关键文件

| 文件 | 说明 |
|------|------|
| `novaic-app/src/services/api.ts` | 前端 API 封装 |
| `novaic-app/src/store/index.ts` | 前端状态 + SSE |
| `novaic-app/src/types/index.ts` | TypeScript 类型 |
| `novaic-backend/main_gateway.py` | 后端主 API |
| `novaic-backend/gateway/api/agents.py` | Agent API |
| `novaic-backend/gateway/api/routes.py` | 其他路由 |
