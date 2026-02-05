# Subagent Execute Log 参考

> 修改 Execute Log 相关功能时参考本文档。

---

## 数据流概览

```
Worker (llm_handlers / tool_handlers)
    ↓ sync_broadcast_log
Gateway Client (task_queue/client.py)
    ↓ POST /api/logs/broadcast
Gateway (main_gateway.py)
    ↓ 写入数据库 + 推送 SSE
前端 (store/index.ts)
    ↓ 收到 SSE，调用 API 拉取
ExecutionLog.tsx 渲染
```

---

## 关键文件

| 层 | 文件 | 职责 |
|----|------|------|
| Worker | `task_queue/handlers/llm_handlers.py` | 发送 think 事件 |
| Worker | `task_queue/handlers/tool_handlers.py` | 发送 tool 事件 |
| Worker | `task_queue/utils/broadcast.py` | `sync_broadcast_log` 函数 |
| Worker | `task_queue/client.py` | `GatewayInternalClient.broadcast_log` |
| Gateway | `main_gateway.py` | `broadcast_log` 函数、`/api/logs/*` 端点 |
| Gateway | `gateway/db/repositories/chat.py` | `upsert_execution_log`、`get_execution_logs` |
| 前端 | `novaic-app/src/store/index.ts` | `connectLogsSSE`、日志状态 |
| 前端 | `novaic-app/src/components/Visual/ExecutionLog.tsx` | 渲染组件 |

---

## 日志事件类型

| kind | status | 触发时机 |
|------|--------|----------|
| `think` | `running` | LLM 调用开始 |
| `think` | `complete` | LLM 调用结束 |
| `tool` | `running` | 工具执行开始 |
| `tool` | `complete` | 工具执行结束 |

---

## API 接口

### 写入日志

```bash
POST /api/logs/broadcast
{
  "agent_id": "xxx",
  "subagent_id": "main",
  "kind": "think" | "tool",
  "status": "running" | "complete",
  "event_key": "think:runtime_id:round_id",
  "data": {...},
  "input": {...},
  "result": {...}
}
```

### 读取日志

```bash
# 获取日志列表
GET /api/logs/entries?agent_id=xxx&subagent_id=main&after_id=123&limit=50

# 获取 subagent 列表
GET /api/logs/subagents?agent_id=xxx
```

---

## 修改时的检查清单

### 修改后端日志写入

- [ ] `sync_broadcast_log` 参数是否正确
- [ ] `event_key` 格式是否正确（用于 upsert）
- [ ] `input` 和 `result` 是否包含有用信息

### 修改后端 API

- [ ] `upsert_execution_log` 参数名是否匹配
- [ ] 返回值是否包含所有字段
- [ ] SSE 推送是否正确触发

### 修改前端显示

- [ ] LogEntry 类型是否包含所有字段
- [ ] 渲染逻辑是否处理了 `kind` 和 `status`
- [ ] 展开/折叠逻辑是否正确

---

## 数据库表结构

```sql
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY,
    agent_id TEXT NOT NULL,
    subagent_id TEXT NOT NULL DEFAULT 'main',
    type TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'tool',
    status TEXT NOT NULL DEFAULT 'complete',
    event_key TEXT,
    timestamp TEXT NOT NULL,
    data TEXT,
    updated_at TEXT
);

-- 用于 upsert 的唯一索引
CREATE UNIQUE INDEX idx_execution_logs_event_key 
ON execution_logs(agent_id, subagent_id, event_key);
```

---

## 常见问题

| 问题 | 原因 | 检查 |
|------|------|------|
| 日志没有新增 | upsert 失败 | 查后端日志看有无错误 |
| 前端不更新 | SSE 未推送 / API 未调用 | 检查 SSE 连接和 API 响应 |
| 日志内容为空 | input/result 未传 | 检查 broadcast 调用参数 |
