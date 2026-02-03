# MCP 调试指南

## MCP 架构概览

```
┌──────────────────────────────────────────────────────────────────────┐
│                      MCP Gateway (19998)                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Agent Shared MCP                             │  │
│  │  (per-agent, 所有 Runtime 共享)                                  │  │
│  │                                                                 │  │
│  │  • local       - 文件系统操作 (read, write, list)                │  │
│  │  • memory      - 记忆存储 (store, retrieve, search)              │  │
│  │  • vmuse       - VM 工具 (browser, desktop, shell, windows)      │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                     Runtime MCP                                  │  │
│  │  (per-runtime)                                                   │  │
│  │                                                                 │  │
│  │  • subagent_spawn   - 启动子 Agent                              │  │
│  │  • subagent_query   - 查询子 Agent 状态                          │  │
│  │  • subagent_cancel  - 取消子 Agent                              │  │
│  │  • context_request  - 请求更多上下文                             │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                   Aggregate Gateway                              │  │
│  │  /aggregate/{agent_id}/{runtime_id}                              │  │
│  │                                                                 │  │
│  │  合并 Agent Shared + Runtime MCP 的所有工具                       │  │
│  │  LLM 通过这个入口获取完整工具列表                                  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 调试命令

### 检查 MCP Gateway 状态

```bash
# 健康检查
curl http://127.0.0.1:19998/api/health

# 列出所有 MCP 服务
curl http://127.0.0.1:19998/mcp/servers
```

### 检查工具列表

```bash
# Agent Shared MCP 工具
curl http://127.0.0.1:19998/mcp/agent-shared/{agent_id}/tools/list

# Runtime MCP 工具
curl http://127.0.0.1:19998/mcp/runtime/{agent_id}/{runtime_id}/tools/list

# Aggregate (全部工具)
curl http://127.0.0.1:19998/aggregate/{agent_id}/{runtime_id}/tools/list
```

### 手动调用工具

```bash
# 调用 local MCP 的 read_file 工具
curl -X POST http://127.0.0.1:19998/mcp/agent-shared/{agent_id}/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "read_file",
    "arguments": {
      "path": "/path/to/file"
    }
  }'

# 调用 Runtime MCP 的 subagent_spawn
curl -X POST http://127.0.0.1:19998/mcp/runtime/{agent_id}/{runtime_id}/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "subagent_spawn",
    "arguments": {
      "task": "Do something",
      "share_context": false
    }
  }'
```

## 常见问题

### 1. 工具列表为空

**症状**: `/tools/list` 返回空数组

**排查**:

```bash
# 检查 MCP 服务是否创建
curl http://127.0.0.1:19998/mcp/servers

# 如果服务不存在，检查 Runtime
curl http://127.0.0.1:19999/internal/runtimes/{agent_id}
# 确认 mcp_url 字段不为空
```

**常见原因**:
- RuntimeLauncher 未成功创建 MCP
- MCP Gateway 重启导致服务丢失
- agent_id 或 runtime_id 错误

### 2. 工具调用超时

**症状**: 工具调用长时间无响应

**排查**:

```bash
# 检查 MCP Gateway 进程
ps aux | grep mcp_main

# 检查是否有挂起的请求
# (需要在 MCP Gateway 中添加日志)
```

**常见原因**:
- VM 操作太慢 (browser, desktop)
- 网络问题
- 资源不足

### 3. Aggregate Gateway 找不到工具

**症状**: Aggregate 返回的工具比预期少

**排查**:

```bash
# 分别检查各 MCP 的工具
curl http://127.0.0.1:19998/mcp/agent-shared/{agent_id}/tools/list
curl http://127.0.0.1:19998/mcp/runtime/{agent_id}/{runtime_id}/tools/list

# 检查 Aggregate 注册
curl http://127.0.0.1:19998/aggregate/{agent_id}/{runtime_id}/info
```

**常见原因**:
- Agent Shared MCP 未创建
- Runtime MCP 未创建
- Aggregate 注册失败

### 4. SubAgent 工具调用失败

**症状**: subagent_spawn/query/cancel 返回错误

**排查**:

```bash
# 检查 SubAgent 状态
curl http://127.0.0.1:19999/internal/subagents/{agent_id}

# 检查 Runtime MCP 配置
curl http://127.0.0.1:19998/mcp/runtime/{agent_id}/{runtime_id}/info

# 手动查询 SubAgent
curl http://127.0.0.1:19999/internal/subagents/{agent_id}/{subagent_id}/status
```

**常见原因**:
- SubAgent ID 不存在
- Runtime MCP 的 gateway_url 配置错误
- 权限问题

## MCP 服务生命周期

### 创建流程

```
1. RuntimeLauncher 创建 Runtime
2. 调用 MCP Gateway 创建 Agent Shared MCP (如果不存在)
   POST /mcp/agent-shared
3. 调用 MCP Gateway 创建 Runtime MCP
   POST /mcp/runtime
4. 调用 MCP Gateway 创建 Aggregate Gateway
   POST /mcp/aggregate
5. 等待工具发现完成 (tool discovery)
6. 保存 mcp_url 到 Runtime
```

### 销毁流程

```
1. SummarizeCollector 完成对话
2. 调用 MCP Gateway 删除 Runtime MCP
   DELETE /mcp/runtime/{agent_id}/{runtime_id}
3. 调用 MCP Gateway 删除 Aggregate Gateway
   DELETE /mcp/aggregate/{agent_id}/{runtime_id}
4. Agent Shared MCP 保留 (可复用)
```

## 日志分析

### MCP Gateway 日志

```python
# 在 mcp_main.py 中添加详细日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 关键日志点

```
[MCP Gateway] Creating Agent Shared MCP for agent xxx
[MCP Gateway] Agent Shared MCP created: http://127.0.0.1:19998/mcp/agent-shared/xxx
[MCP Gateway] Creating Runtime MCP for runtime rt-xxx
[MCP Gateway] Runtime MCP created: http://127.0.0.1:19998/mcp/runtime/xxx/rt-xxx
[MCP Gateway] Aggregate Gateway registered: /aggregate/xxx/rt-xxx
[MCP Gateway] Tool discovery completed: 15 tools found
```

## 开发调试技巧

### 1. 使用 MCP Inspector

```bash
# 安装 MCP Inspector
npm install -g @modelcontextprotocol/inspector

# 连接到 Aggregate Gateway
mcp-inspector http://127.0.0.1:19998/aggregate/{agent_id}/{runtime_id}
```

### 2. 模拟 LLM 工具调用

```python
import httpx

async def test_tool_call():
    async with httpx.AsyncClient() as client:
        # 获取工具列表
        tools = await client.get(
            f"http://127.0.0.1:19998/aggregate/{agent_id}/{runtime_id}/tools/list"
        )
        print("Tools:", tools.json())
        
        # 调用工具
        result = await client.post(
            f"http://127.0.0.1:19998/aggregate/{agent_id}/{runtime_id}/tools/call",
            json={
                "name": "read_file",
                "arguments": {"path": "/tmp/test.txt"}
            }
        )
        print("Result:", result.json())
```

### 3. 检查 MCP 内部状态

```bash
# 检查 MCPManager 状态
curl http://127.0.0.1:19998/internal/mcp-manager/stats

# 检查活跃连接
curl http://127.0.0.1:19998/internal/connections
```

## MCP 配置

### Agent Shared MCP 配置

```python
# mcp_servers/agent_shared.py
SHARED_MCP_CONFIG = {
    "local": {
        "workspace": "/path/to/workspace",
        "allowed_paths": ["/tmp", "/home"],
    },
    "memory": {
        "max_entries": 1000,
    },
    "vmuse": {
        "vm_id": "...",
    },
}
```

### Runtime MCP 配置

```python
# mcp_servers/runtime.py
RUNTIME_MCP_CONFIG = {
    "gateway_url": "http://127.0.0.1:19999",
    "agent_id": "...",
    "runtime_id": "...",
    "subagent_id": "...",
}
```

## 性能优化

### 1. 工具发现缓存

```python
# Aggregate Gateway 缓存工具列表
# 避免每次 LLM 调用都重新发现
TOOL_CACHE_TTL = 60  # seconds
```

### 2. 连接池

```python
# 复用 HTTP 连接
httpx.AsyncClient(
    limits=httpx.Limits(max_connections=100),
    timeout=httpx.Timeout(30.0),
)
```

### 3. 并行工具调用

```python
# 多个工具调用可以并行执行
async def call_tools(tools_calls):
    tasks = [call_tool(tc) for tc in tool_calls]
    return await asyncio.gather(*tasks)
```
