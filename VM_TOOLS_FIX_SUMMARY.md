# VM 工具调用问题修复总结

## 问题描述

用户反馈 Tool Server 的 VM 工具调用失败，错误信息：
```json
{
  "error": "External tool 'browser_navigate' requires MCP client, but none is configured",
  "success": false
}
```

## 问题根源

### 1. 工具路由问题
在 `executor.py` 中，VM 工具（如 `browser_navigate`）**不在** `BUILTIN_TOOL_NAMES` 集合中，导致：
- 工具调用被路由到 `_execute_external()` 方法
- 该方法检查 `external_mcp_client` 是否存在
- 但是 `ToolExecutor` 创建时没有传入 `external_mcp_client`（api.py:315）
- 导致返回错误

### 2. 架构设计问题
原设计中：
- VM 工具应该通过 vmuse_adapter 调用（已实现）
- 但 ToolExecutor 没有集成 vmuse_adapter
- 导致 VM 工具无法被正确执行

## 解决方案

### 修改 1: executor.py - 添加 VM 工具为内置工具

**文件**：`novaic-backend/tools_server/executor.py`

**修改内容**：
1. 将 28 个 VM 工具名称添加到 `BUILTIN_TOOL_NAMES` 集合：
```python
# VM 工具（通过 vmuse_adapter 实现）
"browser_navigate",
"browser_click",
"browser_type",
"browser_screenshot",
"browser_content",
"browser_scroll",
"browser_eval",
"browser_get_tabs",
"browser_switch_tab",
"browser_close_tab",
"file_read",
"file_write",
"shell_exec",
"screenshot",
"mouse",
"keyboard",
"list_windows",
"focus_window",
"maximize_window",
"minimize_window",
"close_window",
"resize_window",
"launch_app",
"system_snapshot",
"clipboard_get",
"clipboard_set",
"environment_info",
```

2. 在 `_execute_builtin()` 方法中添加 VM 工具处理逻辑：
```python
# ==================== VM 工具（通过 vmuse_adapter）====================
elif tool_name in [
    "browser_navigate", "browser_click", "browser_type", 
    "browser_screenshot", "browser_content", "browser_scroll",
    "browser_eval", "browser_get_tabs", "browser_switch_tab", "browser_close_tab",
    "file_read", "file_write", "shell_exec", "screenshot",
    "mouse", "keyboard",
    "list_windows", "focus_window", "maximize_window", "minimize_window",
    "close_window", "resize_window", "launch_app",
    "system_snapshot", "clipboard_get", "clipboard_set", "environment_info",
]:
    # 使用 vmuse_adapter 调用 VM 工具
    from gateway.clients.vmuse_adapter import get_vmuse_adapter
    
    adapter = get_vmuse_adapter()
    
    # 从 agent_id 提取 VM ID（假设 agent_id 格式为 "agent-NNN"）
    # 或者使用固定的 VM ID "1"
    vm_id = self.agent_id.replace("agent-", "") if self.agent_id.startswith("agent-") else "1"
    
    result = await adapter.call_tool(
        tool_name=tool_name,
        arguments=arguments,
        vm_id=vm_id
    )
    
    return result
```

### 修改 2: tools.py - 动态加载 VM 工具

**文件**：`novaic-backend/tools_server/tools.py`

**修改内容**：

1. 修改 `get_all_tools()` 函数，动态从 vmuse_adapter 获取 VM 工具：
```python
def get_all_tools() -> List[Dict[str, Any]]:
    """
    Get all tools as a flat list (for LLM function calling).
    
    Includes both standard builtin tools and VM tools from vmuse_adapter.
    
    Returns:
        List of tool definitions in OpenAI function calling format.
        Each tool has: name, description, inputSchema
    """
    tools = []
    
    # 添加标准内置工具
    for category_tools in BUILTIN_TOOLS.values():
        tools.extend(category_tools)
    
    # 添加 VM 工具（从 vmuse_adapter）
    try:
        from gateway.clients.vmuse_adapter import get_vmuse_adapter
        adapter = get_vmuse_adapter()
        vm_tools = adapter.list_tools_mcp_format()
        tools.extend(vm_tools)
    except Exception as e:
        # 如果 vmuse_adapter 不可用，仅记录警告，不影响其他工具
        import logging
        logging.getLogger(__name__).warning(f"Failed to load VM tools: {e}")
    
    return tools
```

2. 修改 `get_tool_by_name()` 函数，支持查找 VM 工具：
```python
def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a tool definition by name.
    
    Supports both standard builtin tools and VM tools from vmuse_adapter.
    
    Args:
        name: Tool name (e.g., 'memory_save', 'chat_reply', 'browser_navigate')
        
    Returns:
        Tool definition dict or None if not found
    """
    # 首先检查标准内置工具
    tool = _TOOL_BY_NAME.get(name)
    if tool:
        return tool
    
    # 如果不是标准工具，检查是否是 VM 工具
    try:
        from gateway.clients.vmuse_adapter import get_vmuse_adapter
        adapter = get_vmuse_adapter()
        vm_tools = adapter.list_tools_mcp_format()
        
        # 在 VM 工具列表中查找
        for vm_tool in vm_tools:
            if vm_tool.get("name") == name:
                return vm_tool
    except Exception:
        pass  # 忽略错误，返回 None
    
    return None
```

## 工具列表

修复后，系统支持以下 28 个 VM 工具：

### 浏览器工具 (10)
- `browser_navigate` - 导航到 URL
- `browser_click` - 点击元素
- `browser_type` - 输入文本
- `browser_screenshot` - 截图
- `browser_content` - 获取页面内容
- `browser_scroll` - 滚动页面
- `browser_eval` - 执行 JavaScript
- `browser_get_tabs` - 获取标签页列表
- `browser_switch_tab` - 切换标签页
- `browser_close_tab` - 关闭标签页

### 文件工具 (2)
- `file_read` - 读取文件
- `file_write` - 写入文件

### Shell 工具 (1)
- `shell_exec` - 执行 Shell 命令

### 输入工具 (3)
- `screenshot` - VM 截图
- `mouse` - 鼠标控制（需要先 aim，再执行其他操作）
- `keyboard` - 键盘控制

### 窗口管理工具 (7)
- `list_windows` - 列出窗口
- `focus_window` - 聚焦窗口
- `maximize_window` - 最大化窗口
- `minimize_window` - 最小化窗口
- `close_window` - 关闭窗口
- `resize_window` - 调整窗口大小
- `launch_app` - 启动应用

### 上下文工具 (4)
- `system_snapshot` - 系统快照
- `clipboard_get` - 获取剪贴板
- `clipboard_set` - 设置剪贴板
- `environment_info` - 环境信息

## 验证步骤

### 1. 启动服务
```bash
cd /Users/wangchaoqun/novaic/novaic-backend

# 启动 Gateway
python main_gateway.py

# 启动 Tools Server
python -m tools_server.main
```

### 2. 测试工具列表 API
```bash
# 创建 Runtime（需要先有 Agent）
curl -X POST http://localhost:19999/internal/runtimes/main \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent-001", "initial_context": []}'

# 获取 runtime_id，然后查询工具列表
curl http://localhost:19998/internal/runtimes/{runtime_id}/tools | jq '.tools[] | select(.name | startswith("browser_"))'
```

### 3. 测试工具调用
```bash
# 调用 browser_navigate
curl -X POST http://localhost:19998/internal/runtimes/{runtime_id}/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "browser_navigate",
    "arguments": {"url": "https://www.google.com"}
  }'
```

预期结果：
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

## 技术细节

### 工具执行流程

1. **工具调用请求** → Tools Server API (`/runtimes/{runtime_id}/tools/call`)
2. **创建 ToolExecutor** → 传入 `runtime` 和 `manager`
3. **执行工具** → `executor.execute(tool_name, arguments)`
4. **路由判断**：
   - 检查 `tool_name` 是否在 `BUILTIN_TOOL_NAMES` 中
   - 是 → 调用 `_execute_builtin()`
   - 否 → 调用 `_execute_external()`（需要 MCP 客户端）
5. **VM 工具处理** → 在 `_execute_builtin()` 中：
   - 导入 vmuse_adapter
   - 调用 `adapter.call_tool(tool_name, arguments, vm_id)`
   - 返回结果

### 关键设计决策

**为什么将 VM 工具改为内置工具？**

1. **简化架构**：避免引入额外的 MCP 客户端层
2. **直接调用**：vmuse_adapter 已经提供了完整的工具实现
3. **避免重复**：不需要在 MCP 和 vmuse_adapter 之间转换
4. **性能优化**：减少一层网络调用

**为什么在 tools.py 中动态加载 VM 工具？**

1. **单一数据源**：VM 工具定义集中在 vmuse_adapter.list_tools_mcp_format()
2. **避免重复**：不需要在多个地方维护工具定义
3. **自动同步**：vmuse_adapter 更新后，工具列表自动更新

## 相关文件

- `novaic-backend/tools_server/executor.py` - 工具执行器
- `novaic-backend/tools_server/tools.py` - 工具定义
- `novaic-backend/tools_server/api.py` - Tools Server API
- `novaic-backend/gateway/clients/vmuse_adapter.py` - VMUSE 适配器
- `novaic-backend/gateway/api/internal.py` - Gateway Internal API

## 已知限制

1. **VM ID 推导**：当前从 `agent_id` 推导 `vm_id`（格式：`agent-NNN` → `NNN`）。如果格式不匹配，使用默认值 "1"。
2. **vmuse_adapter 初始化**：需要确保 vmcontrol 服务正在运行（默认 `http://127.0.0.1:19997`）。
3. **工具发现缓存**：`get_all_tools()` 每次都会调用 vmuse_adapter，没有缓存机制。如果性能成为问题，可以考虑添加缓存。

## 后续优化建议

1. **添加缓存**：在 `get_all_tools()` 中缓存 VM 工具列表，定期刷新
2. **VM ID 映射**：使用数据库存储 agent_id → vm_id 的映射关系
3. **健康检查**：在 Tools Server 启动时检查 vmuse_adapter 是否可用
4. **监控指标**：添加 VM 工具调用的成功率、延迟等监控指标

## 测试清单

- [ ] 工具列表 API 返回 VM 工具
- [ ] `browser_navigate` 工具调用成功
- [ ] `mouse` 工具 aim + click 流程正常
- [ ] `file_read` / `file_write` 工具正常
- [ ] `shell_exec` 工具执行命令正常
- [ ] 错误处理：vmcontrol 服务不可用时返回友好错误
- [ ] 性能测试：大量并发调用不会阻塞

## 修改时间

2026-02-06
