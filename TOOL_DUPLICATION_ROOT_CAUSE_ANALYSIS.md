# 工具重复问题根因分析报告

## 问题描述

API 返回错误：
```
"error": "API error: 400 - Invalid request: function name browser_navigate is duplicated"
```

## 调查过程

### 1. 追踪工具注册流程

#### 1.1 工具获取入口（`tools_server/api.py:245`）

```python
@internal_router.get("/runtimes/{runtime_id}/tools")
async def get_tools(runtime_id: str):
    # 获取内置工具
    builtin_tools = get_all_tools()
    
    # 获取外部工具（从 RuntimeManager 的发现结果）
    external_tools = manager.get_external_tools(runtime_id)
    
    # 合并工具列表
    tools = builtin_tools + external_tools
```

#### 1.2 内置工具获取（`tools_server/tools.py:736`）

```python
def get_all_tools() -> List[Dict[str, Any]]:
    tools = []
    
    # 添加标准内置工具
    for category_tools in BUILTIN_TOOLS.values():
        tools.extend(category_tools)
    
    # 添加 VM 工具（从 vmuse_adapter）← 第一次添加 VM 工具
    try:
        from gateway.clients.vmuse_adapter import get_vmuse_adapter
        adapter = get_vmuse_adapter()
        vm_tools = adapter.list_tools_mcp_format()
        tools.extend(vm_tools)  # ← 这里添加了 VM 工具
    except Exception as e:
        logger.warning(f"Failed to load VM tools: {e}")
    
    return tools
```

**发现 1**：VM 工具在 `get_all_tools()` 中被添加到 `builtin_tools`

#### 1.3 外部工具发现（`runtime_manager.py:186`）

```python
async def _discover_tools(self, runtime_id: str) -> None:
    # ... 注册 MCP 服务器 ...
    
    # 发现 MCP 工具
    tools = await self._registry.discover_all_tools(use_cache=False)
    runtime_tools = [
        tool for tool in tools
        if tool.get("_server", "").startswith(f"{runtime_id}_")
    ]
    
    # 从 Gateway 获取 VM 工具 ← 第二次添加 VM 工具
    try:
        response = await client.get(
            f"{gateway_url}/internal/runtimes/{runtime_id}/vm-tools",
            timeout=5.0
        )
        if response.status_code == 200:
            vm_tools = vm_data.get("tools", [])
            runtime_tools.extend(vm_tools)  # ← 这里又添加了一次！
    except Exception as e:
        logger.warning(f"Failed to fetch VM tools: {e}")
```

**发现 2**：VM 工具在 `_discover_tools()` 中通过 Gateway API 再次被添加到 `external_tools`

#### 1.4 Gateway VM 工具 API（`gateway/api/internal.py:2990`）

```python
@router.get("/runtimes/{runtime_id}/vm-tools")
def get_runtime_vm_tools(runtime_id: str):
    try:
        adapter = get_vmuse_adapter()
        tools = adapter.list_tools_mcp_format()  # ← 返回相同的 VM 工具列表
        
        return {
            "tools": tools,
            "agent_id": agent_id,
            "vm_available": True
        }
```

**发现 3**：Gateway API 返回的是相同的 `vmuse_adapter.list_tools_mcp_format()`

## 根本原因

### 重复的根源

**VM 工具被添加了两次，导致重复：**

1. **第一次（作为 builtin）**
   - 位置：`tools_server/tools.py:756`
   - 方式：直接调用 `vmuse_adapter.list_tools_mcp_format()`
   - 结果：VM 工具被添加到 `builtin_tools` 列表

2. **第二次（作为 external）**
   - 位置：`tools_server/runtime_manager.py:226-255`
   - 方式：通过 Gateway API `/internal/runtimes/{runtime_id}/vm-tools` 获取
   - 结果：相同的 VM 工具被添加到 `external_tools` 列表

3. **合并导致重复**
   - 位置：`tools_server/api.py:266-285`
   - 方式：`builtin_tools + external_tools`
   - 结果：每个 VM 工具出现两次，导致 LLM API 错误

### 架构设计问题

#### 原本的设计意图（推测）

1. `builtin_tools`：应该包含标准内置工具（memory、runtime、chat、web、qemu、task）
2. `external_tools`：应该包含外部 MCP 服务器提供的工具
3. VM 工具应该是... **这里不明确！**

#### 实际的实现问题

**问题 1**：VM 工具的归属不明确
- 是 builtin 还是 external？
- 如果是 builtin，为什么在 RuntimeManager 中还要发现？
- 如果是 external，为什么在 tools.py 中添加？

**问题 2**：重复的获取路径
- `tools.py` 直接调用 `vmuse_adapter`
- `runtime_manager.py` 通过 Gateway API 调用 `vmuse_adapter`
- 两个路径返回相同的工具列表

**问题 3**：没有去重机制
- `get_tools()` 简单合并两个列表，没有检查重复

## 正确的架构设计

### 设计原则

1. **VM 工具应该通过 vmuse_adapter 提供，不需要 MCP**
   - VM 工具不是外部 MCP 服务器
   - VM 工具是系统内置的，直接通过 Python 调用

2. **VM 工具是全局的，所有 runtime 共享**
   - 所有 runtime 看到的 VM 工具集是一样的
   - 不需要为每个 runtime 单独发现

3. **external_tools 只包含真正的外部 MCP 服务器工具**
   - 例如：用户自定义的 MCP 服务器
   - 例如：第三方 MCP 服务

### 正确的架构

```
┌─────────────────────────────────────────────────┐
│         Tools Server API (get_tools)            │
└─────────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌─────────────┐          ┌─────────────────┐
│ builtin     │          │ external        │
│ tools       │          │ tools           │
└─────────────┘          └─────────────────┘
        │                         │
        ▼                         ▼
┌─────────────┐          ┌─────────────────┐
│ BUILTIN     │          │ MCP Registry    │
│ TOOLS       │          │ Discovery       │
│ (standard)  │          │ (user servers)  │
└─────────────┘          └─────────────────┘
        │
        ▼
┌─────────────┐
│ VM Tools    │
│ (vmuse_     │
│  adapter)   │
└─────────────┘

正确：VM 工具只在 builtin 中
错误：VM 工具既在 builtin 又在 external
```

## 修复方案

### 方案：删除 RuntimeManager 中的 VM 工具获取逻辑

**修改文件**：`novaic-backend/tools_server/runtime_manager.py`

**删除代码**：第 226-255 行（从 Gateway 获取 VM 工具的部分）

**原因**：
1. VM 工具已经在 `tools.py` 中作为 builtin 添加
2. VM 工具不是外部 MCP 服务器工具
3. 所有 runtime 共享相同的 VM 工具集，不需要单独发现

**保留**：
- `tools.py` 中的 VM 工具添加逻辑（作为 builtin）
- RuntimeManager 的 MCP 服务器发现逻辑（真正的 external）

### 修复后的流程

```
get_tools(runtime_id)
    │
    ├─ builtin_tools = get_all_tools()
    │      │
    │      ├─ standard tools (memory, runtime, chat, web, qemu, task)
    │      └─ VM tools (browser, context, desktop, files, shell, windows)
    │
    └─ external_tools = manager.get_external_tools(runtime_id)
           │
           └─ MCP servers (if any user-defined MCP servers)
           
result: builtin_tools + external_tools (no duplicates)
```

## 验证清单

修复后需要验证：

- [ ] VM 工具只出现一次（source: builtin）
- [ ] MCP 服务器工具正常发现（如果有的话）
- [ ] 不同 runtime 看到相同的 VM 工具集
- [ ] LLM API 不再报告重复的函数名
- [ ] 所有 VM 工具（browser_*, context_*, desktop_*, file_*, shell_*, window_*）都可用

## 相关文件

### 修改的文件
- `novaic-backend/tools_server/runtime_manager.py` - 删除重复的 VM 工具获取逻辑

### 保持不变的文件
- `novaic-backend/tools_server/tools.py` - VM 工具作为 builtin 保留
- `novaic-backend/tools_server/api.py` - 工具合并逻辑保持不变
- `novaic-backend/gateway/api/internal.py` - Gateway API 可以保留（可能有其他用途）

## 总结

### 问题根源
VM 工具在两个不同的地方被添加：
1. 作为 builtin（正确）
2. 作为 external（错误）

### 根本原因
架构设计不清晰，VM 工具的归属定位不明确，导致在重构时出现重复添加。

### 修复原则
- VM 工具是系统内置功能，应该作为 builtin
- external_tools 只应该包含真正的外部 MCP 服务器工具
- 保持单一数据源原则（Single Source of Truth）

### 经验教训
1. 工具注册流程需要清晰的架构设计文档
2. builtin 和 external 的边界需要明确定义
3. 代码中应该添加注释说明设计意图
4. 应该有去重机制作为防御性编程
