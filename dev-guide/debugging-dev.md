# 开发环境调试指南

> **重要**: 开发模式下没有 Web UI，所有测试通过 API 进行。

## 启动服务（异步模式）

使用 `nohup` 后台启动服务，日志输出到 `/tmp/*.log`，避免日志刷屏。

### 1. 设置环境变量

```bash
export NOVAIC_DATA_DIR=~/.novaic
export NOVAIC_GATEWAY_URL=http://127.0.0.1:19999
```

### 2. 启动 Gateway

```bash
cd /Users/wangchaoqun/novaic/novaic-gateway
source venv/bin/activate
nohup python main.py > /tmp/gateway.log 2>&1 &
sleep 4

# 验证
curl -s http://127.0.0.1:19999/api/health
```

### 3. 启动 MCP Gateway

```bash
nohup python mcp_main.py > /tmp/mcp-gateway.log 2>&1 &
sleep 3

# 验证
curl -s http://127.0.0.1:19998/api/health
```

### 4. 启动 Worker 服务

```bash
GATEWAY_URL=http://127.0.0.1:19999

nohup python monitor_main.py --gateway-url $GATEWAY_URL > /tmp/monitor.log 2>&1 &
nohup python launcher_main.py --gateway-url $GATEWAY_URL > /tmp/launcher.log 2>&1 &
nohup python collector_main.py --gateway-url $GATEWAY_URL > /tmp/collector.log 2>&1 &
nohup python executor_main.py --gateway-url $GATEWAY_URL > /tmp/executor.log 2>&1 &
nohup python health_main.py --gateway-url $GATEWAY_URL > /tmp/health.log 2>&1 &

sleep 3

# 验证进程数量 (应该是 7 个)
ps aux | grep -E "python.*(main|_main)" | grep -v grep | wc -l
```

### 一键启动脚本

```bash
#!/bin/bash
cd /Users/wangchaoqun/novaic/novaic-gateway
source venv/bin/activate
export NOVAIC_DATA_DIR=~/.novaic
GATEWAY_URL=http://127.0.0.1:19999

# 停止旧进程
pkill -9 -f "python.*(main|_main).py" 2>/dev/null
sleep 2

# 启动 Gateway
nohup python main.py > /tmp/gateway.log 2>&1 &
sleep 4
curl -s http://127.0.0.1:19999/api/health || exit 1

# 启动 MCP Gateway
export NOVAIC_GATEWAY_URL=$GATEWAY_URL
nohup python mcp_main.py > /tmp/mcp-gateway.log 2>&1 &
sleep 3

# 启动 Workers
nohup python monitor_main.py --gateway-url $GATEWAY_URL > /tmp/monitor.log 2>&1 &
nohup python launcher_main.py --gateway-url $GATEWAY_URL > /tmp/launcher.log 2>&1 &
nohup python collector_main.py --gateway-url $GATEWAY_URL > /tmp/collector.log 2>&1 &
nohup python executor_main.py --gateway-url $GATEWAY_URL > /tmp/executor.log 2>&1 &
nohup python health_main.py --gateway-url $GATEWAY_URL > /tmp/health.log 2>&1 &

echo "All services started. Logs in /tmp/*.log"
```

---

## API 测试（无 Web UI）

### 创建 Agent

```bash
curl -s -X POST http://127.0.0.1:19999/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "test-agent"}' | jq .

# 保存返回的 agent_id
AGENT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### 发送消息

```bash
curl -s -X POST http://127.0.0.1:19999/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "hello test"}' | jq .
```

### 检查消息状态

```bash
sqlite3 ~/.novaic/novaic.db \
  "SELECT id, type, status, substr(content, 1, 50) FROM chat_messages ORDER BY timestamp DESC LIMIT 5;"
```

### 检查 Runtime 状态

```bash
sqlite3 ~/.novaic/novaic.db \
  "SELECT runtime_id, status, current_round_num, phase FROM agent_runtimes ORDER BY created_at DESC LIMIT 3;"
```

### 检查 SubAgent 状态

```bash
sqlite3 ~/.novaic/novaic.db \
  "SELECT subagent_id, agent_id, status FROM subagents;"
```

### 检查任务状态

```bash
sqlite3 ~/.novaic/novaic.db \
  "SELECT task_subtype, status, created_at FROM pipeline_tasks ORDER BY created_at DESC LIMIT 10;"
```

---

## 日志监控

### 实时查看所有日志

```bash
tail -f /tmp/gateway.log /tmp/mcp-gateway.log /tmp/monitor.log \
       /tmp/launcher.log /tmp/collector.log /tmp/executor.log /tmp/health.log
```

### 单独查看某个服务

```bash
tail -f /tmp/monitor.log     # Monitor 服务
tail -f /tmp/launcher.log    # Launcher 服务
tail -f /tmp/executor.log    # Executor 服务 (LLM/MCP 调用)
tail -f /tmp/collector.log   # Collector 服务
```

### 查看 Gateway HTTP 请求

```bash
tail -f /tmp/gateway.log | grep -E "POST|GET|PATCH|DELETE"
```

---

## 常用调试命令

### 停止所有服务

```bash
pkill -9 -f "python.*(main|_main).py"
```

### 检查进程状态

```bash
ps aux | grep -E "python.*(main|_main)" | grep -v grep
```

### 清理数据库（重新开始）

```bash
rm ~/.novaic/novaic.db
# 重启 Gateway 会自动创建新数据库
```

### 检查端口占用

```bash
lsof -i :19999 -i :19998
```

---

## 完整测试流程

```bash
# 1. 启动所有服务
# (使用上面的启动脚本)

# 2. 创建 Agent
AGENT_ID=$(curl -s -X POST http://127.0.0.1:19999/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}' | jq -r '.id')
echo "Agent ID: $AGENT_ID"

# 3. 发送消息
curl -s -X POST http://127.0.0.1:19999/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "what is 2+2?"}'

# 4. 等待处理
sleep 10

# 5. 检查结果
sqlite3 ~/.novaic/novaic.db \
  "SELECT type, substr(content, 1, 50) FROM chat_messages ORDER BY timestamp DESC LIMIT 3;"

# 预期输出:
# AGENT_REPLY|2 + 2 = 4
# USER_MESSAGE|what is 2+2?
```

---

## 状态机验证

### 正常流程

1. **消息发送**: `status: sent`
2. **Monitor 检测**: SubAgent `sleeping` → `awaking`
3. **Runtime 创建**: 新 Runtime `active`
4. **Think 执行**: LLM 生成回复
5. **Actions 执行**: tool_call 执行
6. **Summarize**: Runtime `completed`, SubAgent `sleeping`

### 状态查询

```bash
# SubAgent 状态流转
watch -n 2 'sqlite3 ~/.novaic/novaic.db "SELECT subagent_id, status FROM subagents;"'

# Runtime 状态流转
watch -n 2 'sqlite3 ~/.novaic/novaic.db "SELECT runtime_id, status, phase FROM agent_runtimes ORDER BY created_at DESC LIMIT 1;"'

# 任务执行状态
watch -n 2 'sqlite3 ~/.novaic/novaic.db "SELECT task_subtype, status FROM pipeline_tasks ORDER BY created_at DESC LIMIT 5;"'
```
