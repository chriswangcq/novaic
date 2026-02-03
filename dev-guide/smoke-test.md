# 后端冒烟测试指南

> **更新时间**: 2026-02-03
> **适用版本**: v22+ (Task Queue v2 + Saga 架构)

本文档记录后端冒烟测试的完整流程、常见问题和解决方案。

## 设计原则（必须遵守）

1. **非 Gateway 服务不得直接访问数据库**  
   - Task/Saga/Watchdog/Health 等只通过 Gateway API 交互  
   - DB 访问统一由 Gateway 处理

2. **LLM 配置通过 runtime_id 获取**  
   - API 入参统一使用 `runtime_id`  
   - 由 Gateway 内部推理 `agent_id` 并返回 LLM config  
   - 内部接口：`GET /internal/config/llm/runtime/{runtime_id}`

3. **Model 选择是 Agent 级别配置**  
   - 前端选择 model 后写入 agent（`model_id`）  
   - runtime 使用 agent 的 `model_id`，未设置则回退 `default_model`

4. **可用模型来源**  
   - `candidate_models` 表是最终可选模型集合  
   - 字段使用 `available` / `is_custom`  
   - 每个 model 绑定一个 provider（`api_key_id`）

5. **日志只用 tail/head**  
   - 避免 `cat`/`less` 读取大日志导致刷屏  
   - 推荐 `tail -n 50`、`head -n 50`

## 架构概述 (v20)

```
┌─────────────────────────────────────────────────────────┐
│                    服务组件                              │
├─────────────────────────────────────────────────────────┤
│ main_gateway.py   │ Gateway (19999) - REST API + SQLite │
│ main_mcp.py       │ MCP Gateway (19998) - MCP 管理      │
│ main_watchdog.py  │ Watchdog - 消息监听 + 触发 Saga     │
│ main_task.py      │ Task Worker - 执行所有 Handler      │
│ main_saga.py      │ Saga Worker - 编排多步骤流程        │
│ main_health.py    │ Health Worker - 健康监控            │
└─────────────────────────────────────────────────────────┘
```

## 快速启动

### 1. 环境准备

```bash
cd /path/to/novaic/novaic-backend
source venv/bin/activate
export NOVAIC_DATA_DIR=~/.novaic
export NOVAIC_GATEWAY_URL=http://127.0.0.1:19999
```

### 2. 清理旧状态（可选）

```bash
# 停止所有服务
pkill -9 -f "python.*main_" 2>/dev/null

# 清理数据库（完全重新开始）
rm -f ~/.novaic/novaic.db

# 清理日志
rm -f /tmp/*.log
```

### 3. 启动服务

```bash
# 启动 Gateway（必须先启动）
nohup python main_gateway.py > /tmp/gateway.log 2>&1 &
sleep 5

# 验证 Gateway
curl -s http://127.0.0.1:19999/api/health

# 启动 MCP Gateway
nohup python main_mcp.py > /tmp/mcp.log 2>&1 &

# 启动 Workers（必须设置 NOVAIC_GATEWAY_URL）
nohup python main_watchdog.py > /tmp/watchdog.log 2>&1 &
nohup python main_task.py > /tmp/task.log 2>&1 &
nohup python main_saga.py > /tmp/saga.log 2>&1 &
nohup python main_health.py > /tmp/health.log 2>&1 &

sleep 3

# 验证进程数（应该是 6 个）
ps aux | grep "python.*main_" | grep -v grep | wc -l
```

### 4. 验证服务状态

```bash
# Gateway 健康检查
curl -s http://127.0.0.1:19999/api/health

# MCP Gateway 健康检查
curl -s http://127.0.0.1:19998/api/health
```

---

## 冒烟测试流程

### Step 1: 配置 LLM API Key

**重要**: 必须先配置 API Key 才能完成 LLM 调用测试。

#### 方法 A: 从 Tauri 应用数据库复制

```bash
# 查看 Tauri 应用的 API key
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, name, provider, api_base FROM api_keys;"

# 复制到开发数据库
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT * FROM api_keys;" | while IFS='|' read id name provider api_key api_base deployment api_version created; do
  sqlite3 ~/.novaic/novaic.db "INSERT OR REPLACE INTO api_keys (id, name, provider, api_key, api_base, deployment_name, api_version, created_at) VALUES ('$id', '$name', '$provider', '$api_key', '$api_base', '$deployment', '$api_version', '$created');"
done
```

#### 方法 B: 通过 API 添加

```bash
curl -X POST http://127.0.0.1:19999/api/config/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "name": "My API Key",
    "api_key": "sk-xxx",
    "api_base": "https://api.openai.com/v1"
  }'
```

### Step 2: 配置可用模型

```bash
# 添加模型到 candidate_models
sqlite3 ~/.novaic/novaic.db "INSERT OR REPLACE INTO candidate_models (id, name, provider, api_key_id, available, is_custom) VALUES ('kimi-k2.5', 'kimi-k2.5', 'openai', '<your-api-key-id>', 1, 0);"

# 设置默认模型
sqlite3 ~/.novaic/novaic.db "UPDATE config SET value = '\"kimi-k2.5\"' WHERE key = 'default_model';"

# 验证配置
curl -s http://127.0.0.1:19999/api/config
```

**重要**: 配置 API Key 和模型后，需要**重启 Gateway** 才能生效！

```bash
pkill -f "python.*main_gateway"
sleep 2
nohup python main_gateway.py > /tmp/gateway.log 2>&1 &
sleep 5

# 验证 LLM 配置
strings /tmp/gateway.log | grep "LLM client"
# 应该看到: [Gateway] LLM client configured: openai
```

### Step 3: 创建 Agent 和 SubAgent

```bash
# 创建 Agent
AGENT_RESPONSE=$(curl -s -X POST http://127.0.0.1:19999/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "smoke-test"}')
echo $AGENT_RESPONSE

# 获取 Agent ID
AGENT_ID=$(echo $AGENT_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Agent ID: $AGENT_ID"
```

**重要**: 必须创建 SubAgent，否则消息无法路由！

```bash
# SubAgent ID 格式: main-{agent_id前8位}
SUBAGENT_ID="main-${AGENT_ID:0:8}"

# 创建 SubAgent
sqlite3 ~/.novaic/novaic.db "INSERT INTO subagents (subagent_id, agent_id, type, status, created_at) VALUES ('$SUBAGENT_ID', '$AGENT_ID', 'main', 'sleeping', datetime('now'));"

# 验证
sqlite3 ~/.novaic/novaic.db "SELECT subagent_id, agent_id, status FROM subagents;"
```

### Step 4: 发送消息并验证

```bash
# 发送消息
curl -s -X POST http://127.0.0.1:19999/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "请回复 pong"}'

# 等待处理（LLM 调用需要时间）
sleep 30

# 检查 LLM 任务结果
sqlite3 ~/.novaic/novaic.db "SELECT topic, status, substr(result, 1, 100) FROM tq_tasks WHERE topic = 'llm.call' ORDER BY created_at DESC LIMIT 1;"

# 检查聊天消息
sqlite3 ~/.novaic/novaic.db "SELECT type, substr(content, 1, 80) FROM chat_messages ORDER BY timestamp DESC LIMIT 5;"
```

---

## 状态检查命令

### 服务进程

```bash
ps aux | grep "python.*main_" | grep -v grep
```

### Saga 状态

```bash
sqlite3 ~/.novaic/novaic.db "SELECT id, saga_type, status, current_step FROM tq_sagas ORDER BY created_at DESC LIMIT 5;"
```

### Task 状态

```bash
sqlite3 ~/.novaic/novaic.db "SELECT id, topic, status FROM tq_tasks WHERE status != 'done' ORDER BY created_at DESC LIMIT 10;"
```

### Task 分布统计

```bash
sqlite3 ~/.novaic/novaic.db "SELECT topic, status, count(*) FROM tq_tasks GROUP BY topic, status ORDER BY status, topic;"
```

### Runtime 状态

```bash
sqlite3 ~/.novaic/novaic.db "SELECT runtime_id, status, phase, need_rest FROM agent_runtimes ORDER BY created_at DESC LIMIT 3;"
```

### SubAgent 状态

```bash
sqlite3 ~/.novaic/novaic.db "SELECT subagent_id, agent_id, type, status FROM subagents;"
```

### 查看日志

```bash
# Gateway 日志（包含 HTTP 请求）
tail -20 /tmp/gateway.log

# Watchdog 日志（消息检测）
tail -20 /tmp/watchdog.log

# Task Worker 日志（Handler 执行）
tail -20 /tmp/task.log

# 注意：日志文件可能很大，用 tail 而不是 cat
```

---

## 常见问题和解决方案

### 1. "SubAgent not found"

**原因**: Agent 创建后没有对应的 SubAgent 记录。

**解决方案**:
```bash
# SubAgent ID 格式必须是 main-{agent_id前8位}
AGENT_ID="59361ea4-4218-4dc3-a4b8-287e6e6b2406"
SUBAGENT_ID="main-${AGENT_ID:0:8}"  # main-59361ea4

sqlite3 ~/.novaic/novaic.db "INSERT INTO subagents (subagent_id, agent_id, type, status, created_at) VALUES ('$SUBAGENT_ID', '$AGENT_ID', 'main', 'sleeping', datetime('now'));"
```

### 2. "LLM client not configured"

**原因**: Gateway 启动时 API Key 未配置，或配置后未重启 Gateway。

**解决方案**:
1. 检查 API Key 配置
   ```bash
   sqlite3 ~/.novaic/novaic.db "SELECT id, name, provider FROM api_keys;"
   ```
2. 检查 candidate_models 配置
   ```bash
   sqlite3 ~/.novaic/novaic.db "SELECT * FROM candidate_models;"
   ```
3. **重启 Gateway**
   ```bash
   pkill -f "python.*main_gateway"
   nohup python main_gateway.py > /tmp/gateway.log 2>&1 &
   sleep 5
   strings /tmp/gateway.log | grep "LLM client"
   ```

### 3. 模型不存在错误 (404 / "model not found")

**原因**: default_model 配置的模型名与 API Provider 不匹配。

**示例**: 配置了 Kimi API (moonshot)，但 default_model 是 `gpt-4o`。

**解决方案**:
```bash
# 检查当前配置
sqlite3 ~/.novaic/novaic.db "SELECT value FROM config WHERE key = 'default_model';"

# 更新为正确的模型名
sqlite3 ~/.novaic/novaic.db "UPDATE config SET value = '\"kimi-k2.5\"' WHERE key = 'default_model';"

# 重启 Gateway
```

### 4. Task Worker 频繁退出

**原因**: Handler 执行出错，Worker 没有正确处理异常。

**诊断**:
```bash
# 检查 task.log 最后几行
tail -20 /tmp/task.log
```

**临时解决**:
```bash
# 重启 Task Worker
pkill -f "python.*main_task"
nohup python main_task.py > /tmp/task.log 2>&1 &
```

### 5. Saga 卡在 running 状态

**原因**: 
- Task Worker 未运行
- Handler 执行超时
- 依赖的任务失败

**诊断**:
```bash
# 检查 pending/claimed 任务
sqlite3 ~/.novaic/novaic.db "SELECT topic, status, count(*) FROM tq_tasks WHERE status IN ('pending', 'claimed') GROUP BY topic, status;"

# 检查 saga 的 step_results
sqlite3 ~/.novaic/novaic.db "SELECT step_results FROM tq_sagas WHERE id = '<saga-id>';"
```

### 6. Context 中有空消息

**原因**: 之前失败的 LLM 调用留下了无效数据。

**解决方案**: 清理 runtime 数据，重新开始
```bash
sqlite3 ~/.novaic/novaic.db "DELETE FROM agent_runtimes; DELETE FROM tq_sagas; DELETE FROM tq_tasks;"
sqlite3 ~/.novaic/novaic.db "UPDATE subagents SET status = 'sleeping';"
```

---

## 清理和重置

### 完全重置

```bash
# 停止所有服务
pkill -9 -f "python.*main_" 2>/dev/null

# 删除数据库
rm -f ~/.novaic/novaic.db

# 清理日志
rm -f /tmp/*.log

# 重新启动
```

### 部分重置（保留配置）

```bash
# 只清理运行时数据
sqlite3 ~/.novaic/novaic.db "
DELETE FROM agent_runtimes;
DELETE FROM tq_sagas;
DELETE FROM tq_tasks;
DELETE FROM chat_messages;
UPDATE subagents SET status = 'sleeping';
"
```

---

## 验证清单

冒烟测试通过标准：

- [ ] Gateway 健康检查返回 `healthy`
- [ ] MCP Gateway 健康检查返回 `ok`
- [ ] 6 个服务进程都在运行
- [ ] API Key 和模型已配置
- [ ] Gateway 日志显示 `LLM client configured`
- [ ] Agent 和 SubAgent 已创建
- [ ] 发送消息后 `llm.call` 任务 `success: true`
- [ ] LLM 响应包含预期内容

---

## 标杆案例：2026-02-03 冒烟测试闭环

本案例作为 v22+ 的默认基准，用于验证 Task Queue v2 + Saga + MCP 完整闭环。

### 目标

- `ping` 消息触发完整链路
- `llm.call` 成功返回
- `react_think` / `react_actions` 全部完成
- `tool.execute` 成功执行 `chat_reply` 和 `runtime_rest`
- `chat_messages` 写入 `AGENT_REPLY`

### 关键修复清单（必须具备）

- `saga.trigger` 使用异步 `create()`，避免 Gateway 内同步执行阻塞
- MCP 创建走 Gateway → MCP Gateway 代理，写入完整 `mcp_url`
- `tool.execute` 使用 MCP Gateway HTTP client
- MCP URL 统一使用带 `/` 结尾的 mount path
- TaskQueue 并发写入加锁，避免 `sqlite3.OperationalError: cannot commit transaction - SQL statements in progress`

### 快速复现命令

```bash
# 1) 启动并清理运行态
pkill -9 -f "python.*main_" 2>/dev/null
cd /path/to/novaic/novaic-backend
source venv/bin/activate
export NOVAIC_DATA_DIR=~/.novaic
export NOVAIC_GATEWAY_URL=http://127.0.0.1:19999
export NOVAIC_MCP_GATEWAY_URL=http://127.0.0.1:19998
export PYTHONUNBUFFERED=1

nohup python main_gateway.py > /tmp/gateway.log 2>&1 &
sleep 5
nohup python main_mcp.py > /tmp/mcp.log 2>&1 &
nohup python main_watchdog.py > /tmp/watchdog.log 2>&1 &
nohup python main_task.py > /tmp/task.log 2>&1 &
nohup python main_saga.py > /tmp/saga.log 2>&1 &
nohup python main_health.py > /tmp/health.log 2>&1 &
sleep 3

sqlite3 ~/.novaic/novaic.db "
DELETE FROM agent_runtimes;
DELETE FROM tq_sagas;
DELETE FROM tq_tasks;
DELETE FROM chat_messages;
UPDATE subagents SET status = 'sleeping';
"

# 2) 发送测试消息
curl -s -X POST http://127.0.0.1:19999/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "ping"}'

# 3) 等待并验证
sleep 35
sqlite3 ~/.novaic/novaic.db "SELECT id, topic, status, substr(result, 1, 200) FROM tq_tasks ORDER BY created_at DESC LIMIT 10;"
sqlite3 ~/.novaic/novaic.db "SELECT id, saga_type, status, current_step FROM tq_sagas ORDER BY created_at DESC LIMIT 5;"
sqlite3 ~/.novaic/novaic.db "SELECT type, substr(content, 1, 120) FROM chat_messages ORDER BY timestamp DESC LIMIT 5;"
```

### 验证标准（期望输出）

- `tool.execute` 对 `chat_reply` 与 `runtime_rest` 均为 `success: true`
- `react_think` / `react_actions` `status=completed`
- `chat_messages` 出现 `AGENT_REPLY`（包含 LLM 回复）

---

## 已知问题

### Saga 卡在 running 状态

**现象**: `saga.trigger` 任务长期处于 `claimed`，没有进入 `done`

**可能原因**:
- Task Worker 执行完 handler 后没有完成任务（`/internal/tq/tasks/{id}/complete` 未调用或失败）
- Gateway 在 complete 时返回错误

**排查建议**:
```bash
# 检查 Task Worker 是否还有后续日志
tail -20 /tmp/task.log

# 检查 Gateway 是否收到 complete 请求
tail -20 /tmp/gateway.log
```
