# 故障排查指南

## 快速诊断

```bash
# 1. 检查服务健康
curl http://127.0.0.1:19999/api/health  # Gateway
curl http://127.0.0.1:19998/api/health  # MCP Gateway

# 2. 检查核心状态
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
  SELECT '=== 未读消息 ===' as info;
  SELECT type, read, substr(content, 1, 40) FROM chat_messages WHERE read = 0;
  SELECT '=== SubAgent状态 ===' as info;
  SELECT subagent_id, status FROM subagents;
  SELECT '=== 失败任务 ===' as info;
  SELECT task_subtype, status, substr(error, 1, 50) FROM pipeline_tasks WHERE status = 'failed' LIMIT 5;
  SELECT '=== 执行中任务 ===' as info;
  SELECT task_subtype, claimed_at, heartbeat_at FROM pipeline_tasks WHERE status = 'claimed' LIMIT 5;
"
```

## 调试命令速查

### 数据库查询

```bash
# 设置别名 (加到 ~/.zshrc)
alias novaic-db='sqlite3 -header -column ~/Library/Application\ Support/com.novaic.app/novaic.db'

# 使用
novaic-db "SELECT * FROM chat_messages ORDER BY timestamp DESC LIMIT 5"
```

### 常用 SQL

```sql
-- 检查消息状态
SELECT type, read, agent_id, substr(content, 1, 50) as content 
FROM chat_messages ORDER BY timestamp DESC LIMIT 10;

-- 检查 SubAgent
SELECT * FROM subagents;

-- 检查 Runtime
SELECT runtime_id, agent_id, status, phase, mcp_url, current_round_num 
FROM agent_runtimes ORDER BY created_at DESC LIMIT 5;

-- 检查任务流
SELECT task_subtype, status, runtime_id, 
       substr(json_extract(args, '$.runtime_id'), 1, 20) as args_runtime_id
FROM pipeline_tasks ORDER BY created_at DESC LIMIT 20;

-- 检查失败任务详情
SELECT task_subtype, error, args FROM pipeline_tasks WHERE status = 'failed';

-- 检查任务中的 agent_id (诊断 "system" 问题)
SELECT task_subtype, 
       json_extract(args, '$.agent_id') as args_agent_id,
       agent_id as task_agent_id
FROM pipeline_tasks LIMIT 10;
```

### 重置数据

```bash
# 清理任务和状态 (保留消息)
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
DELETE FROM agent_runtimes;
DELETE FROM pipeline_tasks;
UPDATE subagents SET status = 'sleeping';
"

# 完全重置 (包括消息)
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
DELETE FROM agent_runtimes;
DELETE FROM pipeline_tasks;
DELETE FROM chat_messages;
UPDATE subagents SET status = 'sleeping', historical_summary = NULL;
"
```

---

## 常见问题

### 1. Agent 不响应消息

**症状**: 发送消息后没有反应

**排查流程**:

```bash
# Step 1: 确认消息已存入
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
SELECT id, type, read, agent_id FROM chat_messages ORDER BY timestamp DESC LIMIT 3;
"

# Step 2: 检查 SubAgent 状态
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "SELECT * FROM subagents;"
# 应该是 sleeping (等待唤醒) 或 awake/running (正在处理)

# Step 3: 检查是否有 monitor_launcher 任务
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
SELECT task_subtype, status FROM pipeline_tasks 
WHERE task_subtype = 'monitor_launcher' AND status = 'pending';
"

# Step 4: 检查 Launcher Service 是否运行
ps aux | grep launcher_main
```

**常见原因**:
- Launcher Service 未启动
- 首次启动没有使用 `--bootstrap`
- SubAgent 卡在错误状态 (手动 `UPDATE subagents SET status = 'sleeping'`)

### 2. 消息不被标记已读 (循环创建 Runtime)

**症状**: 
- `chat_messages.read` 始终为 0
- 不断创建新的 Runtime

**这是 "system" agent_id 问题！详见 `case-study-agent-id-mismatch.md`**

**排查**:

```bash
# 检查任务中的 agent_id
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
SELECT task_subtype, 
       json_extract(args, '$.agent_id') as args_agent_id,
       json_extract(args, '$.runtime_id') as args_runtime_id
FROM pipeline_tasks 
WHERE task_subtype LIKE 'think%' 
ORDER BY created_at DESC LIMIT 5;
"

# 如果 args_agent_id 为空或 'system'，说明 handler 没有从 Runtime 获取正确的 agent_id
```

**修复**: 确保所有 Handler 从 `runtime.get("agent_id")` 获取 agent_id

### 3. 任务卡在 claimed (executing)

**症状**: `pipeline_tasks` 中有长时间 claimed 的任务

**排查**:

```bash
# 查看卡住的任务
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
SELECT id, task_subtype, claimed_at, heartbeat_at, 
       (julianday('now') - julianday(heartbeat_at)) * 86400 as stale_seconds
FROM pipeline_tasks 
WHERE status = 'claimed'
ORDER BY claimed_at;
"

# heartbeat 超过 60 秒说明 Worker 已挂
```

**解决**:

```bash
# 方法 1: 等待 Health Service 自动恢复

# 方法 2: 手动恢复
curl -X POST "http://127.0.0.1:19999/internal/pipeline-tasks/recover-stale" \
  -H "Content-Type: application/json" \
  -d '{"timeout_seconds": 60}'

# 方法 3: 直接 SQL
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
UPDATE pipeline_tasks 
SET status = 'pending', claimed_by = NULL, claimed_at = NULL 
WHERE status = 'claimed';
"
```

### 4. Collector 永远不执行

**症状**: collector 任务一直是 pending

**原因**: `expected_tasks` != `completed_tasks`

**排查**:

```bash
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
SELECT id, task_subtype, expected_tasks, completed_tasks
FROM pipeline_tasks 
WHERE task_type = 'collector' AND status = 'pending';
"

# 找出同 stage 的 async 任务
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
SELECT id, task_subtype, status, error
FROM pipeline_tasks 
WHERE stage_id = '<stage_id>';
"
```

**常见原因**:
- async 任务失败但没有调用 `increment_collector_count`
- `expected_tasks` 计算错误

### 5. MCP 工具调用失败

**症状**: tool_call 任务失败，错误 "Cannot get MCP server URL"

**排查**:

```bash
# 检查 Runtime 的 mcp_url
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "
SELECT runtime_id, mcp_url FROM agent_runtimes WHERE mcp_url IS NULL;
"

# 检查 MCP Gateway 健康
curl http://127.0.0.1:19998/api/health

# 检查工具列表
curl http://127.0.0.1:19998/aggregate/<agent_id>/<runtime_id>/tools/list
```

**常见原因**:
- MCP Gateway 未启动
- `mcp_url` 字段为 NULL (RuntimeLauncher 创建失败)
- tool_call 任务的 args 中没有 `mcp_url`

### 6. 数据库更新不生效

**症状**: 调用 API 返回成功，但数据库没变化

**原因**: 缺少 `commit()`

**检查模式**:

```python
# 错误代码 (没有 commit)
await db.execute("UPDATE ...", params)

# 正确代码 (有 commit)
async with db.get_connection() as conn:
    await conn.execute("UPDATE ...", params)
    await conn.commit()
```

**已知有此问题的位置** (已修复):
- `api/internal.py` - `update_runtime` (round 更新)
- `api/internal.py` - `mark_messages_processed`
- `api/routes.py` - `clear_history`

### 7. 数据库锁定

**症状**: "database is locked" 错误

**解决**:

```bash
# 检查多进程
ps aux | grep "python.*main.py"

# 杀掉所有进程
pkill -9 -f "python.*main.py"
pkill -9 -f "launcher_main"
pkill -9 -f "collector_main"
pkill -9 -f "async_main"

# 或按端口杀
lsof -i :19999 | grep Python | awk '{print $2}' | xargs kill -9
lsof -i :19998 | grep Python | awk '{print $2}' | xargs kill -9

# 检查 WAL 文件
ls -la ~/Library/Application\ Support/com.novaic.app/*.db*

# Checkpoint WAL
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

### 8. 端口被占用

**症状**: "address already in use" 错误

```bash
# 检查端口占用
lsof -i :19999
lsof -i :19998

# 强制释放
lsof -i :19999 | grep Python | awk '{print $2}' | xargs kill -9
```

---

## 调试技巧

### 1. 添加临时日志

```python
# 在可疑位置添加
print(f"[DEBUG] agent_id={agent_id}, runtime_id={runtime_id}")
print(f"[DEBUG] args={json.dumps(args, indent=2)}")
```

### 2. 使用 API 直接测试

```bash
# 测试内部 API
curl http://127.0.0.1:19999/internal/runtimes/<agent_id>

# 测试 Runtime 更新
curl -X PATCH http://127.0.0.1:19999/internal/runtimes/<runtime_id> \
  -H "Content-Type: application/json" \
  -d '{"current_round_num": 2}'

# 验证更新结果
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT current_round_num FROM agent_runtimes WHERE runtime_id='<runtime_id>'"
```

### 3. 跟踪任务流

```bash
# 实时监控任务变化
watch -n 1 'sqlite3 -header ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT task_subtype, status, claimed_at FROM pipeline_tasks ORDER BY created_at DESC LIMIT 10"'
```

### 4. 验证数据一致性

```sql
-- 检查 Runtime 和 SubAgent 的 agent_id 是否一致
SELECT r.runtime_id, r.agent_id as runtime_agent, s.agent_id as subagent_agent
FROM agent_runtimes r
JOIN subagents s ON r.subagent_id = s.subagent_id
WHERE r.agent_id != s.agent_id;

-- 检查任务的 agent_id 是否正确
SELECT task_subtype, agent_id, json_extract(args, '$.agent_id') as args_agent_id
FROM pipeline_tasks
WHERE agent_id = 'system' AND json_extract(args, '$.agent_id') IS NULL;
```

---

## 日志位置

```bash
# Gateway 日志
~/Library/Application\ Support/com.novaic.app/logs/gateway-YYYYMMDD.log

# 开发模式各服务直接输出到终端
```

---

## 完全重置

**警告**: 这会删除所有数据！

```bash
# 停止所有服务
pkill -9 -f "python.*main.py"
pkill -9 -f "launcher_main"
pkill -9 -f "collector_main"
pkill -9 -f "async_main"
pkill -9 -f "mcp_main"

# 备份
cp ~/Library/Application\ Support/com.novaic.app/novaic.db \
   ~/Library/Application\ Support/com.novaic.app/novaic.db.backup

# 删除数据库 (会自动重建)
rm ~/Library/Application\ Support/com.novaic.app/novaic.db*

# 重启服务
cd novaic-gateway
source venv/bin/activate
python main.py &
python mcp_main.py &
python launcher_main.py --gateway-url "http://127.0.0.1:19999" --bootstrap &
python collector_main.py --gateway-url "http://127.0.0.1:19999" &
python async_main.py --gateway-url "http://127.0.0.1:19999" &
```

---

## 相关文档

- [架构概览](architecture.md)
- [服务架构](services-architecture.md)
- [MCP 调试](debugging-mcp.md)
- [Case Study: agent_id 问题](case-study-agent-id-mismatch.md)
