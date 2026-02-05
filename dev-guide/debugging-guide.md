# Subagent 调试指南

> 本文档告诉你如何调试 NovAIC 的问题。按照步骤执行，然后汇报结果。

---

## 第一步：确定问题在哪一层

```
前端 (React) → Gateway API (FastAPI) → 数据库 (SQLite)
                    ↓
              Worker (Task/Saga)
```

**快速判断方法**：先调 API 看返回值是否正确。

```bash
# 获取 agent 列表
curl -s "http://127.0.0.1:19999/api/agents" | python3 -m json.tool

# 获取消息历史（替换 xxx 为实际 agent_id）
curl -s "http://127.0.0.1:19999/api/chat/history?agent_id=xxx&limit=10" | python3 -m json.tool

# 获取执行日志
curl -s "http://127.0.0.1:19999/api/logs/entries?agent_id=xxx&limit=10" | python3 -m json.tool
```

- **API 返回正确** → 问题在前端
- **API 返回错误** → 问题在后端

---

## 第二步：检查数据库

### 数据库位置

```
~/Library/Application Support/com.novaic.app/novaic.db
```

### 常用查询

```bash
# 查看最近消息
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, type, content, timestamp FROM chat_messages ORDER BY timestamp DESC LIMIT 10;"

# 查看执行日志
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, kind, status, event_key, timestamp FROM execution_logs ORDER BY id DESC LIMIT 10;"

# 查看任务队列
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, topic, status, error FROM tasks ORDER BY created_at DESC LIMIT 10;"

# 查看 Saga 状态
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, saga_type, status, current_step, error FROM sagas ORDER BY created_at DESC LIMIT 5;"

# 查看 Runtime 状态
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, agent_id, status, phase FROM runtimes ORDER BY created_at DESC LIMIT 5;"
```

---

## 第三步：检查日志

### 日志位置

```
~/Library/Application Support/com.novaic.app/logs/
```

### 查看日志命令

```bash
# 查看最近日志
cat ~/Library/Application\ Support/com.novaic.app/logs/*.log | tail -100

# 搜索错误
grep -i "error\|exception\|failed" ~/Library/Application\ Support/com.novaic.app/logs/*.log | tail -30
```

---

## 第四步：检查服务状态

```bash
# 检查进程
ps aux | grep -E "main_gateway|main_tools|queue_service|saga_worker|task_worker|watchdog" | grep -v grep

# 检查端口
lsof -i :19999 -i :19998 -i :19997

# 健康检查
curl -s http://127.0.0.1:19999/api/health
curl -s http://127.0.0.1:19998/api/health
```

---

## 常见问题速查

| 症状 | 可能原因 | 检查方法 |
|------|----------|----------|
| 消息发送无响应 | Saga 失败 / Worker 未运行 | 查 Saga 状态 |
| 消息刷新后消失 | API 返回不全 / 前端过滤 | 先调 API 看返回 |
| Execute Log 为空 | 日志未写入 / SSE 未推送 | 查数据库有无记录 |
| 最后一条消息不显示 | 分页逻辑错误 / 虚拟列表问题 | 调 API 看最后一条 |

---

## 汇报模板

调试完成后，使用以下格式汇报：

```markdown
## 调试结果

**问题**：[问题描述]

**排查过程**：
1. 调 API：[结果]
2. 查数据库：[结果]
3. 查日志：[结果]

**定位**：[问题在哪一层，哪个文件/函数]

**建议修复**：[如何修复]
```

---

## 关键文件位置

| 层 | 文件 | 说明 |
|----|------|------|
| Gateway API | `novaic-backend/main_gateway.py` | HTTP 端点 |
| 数据库操作 | `novaic-backend/gateway/db/repositories/chat.py` | 消息/日志存储 |
| Schema | `novaic-backend/gateway/db/schema.py` | 表结构 |
| Worker | `novaic-backend/task_queue/handlers/` | Task 处理 |
| 前端 Store | `novaic-app/src/store/index.ts` | 状态管理 |
| 前端 API | `novaic-app/src/services/api.ts` | API 调用 |
| 消息列表 | `novaic-app/src/components/Chat/MessageList.tsx` | 消息渲染 |
| 执行日志 | `novaic-app/src/components/Visual/ExecutionLog.tsx` | 日志渲染 |
