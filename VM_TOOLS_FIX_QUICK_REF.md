# VM 工具调用问题修复 - 快速参考

## 问题

```
"error": "External tool 'browser_navigate' requires MCP client, but none is configured"
```

## 根本原因

- VM 工具（28个）没有被识别为内置工具
- ToolExecutor 创建时没有传入 MCP 客户端
- 导致 VM 工具调用失败

## 解决方案

### 1. 修改 executor.py（28个 VM 工具 → 内置工具）

**添加到 BUILTIN_TOOL_NAMES**：
```python
# VM 工具（通过 vmuse_adapter 实现）
"browser_navigate", "browser_click", "browser_type",
"browser_screenshot", "browser_content", "browser_scroll",
"browser_eval", "browser_get_tabs", "browser_switch_tab", "browser_close_tab",
"file_read", "file_write", "shell_exec", "screenshot",
"mouse", "keyboard",
"list_windows", "focus_window", "maximize_window", "minimize_window",
"close_window", "resize_window", "launch_app",
"system_snapshot", "clipboard_get", "clipboard_set", "environment_info",
```

**在 _execute_builtin() 中添加处理逻辑**：
```python
elif tool_name in ["browser_navigate", ...]:
    from gateway.clients.vmuse_adapter import get_vmuse_adapter
    adapter = get_vmuse_adapter()
    vm_id = self.agent_id.replace("agent-", "") if self.agent_id.startswith("agent-") else "1"
    result = await adapter.call_tool(tool_name, arguments, vm_id)
    return result
```

### 2. 修改 tools.py（动态加载 VM 工具）

**get_all_tools()**：
```python
# 添加 VM 工具
from gateway.clients.vmuse_adapter import get_vmuse_adapter
adapter = get_vmuse_adapter()
vm_tools = adapter.list_tools_mcp_format()
tools.extend(vm_tools)
```

**get_tool_by_name()**：
```python
# 查找 VM 工具
from gateway.clients.vmuse_adapter import get_vmuse_adapter
adapter = get_vmuse_adapter()
vm_tools = adapter.list_tools_mcp_format()
for vm_tool in vm_tools:
    if vm_tool.get("name") == name:
        return vm_tool
```

## 支持的 VM 工具（28个）

| 类别 | 工具数量 | 工具列表 |
|------|---------|---------|
| 浏览器 | 10 | navigate, click, type, screenshot, content, scroll, eval, get_tabs, switch_tab, close_tab |
| 文件 | 2 | read, write |
| Shell | 1 | exec |
| 输入 | 3 | screenshot, mouse, keyboard |
| 窗口 | 7 | list, focus, maximize, minimize, close, resize, launch_app |
| 上下文 | 4 | system_snapshot, clipboard_get, clipboard_set, environment_info |

## 测试

```bash
# 1. 启动服务
cd novaic-backend
python main_gateway.py  # Terminal 1
python -m tools_server.main  # Terminal 2

# 2. 创建 Runtime
curl -X POST http://localhost:19999/internal/runtimes/main \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent-001", "initial_context": []}'

# 3. 测试工具调用
curl -X POST http://localhost:19998/internal/runtimes/{runtime_id}/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "browser_navigate", "arguments": {"url": "https://www.google.com"}}'
```

## 预期结果

✅ **成功**：
```json
{
  "success": true,
  "result": {
    "success": true,
    "result": {...}
  }
}
```

❌ **失败**（修复前）：
```json
{
  "success": false,
  "error": "External tool 'browser_navigate' requires MCP client, but none is configured"
}
```

## 关键变化

| 修改前 | 修改后 |
|--------|--------|
| VM 工具 → 外部工具（需要 MCP 客户端） | VM 工具 → 内置工具（通过 vmuse_adapter） |
| 工具调用失败 | 工具调用成功 ✅ |
| 需要配置 MCP 客户端 | 不需要 MCP 客户端 |

## 文件修改

- ✅ `novaic-backend/tools_server/executor.py` - 添加 VM 工具到内置工具集合，添加处理逻辑
- ✅ `novaic-backend/tools_server/tools.py` - 动态加载 VM 工具定义

## 架构图

```
┌─────────────┐
│  LLM        │
│  (调用工具)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Tools Server                       │
│  ┌───────────────────────────────┐ │
│  │ ToolExecutor                  │ │
│  │  ├─ _execute_builtin()        │ │
│  │  │   ├─ Memory 工具 → Gateway │ │
│  │  │   ├─ Chat 工具 → Gateway   │ │
│  │  │   └─ VM 工具 → vmuse_adapter│ │
│  │  └─ _execute_external()       │ │
│  │       └─ (MCP 客户端，可选)    │ │
│  └───────────────────────────────┘ │
└─────────────┬───────────────────────┘
              │
              ▼
       ┌──────────────┐
       │ vmuse_adapter│
       │ (28个 VM工具) │
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │ vmcontrol    │
       │ (VM 控制服务)│
       └──────────────┘
```

## 详细文档

参见：`VM_TOOLS_FIX_SUMMARY.md`
