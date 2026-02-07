# 工具注册流程详解

## 修复前的流程（有重复）

```
┌─────────────────────────────────────────────────────────────┐
│                    Tools Server API                         │
│         GET /internal/runtimes/{runtime_id}/tools          │
└─────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │ builtin_tools│          │external_tools│
        └──────────────┘          └──────────────┘
                │                         │
                ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │get_all_tools()│          │RuntimeManager│
        │              │          │_discover_    │
        │              │          │tools()       │
        └──────────────┘          └──────────────┘
                │                         │
     ┌──────────┴──────────┐   ┌──────────┴──────────┐
     ▼                     ▼   ▼                     ▼
┌─────────┐        ┌─────────┐ ┌──────────┐  ┌──────────────┐
│Standard │        │VM Tools │ │MCP Tools │  │Gateway API   │
│Tools    │        │vmuse_   │ │Registry  │  │/vm-tools     │
│memory_* │        │adapter  │ │discovery │  │              │
│runtime_*│        │         │ │          │  │              │
│chat_*   │        │         │ │          │  │              │
│web_*    │        │         │ │          │  │              │
│qemu_*   │        │         │ │          │  │              │
│task_*   │        │         │ │          │  │              │
└─────────┘        └─────────┘ └──────────┘  └──────────────┘
                        │                             │
                        │                             ▼
                        │                      ┌──────────────┐
                        │                      │vmuse_adapter │
                        │                      │.list_tools   │
                        │                      │_mcp_format() │
                        │                      └──────────────┘
                        │                             │
                        │◄────────────────────────────┘
                        │
                        │ (相同的 VM 工具被添加两次！)
                        │
                        ▼
              ┌──────────────────┐
              │ browser_navigate │
              │ browser_click    │  ← 出现在 builtin
              │ context_capture  │
              │ desktop_screenshot│
              │ ...              │
              └──────────────────┘
                        │
                        │
                        ▼
              ┌──────────────────┐
              │ browser_navigate │
              │ browser_click    │  ← 又出现在 external
              │ context_capture  │
              │ desktop_screenshot│
              │ ...              │
              └──────────────────┘
                        │
                        ▼
                  【重复错误】
        LLM API: function name duplicated
```

## 修复后的流程（正确）

```
┌─────────────────────────────────────────────────────────────┐
│                    Tools Server API                         │
│         GET /internal/runtimes/{runtime_id}/tools          │
└─────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │ builtin_tools│          │external_tools│
        └──────────────┘          └──────────────┘
                │                         │
                ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │get_all_tools()│          │RuntimeManager│
        │              │          │_discover_    │
        │              │          │tools()       │
        └──────────────┘          └──────────────┘
                │                         │
     ┌──────────┴──────────┐             ▼
     ▼                     ▼      ┌──────────────┐
┌─────────┐        ┌─────────┐   │MCP Tools     │
│Standard │        │VM Tools │   │Registry      │
│Tools    │        │vmuse_   │   │discovery     │
│memory_* │        │adapter  │   │(用户自定义)  │
│runtime_*│        │         │   └──────────────┘
│chat_*   │        │         │
│web_*    │        │         │
│qemu_*   │        │         │
│task_*   │        │         │
└─────────┘        └─────────┘
     │                  │
     └────────┬─────────┘
              │
              ▼
    ┌──────────────────┐
    │  builtin_tools   │
    │                  │
    │ Standard Tools:  │
    │  - memory_save   │
    │  - runtime_list  │
    │  - chat_reply    │
    │  - web_search    │
    │  - qemu_status   │
    │  - task_async    │
    │                  │
    │ VM Tools:        │
    │  - browser_*     │
    │  - context_*     │
    │  - desktop_*     │
    │  - file_*        │
    │  - shell_*       │
    │  - window_*      │
    └──────────────────┘
              │
              │ (VM 工具只在这里，只出现一次)
              │
              └────────┬────────┐
                       │        │
                       ▼        ▼
              ┌──────────┐  ┌──────────┐
              │LLM API   │  │工具调用  │
              │          │  │执行      │
              │无重复错误│  │          │
              └──────────┘  └──────────┘
```

## 代码调用链详解

### 1. 工具获取入口

```python
# tools_server/api.py:245
@internal_router.get("/runtimes/{runtime_id}/tools")
async def get_tools(runtime_id: str):
    """获取工具列表（内置 + 外部）"""
    
    # Step 1: 获取内置工具（包括 VM 工具）
    builtin_tools = get_all_tools()
    
    # Step 2: 获取外部工具（MCP 服务器）
    external_tools = manager.get_external_tools(runtime_id)
    
    # Step 3: 合并返回
    return {
        "tools": builtin_tools + external_tools,
        "builtin_count": len(builtin_tools),
        "external_count": len(external_tools),
    }
```

### 2. 内置工具获取

```python
# tools_server/tools.py:736
def get_all_tools() -> List[Dict[str, Any]]:
    """获取所有内置工具"""
    tools = []
    
    # 2.1 添加标准内置工具
    # BUILTIN_TOOLS = {
    #     "memory": [...],    # 10 个工具
    #     "runtime": [...],   # 7 个工具
    #     "chat": [...],      # 6 个工具
    #     "web": [...],       # 2 个工具
    #     "qemu": [...],      # 5 个工具
    #     "task": [...],      # 5 个工具
    # }
    for category_tools in BUILTIN_TOOLS.values():
        tools.extend(category_tools)
    
    # 2.2 添加 VM 工具（修复后：只在这里添加）
    try:
        from gateway.clients.vmuse_adapter import get_vmuse_adapter
        adapter = get_vmuse_adapter()
        vm_tools = adapter.list_tools_mcp_format()
        tools.extend(vm_tools)
    except Exception as e:
        logger.warning(f"Failed to load VM tools: {e}")
    
    return tools
```

### 3. 外部工具发现（修复后）

```python
# tools_server/runtime_manager.py:186
async def _discover_tools(self, runtime_id: str) -> None:
    """发现外部 MCP 工具"""
    
    # 3.1 注册端口对应的 MCP 服务器
    for name, port in context.ports.items():
        if isinstance(port, int):
            self._registry.register_server(
                name=f"{runtime_id}_{name}",
                port=port,
                enabled=True,
            )
    
    # 3.2 发现所有 MCP 工具
    tools = await self._registry.discover_all_tools(use_cache=False)
    
    # 3.3 过滤出属于当前 runtime 的工具
    runtime_tools = [
        tool for tool in tools
        if tool.get("_server", "").startswith(f"{runtime_id}_")
    ]
    
    # 修复：删除了从 Gateway 获取 VM 工具的代码
    # NOTE: VM 工具不在这里添加！
    # VM 工具已经在 tools.py 的 get_all_tools() 中作为 builtin 添加
    
    # 3.4 更新上下文中的外部工具列表
    self._runtimes[runtime_id].external_tools = runtime_tools
```

### 4. VM 工具定义

```python
# gateway/clients/vmuse_adapter.py
class VmuseAdapter:
    """VM 工具适配器（单例）"""
    
    def list_tools_mcp_format(self) -> List[Dict[str, Any]]:
        """返回所有 VM 工具（MCP 格式）"""
        return [
            # Browser tools (6)
            {
                "name": "browser_navigate",
                "description": "Navigate to a URL in the browser",
                "inputSchema": {...}
            },
            {
                "name": "browser_click",
                "description": "Click on coordinates",
                "inputSchema": {...}
            },
            # ... more browser tools
            
            # Context tools (2)
            {
                "name": "context_capture",
                "description": "Capture current context",
                "inputSchema": {...}
            },
            # ... more context tools
            
            # Desktop tools (6)
            {
                "name": "desktop_screenshot",
                "description": "Take screenshot",
                "inputSchema": {...}
            },
            # ... more desktop tools
            
            # File tools (6)
            {
                "name": "file_read",
                "description": "Read file",
                "inputSchema": {...}
            },
            # ... more file tools
            
            # Shell tools (2)
            {
                "name": "shell_execute",
                "description": "Execute shell command",
                "inputSchema": {...}
            },
            # ... more shell tools
            
            # Window tools (3)
            {
                "name": "window_focus",
                "description": "Focus window",
                "inputSchema": {...}
            },
            # ... more window tools
        ]
```

## 工具分类和数量

### Builtin Tools（修复后）

```
Standard Tools (35 个)
├── memory (10)
│   ├── memory_save
│   ├── memory_recall
│   ├── memory_delete
│   ├── memory_list_namespaces
│   ├── task_log
│   ├── task_history
│   ├── goal_set
│   ├── goal_progress
│   ├── goal_complete
│   └── session_state
│
├── runtime (7)
│   ├── runtime_list
│   ├── runtime_history
│   ├── runtime_send
│   ├── runtime_rest
│   ├── subagent_spawn
│   ├── subagent_query
│   └── subagent_cancel
│
├── chat (6)
│   ├── chat_reply
│   ├── chat_ask
│   ├── chat_notify
│   ├── chat_show_image
│   ├── chat_history
│   └── chat_get_message
│
├── web (2)
│   ├── web_search
│   └── web_fetch
│
├── qemu (5)
│   ├── qemu_ssh_exec
│   ├── qemu_status
│   ├── qemu_start_vm
│   ├── qemu_restart_vm
│   └── qemu_shutdown_vm
│
└── task (5)
    ├── task_async
    ├── task_query
    ├── task_list
    ├── task_cancel
    └── task_summary

VM Tools (25 个)
├── browser (6)
│   ├── browser_navigate
│   ├── browser_click
│   ├── browser_type
│   ├── browser_scroll
│   ├── browser_back
│   └── browser_screenshot
│
├── context (2)
│   ├── context_capture
│   └── context_explain
│
├── desktop (6)
│   ├── desktop_screenshot
│   ├── desktop_move_cursor
│   ├── desktop_click
│   ├── desktop_type
│   ├── desktop_key_press
│   └── desktop_scroll
│
├── file (6)
│   ├── file_read
│   ├── file_write
│   ├── file_list
│   ├── file_create
│   ├── file_delete
│   └── file_move
│
├── shell (2)
│   ├── shell_execute
│   └── shell_execute_stream
│
└── window (3)
    ├── window_focus
    ├── window_list
    └── window_info

Total Builtin: 60 个工具
```

### External Tools

```
External Tools (用户定义)
└── (通过 MCP 协议发现的外部服务器工具)
    例如：
    - 用户自定义的 MCP 服务器
    - 第三方 MCP 服务
    - 通过端口发现的外部工具
```

## 关键设计原则

### 1. 单一数据源（Single Source of Truth）
- VM 工具只在 `vmuse_adapter` 中定义
- `tools.py` 和 `runtime_manager.py` 都从同一个源获取
- 修复后：只有 `tools.py` 获取，避免重复

### 2. 清晰的工具分类
- **Builtin Tools**：系统内置，直接 Python 调用
  - Standard tools: 标准功能工具
  - VM tools: VM 控制工具
- **External Tools**：外部 MCP 服务器，通过协议调用

### 3. 全局 vs 局部
- **全局工具（builtin）**：所有 runtime 共享
  - 所有 runtime 看到相同的 builtin 工具集
  - 包括 VM 工具（因为 VM 是全局的）
- **局部工具（external）**：每个 runtime 可能不同
  - 根据 runtime 配置的端口发现
  - 可能包含用户自定义的 MCP 服务器

## 测试验证

### 验证工具不重复
```bash
# 获取工具列表
curl http://localhost:8001/internal/runtimes/rt-xxx/tools | jq '.tools[].name' | sort | uniq -d

# 预期输出：空（没有重复）
```

### 验证 VM 工具存在
```bash
# 检查 VM 工具
curl http://localhost:8001/internal/runtimes/rt-xxx/tools | jq '.tools[] | select(.name | startswith("browser_"))'

# 预期输出：所有 browser_* 工具，且 source: builtin
```

### 验证工具总数
```bash
# 统计工具数量
curl http://localhost:8001/internal/runtimes/rt-xxx/tools | jq '.total'

# 预期输出：
# - 如果没有外部 MCP 服务器：60（35 标准 + 25 VM）
# - 如果有外部 MCP 服务器：60 + 外部工具数
```
