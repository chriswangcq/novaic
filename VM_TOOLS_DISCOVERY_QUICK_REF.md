# VM 工具发现 - 快速参考

## 🎯 核心原则

```
Gateway（被调用）← Tools Server（主动查询）
VM 工具 → 不通过 MCP → 使用 vmuse_adapter
```

## 📋 修改的文件

| 文件 | 作用 | 关键方法/端点 |
|------|------|--------------|
| `gateway/api/internal.py` | 提供 VM 工具查询 API | `GET /internal/runtimes/{runtime_id}/vm-tools` |
| `gateway/clients/vmuse_adapter.py` | 返回 MCP 格式工具列表 | `list_tools_mcp_format()` |
| `tools_server/runtime_manager.py` | 集成 VM 工具发现 | `_discover_tools()` |

## 🔧 API 端点

### Gateway: VM 工具查询

```http
GET /internal/runtimes/{runtime_id}/vm-tools
```

**响应**:
```json
{
  "tools": [
    {
      "name": "browser_navigate",
      "description": "Navigate browser to a URL",
      "inputSchema": {
        "type": "object",
        "properties": {
          "url": {"type": "string", "description": "URL to navigate to"}
        },
        "required": ["url"]
      }
    }
  ],
  "agent_id": "agent-xxx",
  "vm_available": true
}
```

## 🛠 VM 工具列表

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `browser_navigate` | 浏览器导航 | `url` |
| `browser_click` | 点击元素 | `selector` |
| `browser_type` | 输入文本 | `selector`, `text` |
| `browser_screenshot` | 页面截图 | - |
| `browser_content` | 获取页面内容 | - |
| `file_read` | 读取文件 | `path` |
| `file_write` | 写入文件 | `path`, `content` |
| `shell_exec` | 执行命令 | `command` |

## 🚀 快速测试

### 1. 验证语法

```bash
cd novaic-backend
python -m py_compile gateway/api/internal.py
python -m py_compile gateway/clients/vmuse_adapter.py
python -m py_compile tools_server/runtime_manager.py
```

### 2. 运行自动化测试

```bash
python test_vm_tools_discovery.py
```

### 3. 测试 vmuse_adapter

```python
from gateway.clients.vmuse_adapter import VmuseAdapter

adapter = VmuseAdapter()
tools = adapter.list_tools_mcp_format()
print(f"发现 {len(tools)} 个工具")
```

### 4. 测试 Gateway API

```bash
# 启动 Gateway
python novaic-backend/main_gateway.py

# 测试 API（需要真实 runtime_id）
curl http://127.0.0.1:19999/internal/runtimes/rt-xxx/vm-tools
```

## 📊 工作流程

```
Runtime 创建
    ↓
Tools Server._discover_tools()
    ↓
├─ 发现 MCP 工具（端口扫描）
│
└─ 从 Gateway 获取 VM 工具
    ├─ HTTP GET /internal/runtimes/{id}/vm-tools
    ├─ Gateway → vmuse_adapter.list_tools_mcp_format()
    ├─ 添加 _source="vm" 标记
    └─ 合并到工具列表
```

## 🔍 关键代码片段

### vmuse_adapter: 返回 MCP 格式

```python
def list_tools_mcp_format(self) -> list[Dict[str, Any]]:
    return [
        {
            "name": "browser_navigate",
            "description": "Navigate browser to a URL",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL"}
                },
                "required": ["url"]
            }
        },
        # ... 更多工具
    ]
```

### Gateway: 查询 VM 工具

```python
@router.get("/runtimes/{runtime_id}/vm-tools")
def get_runtime_vm_tools(runtime_id: str):
    # 1. 检查 Runtime
    # 2. 获取 Agent 配置
    # 3. 检查 VM 配置
    # 4. 调用 vmuse_adapter
    adapter = get_vmuse_adapter()
    tools = adapter.list_tools_mcp_format()
    return {"tools": tools, "vm_available": True}
```

### Tools Server: 发现 VM 工具

```python
# 从 Gateway 获取 VM 工具
async with httpx.AsyncClient() as client:
    response = await client.get(
        f"{gateway_url}/internal/runtimes/{runtime_id}/vm-tools"
    )
    vm_tools = response.json().get("tools", [])
    
    # 添加标记
    for tool in vm_tools:
        tool["_source"] = "vm"
        tool["_server"] = f"{runtime_id}_vm"
    
    runtime_tools.extend(vm_tools)
```

## ✅ 验证清单

- [x] Python 语法正确
- [x] vmuse_adapter 返回 8 个工具
- [x] Gateway API 端点定义
- [x] Tools Server 集成逻辑
- [x] 错误处理完善
- [x] 日志记录完整
- [ ] 端到端测试（需运行服务）

## 🐛 故障排查

### 问题: Gateway API 返回 404

**原因**: Runtime 不存在

**解决**: 创建一个有效的 Runtime

### 问题: vm_available = false

**原因**: Agent 没有 VM 配置

**解决**: 确保 Agent 配置中有 VM 部分

### 问题: Tools Server 没有发现 VM 工具

**原因**: 
1. Gateway 服务未运行
2. 网络连接问题
3. Runtime 没有 VM 配置

**排查**:
```bash
# 检查 Gateway 是否运行
curl http://127.0.0.1:19999/health

# 检查 API 是否可访问
curl http://127.0.0.1:19999/internal/runtimes/rt-xxx/vm-tools

# 查看 Tools Server 日志
grep "VM tools" logs/tools_server.log
```

## 📝 日志示例

### 成功发现 VM 工具

```
[RuntimeManager] Registered server mcp on port 5555 for runtime rt-xxx
[RuntimeManager] Discovered 10 tools for runtime: rt-xxx
[RuntimeManager] Discovered 8 VM tools from Gateway for runtime: rt-xxx
```

### VM 工具不可用

```
[RuntimeManager] Failed to fetch VM tools: status=404
[RuntimeManager] Discovered 10 tools for runtime: rt-xxx
```

## 🎉 完成标志

当你看到以下日志，说明集成成功：

```
[RuntimeManager] Discovered 8 VM tools from Gateway for runtime: rt-xxx
```

并且工具列表中包含 `_source: "vm"` 的工具。

## 📚 相关文档

- 详细实现报告: `VM_TOOLS_DISCOVERY_IMPLEMENTATION.md`
- 测试脚本: `test_vm_tools_discovery.py`
- vmuse_adapter 文档: `VMUSE_ADAPTER_README.md`
