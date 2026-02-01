# MCP 调试心得

## 问题场景

2026-02-01 调试时遇到 MCP 初始化失败：
- Worker 调用 `POST .../mcp/local/` 返回 **405 Method Not Allowed**
- 日志显示 `[MCP] ✗ Failed to initialize local`
- 工具发现数为 0

## 排查过程

### 1. 检查日志

```bash
# Gateway 日志
tail -100 ~/Library/Application\ Support/com.novaic.app/logs/gateway-$(date +%Y%m%d).log

# MCP Gateway 日志（如果手动启动）
tail -100 /tmp/mcp_gateway.log
```

关键日志特征：
- `[MCPManager] Initialized` - 说明 MCP 在 Gateway 进程内（旧架构）
- `[ProcessManager] Starting` - 说明 ProcessManager 在 Gateway 内（旧架构）
- 新架构应该只看到 `[Gateway] MCP 由 Backend 组件 MCP Gateway 提供`

### 2. 检查服务状态

```bash
# Gateway 健康检查
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:19999/api/health
# 期望: 200

# MCP Gateway 状态
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:19998/internal/mcp/stats
# 期望: 200（如果 MCP Gateway 在跑）
# 期望: 000（连接失败，说明 MCP Gateway 没起）
```

### 3. 检查 DB 中的 mcp_url

```bash
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT subagent_id, mcp_url, status FROM agent_runtimes;"
```

关键判断：
- 如果 `mcp_url` 是 **相对路径**（如 `/mcp/aggregate/xxx/`）→ 旧数据，Worker 会拼到 Gateway 上导致 404/405
- 如果 `mcp_url` 是 **完整 URL**（如 `http://127.0.0.1:19998/mcp/aggregate/xxx/`）→ 新架构，Worker 会直接用

### 4. 测试 MCP 端点

```bash
# 测试 MCP 是否可访问（需要正确的 Accept 头）
curl -s -X POST http://127.0.0.1:19998/mcp/aggregate/main-xxx/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

## 根因分析

**问题 1: MCP Gateway 未启动**
- 现象: curl 19998 返回 000（连接失败）
- 解决: 启动 MCP Gateway

**问题 2: 旧数据使用相对路径**
- 现象: DB 中 `mcp_url = /mcp/aggregate/xxx/`
- 解决: 清理旧 runtime 或等新流程重建

**问题 3: 405 Method Not Allowed**
- 现象: POST 到 19999 的 MCP 路径返回 405
- 原因: Gateway 上没有 MCP 路由（MCP 在 19998）
- 解决: 确保 Worker 用 MCP Gateway URL (19998)

## 解决方案

### 方案 A: 手动启动完整环境

```bash
# 1. 杀掉旧进程
pkill -f "python main.py"
pkill -f "python mcp_main.py"
sleep 2

# 2. 启动 Gateway
cd /path/to/novaic-gateway
export NOVAIC_DATA_DIR="$HOME/Library/Application Support/com.novaic.app"
nohup python main.py > /tmp/gateway.log 2>&1 &
sleep 3

# 3. 启动 MCP Gateway
export NOVAIC_GATEWAY_URL="http://127.0.0.1:19999"
nohup python mcp_main.py > /tmp/mcp_gateway.log 2>&1 &
sleep 3

# 4. 启动 Master
nohup python master_main.py \
  --gateway-url http://127.0.0.1:19999 \
  --mcp-gateway-url http://127.0.0.1:19998 \
  > /tmp/master.log 2>&1 &

# 5. 启动 Worker
nohup python -m worker.worker \
  --gateway http://127.0.0.1:19999 \
  --mcp-gateway-url http://127.0.0.1:19998 \
  > /tmp/worker.log 2>&1 &
```

### 方案 B: 使用开发脚本

```bash
./dev-guide/run-dev.sh
```

### 方案 C: 清理旧数据重来

```bash
# 删除 completed 的旧 runtime
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "DELETE FROM agent_runtimes WHERE status='completed';"
```

## 验证方法

```bash
# 1. 检查两个服务都在跑
curl -s http://127.0.0.1:19999/api/health && echo " Gateway OK"
curl -s http://127.0.0.1:19998/internal/mcp/stats && echo " MCP Gateway OK"

# 2. 检查 MCP stats
curl -s http://127.0.0.1:19998/internal/mcp/stats | python -m json.tool

# 3. 手动创建测试 MCP
curl -s -X POST http://127.0.0.1:19998/internal/mcp/agent-shared \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "YOUR_AGENT_ID"}'

curl -s -X POST http://127.0.0.1:19998/internal/mcp/runtime \
  -H "Content-Type: application/json" \
  -d '{"subagent_id": "test-123", "agent_id": "YOUR_AGENT_ID"}'

curl -s -X POST http://127.0.0.1:19998/internal/mcp/aggregate \
  -H "Content-Type: application/json" \
  -d '{"subagent_id": "test-123", "agent_id": "YOUR_AGENT_ID"}'
```

## 经验总结

1. **先检查服务状态**: curl 19999 和 19998 确认都在跑
2. **看日志辨架构**: 有 `[MCPManager] Initialized` 说明在跑旧代码
3. **DB 是证据**: `mcp_url` 的格式能判断是新旧数据
4. **MCP 需要 Accept 头**: `Accept: application/json, text/event-stream`
5. **顺序很重要**: Gateway → MCP Gateway → Master → Worker

---

## 图片/多模态问题排查

### 问题：截图 base64 被当文本发给 LLM

MCP 协议返回图片时，格式是：
```json
{
  "content": [
    {"type": "image", "data": "iVBORw0KGgo...", "mimeType": "image/png"}
  ]
}
```

`_convert_tool_result` 会提取成：
```python
{"success": True, "screenshot": "iVBORw0KGgo...", "mime_type": "image/png"}
```

### 修复后的处理流程

1. **`worker/llm_caller.py` 的 `add_tool_result`**：
   - 检测 `screenshot` + `mime_type` 字段
   - 生成不含 base64 的文本结果（含 `_image_included: true`）
   - 将图片作为单独的 user message 添加，使用多模态格式

2. **`master/scheduler.py` 的 context 保存**：
   - 存入 DB 时不存 base64，只存 `_image_included: true`
   - 避免 context 膨胀

3. **多模态格式**：
   - **OpenAI**: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}`
   - **Anthropic**: `{"type": "image", "source": {"type": "base64", "media_type": "...", "data": "..."}}`

### 验证方法

发送截图请求后检查：
```bash
# 检查 MCP 返回
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT tool_name, substr(result, 1, 100) FROM mcp_executions WHERE tool_name='screenshot' ORDER BY created_at DESC LIMIT 1;"

# 检查 context 是否存了 base64（不应该有很长的字符串）
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT length(context) FROM agent_runtimes ORDER BY created_at DESC LIMIT 1;"
```

---

## Aggregate MCP 参数格式问题 (2026-02-01)

### 问题：`runtime_rest` 调用失败

```
"error": "2 validation errors for call[runtime_rest]
  reason: Missing required argument
  args: Unexpected keyword argument"
```

### 根因分析

1. **LLMCaller 从 aggregate MCP 加载工具 schema**
2. **旧设计**: aggregate MCP 用 `proxy_handler(args: Dict = {})` 包装所有工具
   - LLM 看到的 schema: `{"properties": {"args": {...}}}`
   - LLM 发送: `{"args": {"reason": "...", ...}}`
3. **Executor 绕过 aggregate，直接调底层 MCP**
   - 底层 MCP 期望: `{"reason": "...", ...}`
   - 参数不匹配 → 失败

### 修复方案

1. **统一走 aggregate MCP** (`executor_handler.py`)
   - 修改 `_get_mcp_url_for_tool()` 返回 None
   - 让所有工具都用 `task_mcp_url`（aggregate MCP）

2. **去掉 args 包装** (`mcp_gateway/gateway.py`)
   - 修改 `_register_proxy_tool()`
   - 动态生成与原始工具**相同签名**的 proxy 函数
   - LLM 看到原始 schema，直接发送参数

### 修复后的效果

```python
# 修复前（args 包装）
LLM 发送: {"args": {"message": "hello"}}
Schema: {"properties": {"args": {...}}}

# 修复后（原始格式）
LLM 发送: {"message": "hello"}
Schema: {"properties": {"message": {...}}}
```

### 验证方法

```bash
# 检查参数格式
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT action, substr(args, 1, 200) FROM action_tasks WHERE type='tool_call' ORDER BY created_at DESC LIMIT 5;"

# 期望看到 tool_args 直接包含参数，没有 args 包装：
# {"tool_args": {"message": "..."}, ...}  ✅
# {"tool_args": {"args": {"message": "..."}}, ...}  ❌
```
