# NovAIC 后端调试指南

本文档总结了调试 NovAIC 后端问题的系统方法和技巧。

## 目录

1. [服务状态检查](#1-服务状态检查)
2. [数据库状态查询](#2-数据库状态查询)
3. [日志分析](#3-日志分析)
4. [API 测试](#4-api-测试)
5. [常见问题诊断](#5-常见问题诊断)
6. [修复操作](#6-修复操作)

---

## 1. 服务状态检查

### 1.1 检查进程是否运行

```bash
# 检查所有后端进程
ps aux | grep -E "main_gateway|main_tools|queue_service|saga_worker|task_worker|watchdog" | grep -v grep

# 检查特定进程
ps aux | grep main_gateway | grep -v grep
```

### 1.2 检查端口监听

```bash
# 检查关键端口
lsof -i :19999 -i :19998 -i :19997

# 各端口对应服务：
# - 19999: Gateway (主 API 和数据库)
# - 19998: Tools Server (工具调用服务)
# - 19997: Queue Service (任务/Saga 队列)
```

### 1.3 健康检查 API

```bash
# Gateway 健康检查
curl http://127.0.0.1:19999/api/health

# Tools Server 健康检查
curl http://127.0.0.1:19998/api/health

# Queue Service 健康检查
curl http://127.0.0.1:19997/health
```

---

## 2. 数据库状态查询

数据库位置: `~/Library/Application Support/com.novaic.app/`
- `novaic.db` - 主数据库 (Agent、消息、Runtime 等)
- `queue.db` - 队列数据库 (Task、Saga)

### 2.1 检查消息状态

```bash
# 查看最近消息
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, content, status, created_at FROM chat_messages ORDER BY created_at DESC LIMIT 5;"

# 消息状态说明：
# - sending: 等待处理
# - sent: 已发送（可能是问题状态）
# - delivered: 已处理
```

### 2.2 检查 Runtime 状态

```bash
# 查看活跃 Runtime
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT runtime_id, status, phase, created_at FROM agent_runtimes WHERE status='active' ORDER BY created_at DESC LIMIT 5;"

# Runtime phase 说明：
# - init: 初始化中
# - thinking: AI 思考中
# - waiting_actions: 等待工具执行
# - completed: 已完成
```

### 2.3 检查 Subagent 状态

```bash
# 查看 Subagent 状态
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT subagent_id, agent_id, status FROM subagents LIMIT 5;"

# 状态说明：
# - sleeping: 休眠中（等待消息唤醒）
# - awake: 已唤醒（正在处理）
```

### 2.4 检查 Saga 状态

```bash
# 查看最近 Saga
sqlite3 ~/Library/Application\ Support/com.novaic.app/queue.db \
  "SELECT saga_id, saga_type, status, error, created_at FROM tq_sagas ORDER BY created_at DESC LIMIT 5;"

# Saga 类型：
# - message_process: 消息处理
# - runtime_start: Runtime 启动
# - react_think: AI 思考循环
# - react_actions: 工具执行

# 状态：
# - pending: 等待执行
# - running: 执行中
# - completed: 已完成
# - failed: 失败
```

### 2.5 检查 Task 状态

```bash
# 查看最近 Task
sqlite3 ~/Library/Application\ Support/com.novaic.app/queue.db \
  "SELECT task_id, topic, status, error FROM tq_tasks ORDER BY created_at DESC LIMIT 10;"
```

---

## 3. 日志分析

日志位置: `~/Library/Application Support/com.novaic.app/logs/`

### 3.1 查看最新日志

```bash
# Gateway 日志
tail -100 ~/Library/Application\ Support/com.novaic.app/logs/gateway-*.log

# Saga Worker 日志
tail -100 ~/Library/Application\ Support/com.novaic.app/logs/saga-worker-*.log

# Task Worker 日志
tail -100 ~/Library/Application\ Support/com.novaic.app/logs/task-worker-*.log
```

### 3.2 搜索错误

```bash
# 搜索所有日志中的错误
grep -i "error\|exception\|failed" ~/Library/Application\ Support/com.novaic.app/logs/*.log | tail -30

# 搜索特定关键词
grep -i "tools\|mcp\|connection" ~/Library/Application\ Support/com.novaic.app/logs/*.log | tail -20
```

### 3.3 Tools Server 日志

```bash
# 如果使用 nohup 启动
tail -50 /tmp/tools_server.log
```

---

## 4. API 测试

### 4.1 Tools Server API

```bash
# 健康检查
curl http://127.0.0.1:19998/api/health

# 查看 Runtime 列表
curl http://127.0.0.1:19998/internal/runtimes

# 创建 Runtime 上下文
curl -X POST http://127.0.0.1:19998/internal/runtimes \
  -H "Content-Type: application/json" \
  -d '{"runtime_id": "rt-test", "agent_id": "agent-test", "subagent_id": "main-test", "ports": {}}'

# 获取工具列表
curl http://127.0.0.1:19998/internal/runtimes/rt-test/tools

# 调用工具
curl -X POST http://127.0.0.1:19998/internal/runtimes/rt-test/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "runtime_list", "arguments": {}}'

# 获取统计信息
curl http://127.0.0.1:19998/internal/stats

# 删除 Runtime
curl -X DELETE http://127.0.0.1:19998/internal/runtimes/rt-test
```

### 4.2 Gateway API

```bash
# 获取活跃 Runtime 列表
curl http://127.0.0.1:19999/internal/runtimes/list

# 获取 Agent 列表
curl http://127.0.0.1:19999/api/agents
```

### 4.3 Queue Service API

```bash
# 健康检查
curl http://127.0.0.1:19997/health

# 获取 Saga 统计
curl http://127.0.0.1:19997/api/sagas/stats
```

---

## 5. 常见问题诊断

### 5.1 消息发送无响应

**诊断步骤：**

1. 检查服务状态
```bash
lsof -i :19999 -i :19998 -i :19997
```

2. 检查消息状态
```bash
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, status FROM chat_messages ORDER BY created_at DESC LIMIT 3;"
```

3. 检查 Saga 状态
```bash
sqlite3 ~/Library/Application\ Support/com.novaic.app/queue.db \
  "SELECT saga_id, saga_type, status, error FROM tq_sagas ORDER BY created_at DESC LIMIT 5;"
```

4. 检查 Runtime 状态
```bash
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT runtime_id, status, phase FROM agent_runtimes WHERE status='active';"
```

**常见原因：**
- Tools Server 未启动 (端口 19998 无监听)
- Runtime 卡在 `waiting_actions` 状态
- Subagent 状态不正确
- Saga 失败

### 5.2 Runtime 卡住

**症状：** Runtime 长时间处于 `active` 状态，phase 为 `waiting_actions`

**诊断：**
```bash
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT runtime_id, status, phase, pending_actions FROM agent_runtimes WHERE status='active';"
```

**解决：** 见 [6.2 重置卡住的 Runtime](#62-重置卡住的-runtime)

### 5.3 工具调用失败

**诊断：**
```bash
# 检查 Tools Server 是否运行
curl http://127.0.0.1:19998/api/health

# 检查日志
grep -i "tool\|error" /tmp/tools_server.log | tail -20
```

---

## 6. 修复操作

### 6.1 重启服务

```bash
# 杀掉旧进程
pkill -f "main_tools.py"
pkill -f "saga_worker"
pkill -f "task_worker"

# 重启 Tools Server
cd /path/to/novaic/novaic-backend
export NOVAIC_DATA_DIR=~/Library/Application\ Support/com.novaic.app
export GATEWAY_URL=http://127.0.0.1:19999
nohup python main_tools.py --port 19998 > /tmp/tools_server.log 2>&1 &

# 重启 Workers
export QUEUE_SERVICE_URL=http://127.0.0.1:19997
export NOVAIC_TOOLS_SERVER_URL=http://127.0.0.1:19998
nohup python -m task_queue.workers.saga_worker_sync > /tmp/saga_worker.log 2>&1 &
nohup python -m task_queue.workers.task_worker_sync > /tmp/task_worker.log 2>&1 &
```

### 6.2 重置卡住的 Runtime

```bash
# 1. 找到卡住的 Runtime
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT runtime_id, agent_id FROM agent_runtimes WHERE status='active' AND phase='waiting_actions';"

# 2. 重置 Runtime 状态
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "UPDATE agent_runtimes SET status='completed', phase='completed' WHERE runtime_id='rt-xxx';"

# 3. 重置 Subagent 状态
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "UPDATE subagents SET status='sleeping' WHERE subagent_id='main-xxx';"
```

### 6.3 清理失败的 Saga

```bash
# 将 running 状态的 Saga 标记为失败
sqlite3 ~/Library/Application\ Support/com.novaic.app/queue.db \
  "UPDATE tq_sagas SET status='failed', error='Manual cleanup' WHERE status='running';"
```

### 6.4 重置消息状态

```bash
# 将 sent 状态的消息改为 sending（重新触发处理）
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "UPDATE chat_messages SET status='sending' WHERE status='sent' AND id='msg-xxx';"
```

---

## 7. 调试流程总结

### 完整诊断流程

```bash
# 1. 检查服务
lsof -i :19999 -i :19998 -i :19997

# 2. 检查健康
curl -s http://127.0.0.1:19999/api/health
curl -s http://127.0.0.1:19998/api/health
curl -s http://127.0.0.1:19997/health

# 3. 检查消息
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, status FROM chat_messages ORDER BY created_at DESC LIMIT 5;"

# 4. 检查 Saga
sqlite3 ~/Library/Application\ Support/com.novaic.app/queue.db \
  "SELECT saga_type, status, error FROM tq_sagas ORDER BY created_at DESC LIMIT 5;"

# 5. 检查 Runtime
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT runtime_id, status, phase FROM agent_runtimes ORDER BY created_at DESC LIMIT 3;"

# 6. 检查日志
grep -i "error" ~/Library/Application\ Support/com.novaic.app/logs/*.log | tail -10
```

### 快速修复脚本

```bash
#!/bin/bash
# quick-fix.sh - 快速修复常见问题

DATA_DIR=~/Library/Application\ Support/com.novaic.app

echo "=== 1. 检查服务状态 ==="
lsof -i :19999 -i :19998 -i :19997 2>/dev/null

echo -e "\n=== 2. 重置卡住的 Runtime ==="
sqlite3 "$DATA_DIR/novaic.db" "UPDATE agent_runtimes SET status='completed' WHERE status='active' AND phase='waiting_actions';"

echo -e "\n=== 3. 重置 Subagent 状态 ==="
sqlite3 "$DATA_DIR/novaic.db" "UPDATE subagents SET status='sleeping' WHERE status='awake';"

echo -e "\n=== 4. 清理失败的 Saga ==="
sqlite3 "$DATA_DIR/queue.db" "UPDATE tq_sagas SET status='failed' WHERE status='running';"

echo -e "\n=== 修复完成 ==="
```

---

## 8. 架构参考

```
┌─────────────────────────────────────────────────────────────────┐
│                        NovAIC Backend                            │
├─────────────────────┬───────────────────┬───────────────────────┤
│  Gateway (19999)    │  Tools Server     │  Queue Service        │
│  • 数据库操作       │  (19998)          │  (19997)              │
│  • Internal API     │  • 32个内置工具   │  • Task 队列          │
│  • 用户/Agent管理   │  • 外部MCP发现    │  • Saga 编排          │
└─────────────────────┴───────────────────┴───────────────────────┘
         │                    │                      │
         └────────────────────┼──────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         Saga Worker    Task Worker      Watchdog
         (Saga 执行)    (Task 执行)    (状态监控)
```

### 数据流

1. 用户发送消息 → Gateway 存储消息 (`status='sending'`)
2. Watchdog 检测到新消息 → 创建 `message_process` Saga
3. Saga Worker 执行 Saga → 创建/唤醒 Runtime
4. Runtime 进入 `react_think` 循环 → 调用 LLM
5. LLM 返回工具调用 → 创建 `react_actions` Saga
6. Task Worker 执行工具 → 通过 Tools Server HTTP API
7. 工具结果返回 → 继续 `react_think` 循环
8. 完成后 Runtime 进入 rest 状态

---

*最后更新: 2026-02-05*
