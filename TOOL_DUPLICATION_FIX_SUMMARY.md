# 工具重复问题修复总结

## 问题
```
"error": "API error: 400 - Invalid request: function name browser_navigate is duplicated"
```

## 根本原因
VM 工具（`browser_navigate` 等）被添加了**两次**：

### 第一次：作为 builtin（正确）
```python
# novaic-backend/tools_server/tools.py:756
def get_all_tools():
    # ... 添加标准工具 ...
    
    # 添加 VM 工具
    adapter = get_vmuse_adapter()
    vm_tools = adapter.list_tools_mcp_format()
    tools.extend(vm_tools)  # ← VM 工具在这里添加
```

### 第二次：作为 external（错误）
```python
# novaic-backend/tools_server/runtime_manager.py:226-255
async def _discover_tools(self, runtime_id: str):
    # ... MCP 工具发现 ...
    
    # 从 Gateway 获取 VM 工具
    response = await client.get(f"{gateway_url}/internal/runtimes/{runtime_id}/vm-tools")
    vm_tools = vm_data.get("tools", [])
    runtime_tools.extend(vm_tools)  # ← VM 工具在这里又添加了一次！
```

### 合并导致重复
```python
# novaic-backend/tools_server/api.py:245
async def get_tools(runtime_id: str):
    builtin_tools = get_all_tools()      # ← 包含 VM 工具
    external_tools = manager.get_external_tools(runtime_id)  # ← 又包含 VM 工具
    
    tools = builtin_tools + external_tools  # ← 导致重复！
```

## 修复方案

### 删除重复的获取逻辑

**文件**：`novaic-backend/tools_server/runtime_manager.py`

**删除**：第 226-255 行（从 Gateway 获取 VM 工具的代码）

**原因**：
- VM 工具已经在 `tools.py` 中作为 builtin 添加
- VM 工具不是外部 MCP 服务器工具
- 不需要为每个 runtime 单独发现 VM 工具

## 正确的架构

```
builtin_tools (应该包含)          external_tools (应该包含)
├── memory_*                      └── (用户自定义的 MCP 服务器工具)
├── runtime_*
├── chat_*
├── web_*
├── qemu_*
├── task_*
└── VM tools ← 只在这里！
    ├── browser_*
    ├── context_*
    ├── desktop_*
    ├── file_*
    ├── shell_*
    └── window_*
```

## 设计原则

1. **VM 工具是 builtin**
   - 通过 `vmuse_adapter` 直接调用
   - 不通过 MCP 协议
   - 所有 runtime 共享相同的工具集

2. **external_tools 只包含真正的外部 MCP 服务器**
   - 用户自定义的 MCP 服务器
   - 第三方 MCP 服务
   - 通过端口发现的外部工具

3. **单一数据源原则**
   - VM 工具只在一个地方定义和获取
   - 避免重复的获取路径

## 验证方法

```bash
# 1. 查看工具列表
curl http://localhost:8001/internal/runtimes/{runtime_id}/tools

# 2. 检查每个工具是否只出现一次
# 预期：
# - browser_navigate (source: builtin) ✓
# - 没有重复的 browser_navigate ✓

# 3. 检查所有 VM 工具
# 预期工具列表：
# - browser_navigate, browser_click, browser_type, ...
# - context_capture, context_explain
# - desktop_screenshot, desktop_move_cursor, ...
# - file_read, file_write, file_list, ...
# - shell_execute, shell_execute_stream
# - window_focus, window_list, window_info, ...
```

## 修改记录

### 修改文件
- `novaic-backend/tools_server/runtime_manager.py` - 删除从 Gateway 获取 VM 工具的逻辑

### 保持不变
- `novaic-backend/tools_server/tools.py` - VM 工具作为 builtin 保留
- `novaic-backend/tools_server/api.py` - 工具合并逻辑保持不变
- `novaic-backend/gateway/api/internal.py` - Gateway API 保留（可能有其他用途）

## 后续建议

### 1. 添加去重机制（防御性编程）

```python
# tools_server/api.py
async def get_tools(runtime_id: str):
    builtin_tools = get_all_tools()
    external_tools = manager.get_external_tools(runtime_id)
    
    # 合并并去重（基于工具名称）
    tools_dict = {}
    for tool in builtin_tools:
        tools_dict[tool["name"]] = {"source": "builtin", **tool}
    for tool in external_tools:
        if tool["name"] not in tools_dict:  # 避免覆盖 builtin
            tools_dict[tool["name"]] = {"source": "external", **tool}
    
    return list(tools_dict.values())
```

### 2. 添加架构文档

在 `novaic-backend/tools_server/README.md` 中说明：
- builtin vs external 的定义
- VM 工具的归属和获取方式
- 工具注册流程图

### 3. 添加单元测试

```python
def test_vm_tools_no_duplication():
    """确保 VM 工具不重复"""
    tools = get_all_tools()
    tool_names = [t["name"] for t in tools]
    assert len(tool_names) == len(set(tool_names)), "工具名称重复！"
```

## 相关文档

- [详细根因分析](./TOOL_DUPLICATION_ROOT_CAUSE_ANALYSIS.md)
- [VM 工具适配器文档](./VMUSE_ADAPTER_README.md)
- [Tools Server 架构](./novaic-backend/tools_server/)
