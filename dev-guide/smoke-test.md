# 后端冒烟测试指南

> **更新时间**: 2026-02-04  
> **适用版本**: v22+ (Task Queue v2 + Saga 架构)  
> **最新修复**: 旧修复记录已归档，本文档已按当前严格 Runtime Orchestrator 架构更新。

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
│ main_tools.py     │ Tools Server (19998) - 工具服务管理 │
│ main_queue.py     │ Queue Service (19997) - 队列服务    │
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
rm -f ~/.novaic/gateway.db ~/.novaic/runtime_orchestrator.db ~/.novaic/queue.db

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

# 启动 Tools Server
nohup python main_tools.py > /tmp/tools.log 2>&1 &

# 启动 Queue Service
nohup python main_queue.py > /tmp/queue.log 2>&1 &

# 启动 Workers（必须设置 NOVAIC_GATEWAY_URL）
nohup python main_watchdog.py > /tmp/watchdog.log 2>&1 &
nohup python main_task.py > /tmp/task.log 2>&1 &
nohup python main_saga.py > /tmp/saga.log 2>&1 &
nohup python main_health.py > /tmp/health.log 2>&1 &

sleep 3

# 验证进程数（应该是 7 个）
ps aux | grep "python.*main_" | grep -v grep | wc -l
```

### 4. 验证服务状态

```bash
# Gateway 健康检查
curl -s http://127.0.0.1:19999/api/health

# Tools Server 健康检查
curl -s http://127.0.0.1:19998/api/health

# Queue Service 健康检查
curl -s http://127.0.0.1:19997/api/health
```

---

## 冒烟测试流程

### Step 1: 配置 LLM API Key 和 Model

**重要**: 必须先配置 API Key 和 Model 才能完成 LLM 调用测试。

#### 快速配置命令

```python
# 1. 添加 API Key
import httpx

with httpx.Client(trust_env=False, timeout=10.0) as client:
    r = client.post("http://127.0.0.1:19999/api/config/api-keys", json={
        "provider": "openai",  # moonshot兼容openai
        "name": "Moonshot/Kimi",
        "api_key": "sk-YOUR-REAL-KEY",
        "api_base": "https://api.moonshot.cn/v1"
    })
    key_id = r.json()['id']
    print(f"✓ API Key ID: {key_id}")
```

```python
# 2. 添加模型到 candidate_models
import sqlite3
from pathlib import Path

gateway_db = Path.home() / ".novaic" / "gateway.db"
conn = sqlite3.connect(str(gateway_db))

# 获取刚创建的api_key_id
key_id = conn.execute(
    "SELECT id FROM api_keys ORDER BY created_at DESC LIMIT 1"
).fetchone()[0]

# 插入kimi-k2.5模型
conn.execute("""
    INSERT INTO candidate_models (id, name, provider, api_key_id, available, is_custom)
    VALUES (?, ?, ?, ?, 1, 0)
""", ("model-kimi-k25", "kimi-k2.5", "openai", key_id))

conn.commit()
conn.close()
print("✓ kimi-k2.5已添加")
```

```bash
# 3. 验证配置
curl -s http://127.0.0.1:19999/internal/config/llm | python -m json.tool
```

### Step 2: 创建 Agent（自动创建SubAgent）

```bash
# 创建 Agent（指定model，自动创建SubAgent）
curl -s -X POST http://127.0.0.1:19999/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "smoke-test",
    "model": "kimi-k2.5"
  }'

# 验证
sqlite3 ~/.novaic/gateway.db "SELECT id, name, model_id FROM agents;"
sqlite3 ~/.novaic/runtime_orchestrator.db "SELECT subagent_id, agent_id FROM subagents;"
```

**注意**: 从 2026-02-04 起，创建 Agent 时会自动创建 main SubAgent，无需手动插入。

### Step 3: 发送消息并验证

```bash
# 发送消息
curl -s -X POST http://127.0.0.1:19999/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "你好！请回复：收到"}'

# 等待处理（通常5-10秒）
sleep 10

# 检查 AI 回复
sqlite3 ~/.novaic/runtime_orchestrator.db "
  SELECT type, content, timestamp 
  FROM chat_messages 
  WHERE type='AGENT_REPLY' 
  ORDER BY timestamp DESC 
  LIMIT 1;
"

# 检查任务状态
sqlite3 ~/.novaic/queue.db "
  SELECT topic, status, COUNT(*) 
  FROM tq_tasks 
  GROUP BY topic, status 
  ORDER BY topic;
"
```

**预期结果**:
- 应该看到 `AGENT_REPLY` 类型的消息
- 内容应该是 "收到"
- LLM任务和tool.execute任务都是 `done` 状态

---

## 状态检查命令

### 服务进程

```bash
ps aux | grep "python.*main_" | grep -v grep
```

### Saga 状态

```bash
sqlite3 ~/.novaic/queue.db "SELECT id, saga_type, status, current_step FROM tq_sagas ORDER BY created_at DESC LIMIT 5;"
```

### Task 状态

```bash
sqlite3 ~/.novaic/queue.db "SELECT id, topic, status FROM tq_tasks WHERE status != 'done' ORDER BY created_at DESC LIMIT 10;"
```

### Task 分布统计

```bash
sqlite3 ~/.novaic/queue.db "SELECT topic, status, count(*) FROM tq_tasks GROUP BY topic, status ORDER BY status, topic;"
```

### Runtime 状态

```bash
sqlite3 ~/.novaic/runtime_orchestrator.db "SELECT runtime_id, status, phase, need_rest FROM agent_runtimes ORDER BY created_at DESC LIMIT 3;"
```

### SubAgent 状态

```bash
sqlite3 ~/.novaic/runtime_orchestrator.db "SELECT subagent_id, agent_id, type, status FROM subagents;"
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

### 1. "SubAgent not found"（已过时）

**注意**: 从 2026-02-04 起，此问题已修复。创建 Agent 时会自动创建 main SubAgent。

如果使用旧代码，手动创建：
```bash
AGENT_ID="your-agent-id"
SUBAGENT_ID="main-${AGENT_ID:0:8}"

sqlite3 ~/.novaic/runtime_orchestrator.db "INSERT INTO subagents (subagent_id, agent_id, type, status, created_at) VALUES ('$SUBAGENT_ID', '$AGENT_ID', 'main', 'sleeping', datetime('now'));"
```

### 2. LLM 调用失败（401 / API key错误）

**原因**: API Key 未配置或配置错误。

**解决方案**:
1. 检查 API Key 配置
   ```bash
   sqlite3 ~/.novaic/gateway.db "SELECT id, name, provider, api_base FROM api_keys;"
   ```
2. 检查 candidate_models 配置
   ```bash
   sqlite3 ~/.novaic/gateway.db "SELECT name, provider, api_key_id, available FROM candidate_models;"
   ```
3. 验证 LLM 配置（不需要重启）
   ```bash
   curl -s http://127.0.0.1:19999/internal/config/llm | python -m json.tool
   ```

**注意**: 从 2026-02-04 起，LLM 配置从 DB 动态读取，无需重启 Gateway。

### 3. 模型不存在错误 (404 / "model not found")

**原因**: Agent 的 model_id 或 default_model 不在 candidate_models 中。

**解决方案**:
```bash
# 检查 agent 的 model_id
sqlite3 ~/.novaic/gateway.db "SELECT id, name, model_id FROM agents;"

# 检查可用模型
sqlite3 ~/.novaic/gateway.db "SELECT name, available FROM candidate_models;"

# 如果模型不存在，添加它（参见 Step 1）
```

**提示**: 创建 Agent 时指定 `"model": "kimi-k2.5"` 会自动使用该模型，无需修改 default_model。

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
sqlite3 ~/.novaic/queue.db "SELECT topic, status, count(*) FROM tq_tasks WHERE status IN ('pending', 'claimed') GROUP BY topic, status;"

# 检查 saga 的 step_results
sqlite3 ~/.novaic/queue.db "SELECT step_results FROM tq_sagas WHERE id = '<saga-id>';"
```

### 6. "cannot commit transaction - SQL statements in progress"

**原因**: cursor 未在 commit 前 close（已在 2026-02-04 修复）。

**状态**: 此问题已修复，错误减少 92%。如果仍出现，请报告。

### 7. Context 中有空消息（已较少见）

**原因**: 之前失败的 LLM 调用留下了无效数据。

**解决方案**: 清理 runtime 数据
```bash
sqlite3 ~/.novaic/runtime_orchestrator.db "
DELETE FROM agent_runtimes; 
DELETE FROM chat_messages;
"
sqlite3 ~/.novaic/queue.db "
DELETE FROM tq_sagas; 
DELETE FROM tq_tasks;
"
```

---

## 清理和重置

### 完全重置

```bash
# 停止所有服务
pkill -9 -f "python.*main_" 2>/dev/null

# 删除数据库
rm -f ~/.novaic/gateway.db ~/.novaic/runtime_orchestrator.db ~/.novaic/queue.db

# 清理日志
rm -f /tmp/*.log

# 重新启动
```

### 部分重置（保留配置）

```bash
# 只清理运行时数据
sqlite3 ~/.novaic/runtime_orchestrator.db "
DELETE FROM agent_runtimes;
DELETE FROM chat_messages;
UPDATE subagents SET status = 'sleeping';
"
sqlite3 ~/.novaic/queue.db "
DELETE FROM tq_sagas;
DELETE FROM tq_tasks;
"
```

---

## 验证清单

冒烟测试通过标准：

- [ ] Gateway 健康检查返回 `healthy`
- [ ] Tools Server 健康检查返回 `ok`
- [ ] Queue Service 健康检查返回 `ok`
- [ ] 7 个服务进程都在运行
- [ ] API Key 和模型已配置
- [ ] Gateway 日志显示 `LLM client configured`
- [ ] Agent 和 SubAgent 已创建
- [ ] 发送消息后 `llm.call` 任务 `success: true`
- [ ] LLM 响应包含预期内容

---

## 标杆案例：2026-02-03 冒烟测试闭环

本案例作为 v22+ 的默认基准，用于验证 Task Queue v2 + Saga + Tools Server 完整闭环。

### 目标

- `ping` 消息触发完整链路
- `llm.call` 成功返回
- `react_think` / `react_actions` 全部完成
- `tool.execute` 成功执行 `chat_reply` 和 `runtime_rest`
- `chat_messages` 写入 `AGENT_REPLY`

### 关键修复清单（必须具备）

- `saga.trigger` 使用异步 `create()`，避免 Gateway 内同步执行阻塞
- 工具创建走 Gateway → Tools Server 代理，写入完整 `tools_url`
- `tool.execute` 使用 Tools Server HTTP client
- Tools URL 统一使用带 `/` 结尾的 mount path
- TaskQueue 并发写入加锁，避免 `sqlite3.OperationalError: cannot commit transaction - SQL statements in progress`

### 快速复现命令

```bash
# 1) 启动并清理运行态
pkill -9 -f "python.*main_" 2>/dev/null
cd /path/to/novaic/novaic-backend
source venv/bin/activate
export NOVAIC_DATA_DIR=~/.novaic
export NOVAIC_GATEWAY_URL=http://127.0.0.1:19999
export NOVAIC_TOOLS_SERVER_URL=http://127.0.0.1:19998
export NOVAIC_QUEUE_SERVICE_URL=http://127.0.0.1:19997
export PYTHONUNBUFFERED=1

nohup python main_gateway.py > /tmp/gateway.log 2>&1 &
sleep 5
nohup python main_tools.py > /tmp/tools.log 2>&1 &
nohup python main_queue.py > /tmp/queue.log 2>&1 &
nohup python main_watchdog.py > /tmp/watchdog.log 2>&1 &
nohup python main_task.py > /tmp/task.log 2>&1 &
nohup python main_saga.py > /tmp/saga.log 2>&1 &
nohup python main_health.py > /tmp/health.log 2>&1 &
sleep 3

sqlite3 ~/.novaic/runtime_orchestrator.db "
DELETE FROM agent_runtimes;
DELETE FROM chat_messages;
UPDATE subagents SET status = 'sleeping';
"
sqlite3 ~/.novaic/queue.db "
DELETE FROM tq_sagas;
DELETE FROM tq_tasks;
"

# 2) 发送测试消息
curl -s -X POST http://127.0.0.1:19999/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "ping"}'

# 3) 等待并验证
sleep 35
sqlite3 ~/.novaic/queue.db "SELECT id, topic, status, substr(result, 1, 200) FROM tq_tasks ORDER BY created_at DESC LIMIT 10;"
sqlite3 ~/.novaic/queue.db "SELECT id, saga_type, status, current_step FROM tq_sagas ORDER BY created_at DESC LIMIT 5;"
sqlite3 ~/.novaic/runtime_orchestrator.db "SELECT type, substr(content, 1, 120) FROM chat_messages ORDER BY timestamp DESC LIMIT 5;"
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
