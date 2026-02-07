# VMUSE 完整迁移总结

## ✅ 已完成的工作

### 1. VM 内的完整 VMUSE HTTP 服务器

**文件**: `novaic-backend/scripts/vmuse_complete_server.py`

- 不依赖 FastMCP
- 整合所有原始 VMUSE 工具：
  - Browser Tools (navigate, click, type, screenshot, scroll, evaluate)
  - Desktop Tools (screenshot, mouse, keyboard)
  - Shell Tools (command execution)
  - File Tools (read, write, list)
  - Window Tools (list, focus, maximize, minimize, close, resize, launch)
  - Context Tools (snapshot, clipboard, environment)

**目录结构**:
```
novaic-backend/scripts/
├── vmuse_complete_server.py          # HTTP 服务器主程序
└── vmuse_tools/                      # 工具模块目录
    ├── __init__.py
    ├── config.py                     # 配置
    ├── browser.py                    # 浏览器工具
    ├── desktop.py                    # 桌面工具
    ├── shell.py                      # Shell 工具
    ├── files.py                      # 文件工具
    ├── windows.py                    # 窗口管理工具
    └── context.py                    # 环境感知工具
```

**API 路由**:
- `/api/browser/{operation}` - 浏览器操作
- `/api/desktop/{operation}` - 桌面操作
- `/api/shell/{operation}` - Shell 操作
- `/api/file/{operation}` - 文件操作
- `/health` - 健康检查

### 2. vmcontrol 通用代理路由

**文件**: `novaic-app/src-tauri/vmcontrol/src/api/routes/vmuse.rs`

**路由**: `/api/vms/:id/vmuse/:tool/:operation`

**功能**:
- 接收来自 backend 的请求
- 通过 Guest Agent 执行 `curl` 命令
- 调用 VM 内的 HTTP 服务器
- 返回统一的 JSON 响应

**示例**:
```
POST /api/vms/e270ec13/vmuse/browser/navigate
Body: {"url": "https://example.com"}

→ Guest Agent curl → http://localhost:8080/api/browser/navigate
```

### 3. 移除 vmuse_adapter 依赖

**修改的文件**:

1. **`novaic-backend/tools_server/executor.py`**
   - 移除了 `from gateway.clients.vmuse_adapter import get_vmuse_adapter`
   - 添加了 `VM_TOOL_MAPPING` 映射表
   - VM 工具调用改为直接 HTTP 请求到 vmcontrol
   - 添加了 `VMCONTROL_URL` 配置

2. **`novaic-backend/tools_server/tools.py`**
   - 添加了 `VM_TOOLS` 列表（13 个工具的完整定义）
   - 移除了对 `vmuse_adapter.list_tools_mcp_format()` 的调用
   - 直接使用 `VM_TOOLS` 作为工具定义源

3. **`novaic-backend/gateway/api/internal/vm.py`**
   - 移除了 `from gateway.clients.vmuse_adapter import get_vmuse_adapter`
   - 改为 `from tools_server.tools import VM_TOOLS`
   - 直接返回 `VM_TOOLS` 而不是调用 adapter

### 4. 保留的向后兼容路由

**vmcontrol 中保留的专门路由**（可选使用）:
- `/api/vms/:id/browser/navigate`
- `/api/vms/:id/browser/click`
- `/api/vms/:id/browser/type`
- `/api/vms/:id/browser/content`
- `/api/vms/:id/browser/screenshot`

这些路由仍然可用，但新的通用路由 `/api/vms/:id/vmuse/:tool/:operation` 可以处理所有工具。

## 📊 新架构图

```
┌──────────────────────────────────────────────────────┐
│                  Agent (LLM)                         │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│             executor.py (Tools Server)               │
│  • 直接调用 vmcontrol API                            │
│  • 使用 VM_TOOL_MAPPING 映射工具                     │
│  • HTTP POST 到 vmcontrol                            │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│             vmcontrol (Rust Service)                 │
│                                                      │
│  通用路由: /api/vms/:id/vmuse/:tool/:operation      │
│  • browser/navigate                                  │
│  • desktop/screenshot                                │
│  • desktop/mouse                                     │
│  • shell/command                                     │
│  • file/read, file/write                            │
│  • ...                                               │
└────────────────────┬─────────────────────────────────┘
                     │ Guest Agent (curl)
┌────────────────────▼─────────────────────────────────┐
│                    VM 内部                           │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  vmuse_complete_server.py (HTTP Server)      │  │
│  │  监听: localhost:8080                        │  │
│  │                                              │  │
│  │  完整 VMUSE 功能:                             │  │
│  │  • BrowserTools (Playwright)                 │  │
│  │  • DesktopTools (xdotool, scrot)            │  │
│  │  • ShellTools (bash)                         │  │
│  │  • FileTools (文件操作)                       │  │
│  │  • WindowTools (wmctrl, xdotool)            │  │
│  │  • ContextTools (系统信息)                    │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 🔄 调用流程示例

### browser_navigate 调用

```python
# 1. Agent 调用工具
result = await executor.execute_tool(
    tool_name="browser_navigate",
    arguments={"url": "https://example.com"},
    agent_id="e270ec13"
)

# 2. executor.py 查找映射
tool, operation = VM_TOOL_MAPPING["browser_navigate"]  # ("browser", "navigate")

# 3. executor.py 发送 HTTP 请求
url = f"{VMCONTROL_URL}/api/vms/e270ec13/vmuse/browser/navigate"
response = await httpx.post(url, json={"url": "https://example.com"})

# 4. vmcontrol 执行 curl 命令 (通过 Guest Agent)
curl -s -X POST http://localhost:8080/api/browser/navigate \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'

# 5. VM 内的 vmuse_complete_server.py 处理请求
async def browser_navigate(request):
    data = await request.json()
    browser = get_browser_tools()
    result = await browser.navigate(data.get('url'))
    return web.json_response({"status": "success", "url": result.get('url')})

# 6. 返回结果
# vmcontrol ← VM: {"status": "success", "url": "..."}
# executor ← vmcontrol: {"status": "success", "url": "..."}
# Agent ← executor: {"success": True, "content": [...]}
```

## 📁 需要删除的文件（可选）

以下文件已不再使用，可以考虑删除：

- `novaic-backend/gateway/clients/vmuse_adapter.py` (2762 行)
- `novaic-backend/gateway/clients/vmuse_adapter_example.py`
- `novaic-backend/tests/unit/gateway/test_vmuse_adapter.py`

## ⚠️ 注意事项

1. **VM 初始化**: 新的 VM 需要：
   - 安装 `aiohttp`: `pip install aiohttp`
   - 部署 `vmuse_complete_server.py` 到 `/opt/novaic/scripts/`
   - 部署 `vmuse_tools/` 到 `/opt/novaic/scripts/`
   - 配置 systemd 服务自动启动

2. **端口**: VM 内 HTTP 服务器监听 `localhost:8080`

3. **环境变量**: 
   - `VMCONTROL_URL`: vmcontrol 服务地址 (默认: `http://127.0.0.1:18888`)
   - `GATEWAY_URL`: gateway 服务地址 (默认: `http://127.0.0.1:19999`)

4. **Guest Agent**: 确保 QEMU Guest Agent 正常运行

## 🎯 优势

1. **架构简化**: 移除了中间的 adapter 层
2. **直接通信**: executor → vmcontrol → VM，减少转换
3. **完整功能**: 恢复了所有原始 VMUSE 工具
4. **独立部署**: VM 内服务器独立运行，不依赖外部 FastMCP
5. **易于维护**: 工具定义集中在 `tools.py`，不分散在多个文件

## 📝 TODO (可选)

- [ ] 更新 cloud-init 配置，自动部署 vmuse_complete_server
- [ ] 添加 VM 内服务器的健康检查机制
- [ ] 实现工具调用的重试机制
- [ ] 添加详细的调用日志
- [ ] 性能优化（如果需要）
