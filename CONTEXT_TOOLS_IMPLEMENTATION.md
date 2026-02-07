# Context 工具实现总结

## 概述
在 `novaic-backend/gateway/clients/vmuse_adapter.py` 中成功实现了4个 Context 上下文工具。

## 实现的工具

### 1. system_snapshot - 系统快照
**功能**: 获取系统状态快照（进程、内存、磁盘、网络、CPU）

**参数**:
- `include` (可选): 要包含的组件数组，可选值：`["processes", "memory", "disk", "network", "cpu"]`
- 默认包含所有组件

**实现细节**:
- 通过 Guest Agent 执行多个系统命令
- `ps aux --sort=-%mem | head -20` - 获取前20个内存占用最高的进程
- `free -h` - 获取内存信息
- `df -h` - 获取磁盘使用情况
- `ip addr show` - 获取网络接口信息
- `top -bn1 | head -5` - 获取 CPU 信息

### 2. clipboard_get - 获取剪贴板
**功能**: 获取虚拟机剪贴板内容

**参数**: 无

**实现细节**:
- 使用 `xclip` 或 `xsel` 工具
- 命令: `xclip -selection clipboard -o 2>/dev/null || xsel --clipboard --output 2>/dev/null || echo ''`
- 支持自动降级（xclip → xsel → 空字符串）

### 3. clipboard_set - 设置剪贴板
**功能**: 设置虚拟机剪贴板内容

**参数**:
- `content` (必需): 要设置的内容

**实现细节**:
- 使用 `shlex.quote()` 安全地引用内容，防止命令注入
- 使用 `xclip` 或 `xsel` 工具
- 命令: `echo {quoted_content} | xclip -selection clipboard`

**安全性**: ✅ 使用 `shlex.quote()` 防止命令注入

### 4. environment_info - 环境信息
**功能**: 获取虚拟机环境信息（OS、架构、环境变量）

**参数**: 无

**实现细节**:
- `uname -a` - 获取操作系统信息
- `cat /etc/os-release | grep PRETTY_NAME` - 获取发行版信息
- `uname -m` - 获取架构信息
- `env | grep -E '^(PATH|HOME|USER|DISPLAY|LANG|SHELL)'` - 获取常用环境变量

## 技术实现

### 辅助方法
添加了 `_exec_guest_command()` 辅助方法：
```python
async def _exec_guest_command(self, agent_id: str, command: str) -> Dict[str, Any]:
    """执行 Guest Agent 命令的辅助方法"""
    url = f"{self.vmcontrol_url}/api/vms/{agent_id}/guest/exec"
    payload = {
        "path": "/bin/bash",
        "args": ["-c", command],
        "wait": True
    }
```

### 路由配置
在 `call_tool()` 方法中添加了4个工具的路由：
```python
# Context 工具
elif tool_name == "system_snapshot":
    return await self._system_snapshot(vm_id, arguments)

elif tool_name == "clipboard_get":
    return await self._clipboard_get(vm_id, arguments)

elif tool_name == "clipboard_set":
    return await self._clipboard_set(vm_id, arguments)

elif tool_name == "environment_info":
    return await self._environment_info(vm_id, arguments)
```

### MCP 工具定义
在 `list_tools_mcp_format()` 方法中添加了4个工具的 MCP 标准格式定义。

## 依赖项
- 添加了 `import shlex` 用于安全的命令参数引用

## 安全性考虑

### 命令注入防护
✅ **clipboard_set 工具**:
- 使用 `shlex.quote()` 对用户输入进行安全引用
- 防止恶意输入注入 shell 命令

### 错误处理
所有工具都包含完整的异常处理：
```python
try:
    # ... 执行操作
    return {"success": True, "result": ...}
except Exception as e:
    logger.error(f"[VmuseAdapter] Operation failed: {e}")
    return {"success": False, "error": f"Operation failed: {str(e)}"}
```

## 验证结果

### 语法验证
✅ Python 语法正确
✅ 所有方法签名正确
✅ 模块导入完整

### 结构验证
✅ 5个方法实现：
  - `_exec_guest_command(agent_id, command)`
  - `_system_snapshot(vm_id, arguments)`
  - `_clipboard_get(vm_id, arguments)`
  - `_clipboard_set(vm_id, arguments)`
  - `_environment_info(vm_id, arguments)`

✅ 4个工具路由已添加到 `call_tool()`
✅ 4个工具定义已添加到 `list_tools_mcp_format()`
✅ `shlex` 模块已导入并使用

## 使用示例

### system_snapshot
```python
# 获取所有系统信息
result = await adapter.call_tool("system_snapshot", {}, vm_id="1")

# 只获取内存和磁盘信息
result = await adapter.call_tool("system_snapshot", {
    "include": ["memory", "disk"]
}, vm_id="1")
```

### clipboard_get
```python
result = await adapter.call_tool("clipboard_get", {}, vm_id="1")
# result["result"]["content"] 包含剪贴板内容
```

### clipboard_set
```python
result = await adapter.call_tool("clipboard_set", {
    "content": "Hello, World!"
}, vm_id="1")
```

### environment_info
```python
result = await adapter.call_tool("environment_info", {}, vm_id="1")
# result["result"] 包含 os, distro, arch, env 等信息
```

## 注意事项

1. **剪贴板工具依赖**:
   - 虚拟机中需要安装 `xclip` 或 `xsel` 工具
   - Ubuntu/Debian: `sudo apt install xclip xsel`
   - 如果两个工具都不可用，会优雅地降级

2. **Guest Agent 要求**:
   - 所有工具都依赖 vmcontrol 的 Guest Agent
   - 确保虚拟机中 Guest Agent 正常运行

3. **超时设置**:
   - 当前超时设置为 30 秒
   - 对于耗时较长的操作（如 system_snapshot），可能需要调整超时时间

4. **错误处理**:
   - 所有工具都返回标准格式：`{"success": bool, "result": {...}}` 或 `{"success": bool, "error": str}`
   - 便于统一的错误处理

## 下一步

建议在实际虚拟机环境中测试这些工具：

1. 启动 vmcontrol 服务
2. 确保虚拟机中 Guest Agent 运行正常
3. 在虚拟机中安装必要的工具（xclip/xsel）
4. 通过 Tools Server 测试工具调用
5. 验证返回结果格式和内容

## 相关文件

- `novaic-backend/gateway/clients/vmuse_adapter.py` - 主实现文件
- `test_context_tools_syntax.py` - 语法验证脚本
- `CONTEXT_TOOLS_IMPLEMENTATION.md` - 本文档

---

**实现完成日期**: 2026-02-06
**实现者**: AI Assistant
**状态**: ✅ 已完成并通过验证
