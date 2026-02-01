# 常见问题排查

## 1. MCP 工具发现为 0

### 现象
```
[ToolRegistry] Discovered 0 tools from local
[ToolRegistry] Discovered 0 tools from qemudebug
```

### 原因
- MCP Gateway (19998) 未启动
- Worker 把 MCP 请求发到 Gateway (19999) 而不是 MCP Gateway

### 解决
```bash
# 确认 MCP Gateway 在跑
curl -s http://127.0.0.1:19998/internal/mcp/stats

# 如果返回 000 或连接失败，启动 MCP Gateway
./dev-guide/run-dev.sh mcp-gateway
```

---

## 2. POST .../mcp/... 返回 405

### 现象
```
INFO: "POST /agents/.../mcp/local/ HTTP/1.1" 405 Method Not Allowed
```

### 原因
- 请求发到了 Gateway (19999)，但 Gateway 上没有 MCP 路由
- MCP 路由在 MCP Gateway (19998) 上

### 解决
- 确保 MCP Gateway 启动
- 确保 Worker/Master 配置了正确的 `--mcp-gateway-url`
- 检查 DB 中 runtime 的 `mcp_url` 是否是完整 URL

---

## 3. 日志显示旧架构（MCPManager/ProcessManager 在 Gateway 内）

### 现象
```
[MCPManager] Initialized
[ProcessManager] Starting with config: min=2, max=5
[Gateway] Master started (v12 architecture)
```

### 原因
- 运行的是旧版本代码/构建
- 新架构的 Gateway 不应该有这些日志

### 解决
- 确认使用最新代码：`git status`
- 如果用 Tauri App，需要重新 build：`./build.sh`
- 如果用 Python 开发模式，确认 `main.py` 里没有 MCPManager 初始化

---

## 4. DB 中 mcp_url 是相对路径

### 现象
```sql
SELECT mcp_url FROM agent_runtimes;
-- 返回: /mcp/aggregate/main-xxx/
```

### 原因
- 旧代码创建的 runtime 使用相对路径
- 新代码应该返回完整 URL

### 解决
```bash
# 清理旧数据
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "DELETE FROM agent_runtimes WHERE status='completed';"

# 或手动更新
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "UPDATE agent_runtimes SET mcp_url='http://127.0.0.1:19998' || mcp_url WHERE mcp_url LIKE '/%';"
```

---

## 5. Worker 连接不上 Gateway SSE

### 现象
```
[Worker] Connection error: Cannot connect to host 127.0.0.1:19999
[Worker] Max reconnect attempts reached, shutting down
```

### 原因
- Gateway 未启动或已崩溃
- Worker 启动时 Gateway 还没就绪

### 解决
```bash
# 检查 Gateway
curl -s http://127.0.0.1:19999/api/health

# 查看 Gateway 日志
tail -50 /tmp/gateway.log

# 重启
./dev-guide/run-dev.sh
```

---

## 6. MCP 请求返回 406 Not Acceptable

### 现象
```json
{"error":{"code":-32600,"message":"Not Acceptable: Client must accept text/event-stream"}}
```

### 原因
- MCP HTTP 协议要求 `Accept: application/json, text/event-stream`

### 解决
- 正常 MCP 客户端会自动添加正确头
- 手动测试时需要加头：
```bash
curl -X POST http://127.0.0.1:19998/mcp/aggregate/xxx/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}'
```

---

## 7. Master 调用 MCP Gateway 返回 500

### 现象
```
ValueError: Runtime MCP for xxx not found. Call create_runtime_server first.
```

### 原因
- 创建 Aggregate 前需要先创建 Runtime MCP
- 正确顺序: Agent Shared → Runtime → Aggregate

### 解决
按顺序调用：
```bash
# 1. Agent Shared
curl -X POST http://127.0.0.1:19998/internal/mcp/agent-shared \
  -d '{"agent_id": "xxx"}'

# 2. Runtime
curl -X POST http://127.0.0.1:19998/internal/mcp/runtime \
  -d '{"subagent_id": "main-xxx", "agent_id": "xxx"}'

# 3. Aggregate
curl -X POST http://127.0.0.1:19998/internal/mcp/aggregate \
  -d '{"subagent_id": "main-xxx", "agent_id": "xxx"}'
```

---

## 快速诊断命令

```bash
# 一键检查所有服务
./dev-guide/run-dev.sh status

# 检查 Gateway
curl -s http://127.0.0.1:19999/api/system/status | python -m json.tool | head -20

# 检查 MCP Gateway
curl -s http://127.0.0.1:19998/internal/mcp/stats | python -m json.tool

# 检查 DB
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db ".tables"
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT subagent_id, mcp_url, status FROM agent_runtimes;"

# 查看最近日志
tail -50 /tmp/gateway.log
tail -50 /tmp/mcp_gateway.log
tail -50 /tmp/master.log
tail -50 /tmp/worker.log
```
