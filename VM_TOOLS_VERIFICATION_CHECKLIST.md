# VM 工具修复验证清单

## 前置条件

- [ ] vmcontrol 服务正在运行（http://127.0.0.1:19997）
- [ ] Gateway 服务正在运行（http://127.0.0.1:19999）
- [ ] Tools Server 服务正在运行（http://127.0.0.1:19998）
- [ ] 至少有一个配置好的 Agent（如 agent-001）

## 基础验证

### 1. 检查代码修改

- [ ] `executor.py` - BUILTIN_TOOL_NAMES 包含 28 个 VM 工具
- [ ] `executor.py` - _execute_builtin() 包含 VM 工具处理逻辑
- [ ] `tools.py` - get_all_tools() 动态加载 VM 工具
- [ ] `tools.py` - get_tool_by_name() 支持查找 VM 工具
- [ ] 没有 linter 错误

### 2. 启动服务测试

```bash
# Terminal 1 - Gateway
cd /Users/wangchaoqun/novaic/novaic-backend
python main_gateway.py

# Terminal 2 - Tools Server
cd /Users/wangchaoqun/novaic/novaic-backend
python -m tools_server.main
```

**检查点**：
- [ ] Gateway 启动成功，监听 19999 端口
- [ ] Tools Server 启动成功，监听 19998 端口
- [ ] 日志中没有错误

## 功能验证

### 3. 工具列表测试

```bash
# 创建 Runtime（如果还没有）
RUNTIME_RESPONSE=$(curl -s -X POST http://localhost:19999/internal/runtimes/main \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent-001", "initial_context": []}')

RUNTIME_ID=$(echo $RUNTIME_RESPONSE | jq -r '.runtime.runtime_id')
echo "Runtime ID: $RUNTIME_ID"

# 获取工具列表
curl -s http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools | jq '.'
```

**检查点**：
- [ ] 响应成功（HTTP 200）
- [ ] `total` 字段 >= 63（35个标准工具 + 28个VM工具）
- [ ] 工具列表包含 `browser_navigate`
- [ ] 工具列表包含 `mouse`
- [ ] 工具列表包含 `file_read`

**预期输出示例**：
```json
{
  "runtime_id": "rt-xxx",
  "tools": [
    {
      "name": "browser_navigate",
      "description": "Navigate browser to a URL",
      "input_schema": {...},
      "source": "builtin"
    },
    ...
  ],
  "total": 63,
  "builtin_count": 63,
  "external_count": 0
}
```

### 4. 浏览器工具测试

```bash
# 测试 browser_navigate
curl -s -X POST http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "browser_navigate",
    "arguments": {"url": "https://www.google.com"}
  }' | jq '.'
```

**检查点**：
- [ ] 响应成功（HTTP 200）
- [ ] `success: true`
- [ ] `result.success: true`
- [ ] 没有 "requires MCP client" 错误

**预期输出**：
```json
{
  "success": true,
  "result": {
    "success": true,
    "result": {...}
  },
  "error": null
}
```

### 5. 鼠标工具测试（aim + click 流程）

```bash
# Step 1: aim（获取 aim_id）
AIM_RESPONSE=$(curl -s -X POST http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mouse",
    "arguments": {
      "action": "aim",
      "x": 500,
      "y": 300
    }
  }')

echo "Aim Response:"
echo $AIM_RESPONSE | jq '.'

AIM_ID=$(echo $AIM_RESPONSE | jq -r '.result.aim_id')
echo "Aim ID: $AIM_ID"

# Step 2: click（使用 aim_id）
curl -s -X POST http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools/call \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"mouse\",
    \"arguments\": {
      \"action\": \"click\",
      \"aim_id\": \"$AIM_ID\"
    }
  }" | jq '.'
```

**检查点**：
- [ ] aim 响应包含 `aim_id`
- [ ] click 使用 `aim_id` 成功
- [ ] 两次调用都返回 `success: true`

### 6. 文件工具测试

```bash
# 测试 file_write
curl -s -X POST http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "file_write",
    "arguments": {
      "path": "/tmp/test_vm_tools.txt",
      "content": "Hello from VM tools!"
    }
  }' | jq '.'

# 测试 file_read
curl -s -X POST http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "file_read",
    "arguments": {
      "path": "/tmp/test_vm_tools.txt"
    }
  }' | jq '.'
```

**检查点**：
- [ ] file_write 成功
- [ ] file_read 返回正确内容 "Hello from VM tools!"

### 7. Shell 工具测试

```bash
# 测试 shell_exec
curl -s -X POST http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "shell_exec",
    "arguments": {
      "command": "echo Hello && uname -a"
    }
  }' | jq '.'
```

**检查点**：
- [ ] shell_exec 成功执行
- [ ] `result.exit_code: 0`
- [ ] `result.stdout` 包含输出

## 错误处理验证

### 8. vmcontrol 服务不可用

```bash
# 停止 vmcontrol 服务
# 然后测试工具调用

curl -s -X POST http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "browser_navigate",
    "arguments": {"url": "https://www.google.com"}
  }' | jq '.'
```

**检查点**：
- [ ] 返回友好的错误信息
- [ ] 不会导致 Tools Server 崩溃

### 9. 无效参数测试

```bash
# 缺少必需参数
curl -s -X POST http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "browser_navigate",
    "arguments": {}
  }' | jq '.'
```

**检查点**：
- [ ] 返回参数验证错误
- [ ] `success: false`
- [ ] 错误信息清晰

## 性能验证

### 10. 并发调用测试

```bash
# 并发调用 10 次
for i in {1..10}; do
  curl -s -X POST http://localhost:19998/internal/runtimes/$RUNTIME_ID/tools/call \
    -H "Content-Type: application/json" \
    -d '{
      "name": "shell_exec",
      "arguments": {"command": "echo Test $i"}
    }' &
done
wait
```

**检查点**：
- [ ] 所有请求都成功返回
- [ ] 没有超时或崩溃
- [ ] 响应时间合理（< 5秒）

## 日志验证

### 11. 检查日志输出

**Gateway 日志**：
- [ ] 没有 VM 工具相关错误
- [ ] VM 工具 API 调用日志正常

**Tools Server 日志**：
- [ ] 工具发现日志正常
- [ ] VM 工具调用日志正常
- [ ] 没有 "requires MCP client" 错误

## 总结

### 成功标准

✅ **所有测试通过**：
- 工具列表包含 63+ 个工具（含 28 个 VM 工具）
- browser_navigate 工具调用成功
- mouse aim + click 流程正常
- file_read/write 工具正常
- shell_exec 工具正常
- 错误处理友好
- 日志没有错误

### 失败排查

如果测试失败，检查：

1. **工具列表不包含 VM 工具**
   - 检查 `get_all_tools()` 是否正确调用 vmuse_adapter
   - 检查 vmuse_adapter.list_tools_mcp_format() 返回值

2. **工具调用失败（"requires MCP client"）**
   - 检查 `BUILTIN_TOOL_NAMES` 是否包含 VM 工具名称
   - 检查 `_execute_builtin()` 是否处理 VM 工具

3. **vmcontrol 连接失败**
   - 检查 vmcontrol 服务是否运行
   - 检查 `ServiceConfig.VMCONTROL_URL` 配置
   - 检查网络连接

4. **其他错误**
   - 查看完整错误日志
   - 检查 Python 导入路径
   - 检查服务端口冲突

## 回滚方案

如果修复导致问题：

```bash
cd /Users/wangchaoqun/novaic
git checkout novaic-backend/tools_server/executor.py
git checkout novaic-backend/tools_server/tools.py
```

然后重启服务。

## 报告问题

如果验证失败，请提供：

1. 失败的测试步骤编号
2. 完整的错误响应
3. Gateway 和 Tools Server 的日志
4. 服务版本和配置信息

---

最后更新：2026-02-06
