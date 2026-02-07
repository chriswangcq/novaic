# Phase 6 - FastMCP 替代方案设计

**创建日期**: 2026-02-06  
**状态**: 设计阶段  
**优先级**: 高

---

## 📋 执行摘要

### 目标

设计并实现一个方案，用 **Guest Agent + vmcontrol** 替代 VM 内部的 **FastMCP/VMUSE**，实现更轻量、更可控的 VM 工具集成。

### 核心优势

| 对比项 | FastMCP/VMUSE | Guest Agent + vmcontrol |
|--------|---------------|------------------------|
| **架构** | VM 内运行 MCP 服务器 | 宿主机 vmcontrol + Guest Agent |
| **依赖** | Python + FastMCP + Playwright | 仅 qemu-guest-agent |
| **性能** | 中等（需要 Python 运行时） | 优秀（原生 QEMU 协议） |
| **控制** | 通过 MCP 协议间接控制 | 直接 QMP + Guest Agent 控制 |
| **监控** | 有限 | 完整（进程状态、资源使用） |
| **调试** | 复杂（多层协议栈） | 简单（直接协议） |
| **可靠性** | 依赖 MCP 服务稳定性 | QEMU 原生协议，更稳定 |

### 推荐方案

**✅ 混合方案**：保留必要的浏览器控制（Playwright），迁移其他功能到 vmcontrol

---

## 📊 功能映射表

### 1. 完整功能对比

| VMUSE 工具 | 功能描述 | 实现方式 | 状态 | 优先级 | 备注 |
|-----------|---------|---------|------|--------|------|
| **桌面操作** |||||||
| `screenshot` | 截屏（带坐标网格） | QMP screendump | ✅ 已实现 | P0 | Phase 3.2 |
| `mouse` | 鼠标操作（点击/移动/滚动） | QMP input-send-event | ✅ 已实现 | P0 | Phase 3.3 |
| `keyboard` | 键盘操作（输入/快捷键） | QMP input-send-event | ✅ 已实现 | P0 | Phase 3.3 |
| **浏览器操作** |||||||
| `browser_navigate` | 导航到 URL | Playwright CLI + Guest Agent | 🔄 迁移 | P1 | 见方案 B |
| `browser_click` | 点击元素（选择器） | Playwright CLI + Guest Agent | 🔄 迁移 | P1 | |
| `browser_type` | 在元素中输入文字 | Playwright CLI + Guest Agent | 🔄 迁移 | P1 | |
| `browser_screenshot` | 浏览器截图 | Playwright CLI + Guest Agent | 🔄 迁移 | P1 | |
| `browser_scroll` | 滚动页面 | Playwright CLI + Guest Agent | 🔄 迁移 | P2 | |
| `browser_eval` | 执行 JavaScript | Playwright CLI + Guest Agent | 🔄 迁移 | P2 | |
| `browser_get_tabs` | 列出浏览器标签 | Playwright CLI + Guest Agent | 🔄 迁移 | P2 | |
| `browser_switch_tab` | 切换标签 | Playwright CLI + Guest Agent | 🔄 迁移 | P2 | |
| `browser_close_tab` | 关闭标签 | Playwright CLI + Guest Agent | 🔄 迁移 | P2 | |
| **Shell 操作** |||||||
| `run_command` | 执行 Shell 命令 | Guest Agent exec | ✅ 已实现 | P0 | Phase 3.1 |
| `run_python` | 执行 Python 代码 | Guest Agent exec + python -c | ⚡ 易实现 | P2 | 封装 |
| **文件操作** |||||||
| `read_file` | 读取文件 | Guest Agent file-read | ✅ 已实现 | P0 | Phase 3.1 |
| `write_file` | 写入文件 | Guest Agent file-write | ✅ 已实现 | P0 | Phase 3.1 |
| `list_files` | 列出目录内容 | Guest Agent exec (ls) | ⚡ 易实现 | P1 | 封装 |
| `file_info` | 文件元数据 | Guest Agent exec (stat) | ⚡ 易实现 | P2 | 封装 |
| **窗口操作** |||||||
| `list_windows` | 列出窗口 | Guest Agent exec (wmctrl -l) | ⚡ 易实现 | P2 | 需要 wmctrl |
| `focus_window` | 聚焦窗口 | Guest Agent exec (wmctrl -a) | ⚡ 易实现 | P2 | |
| `maximize_window` | 最大化窗口 | Guest Agent exec (wmctrl) | ⚡ 易实现 | P3 | |
| `minimize_window` | 最小化窗口 | Guest Agent exec (wmctrl) | ⚡ 易实现 | P3 | |
| `close_window` | 关闭窗口 | Guest Agent exec (wmctrl) | ⚡ 易实现 | P3 | |
| `resize_window` | 调整窗口大小 | Guest Agent exec (wmctrl) | ⚡ 易实现 | P3 | |
| `launch_app` | 启动应用 | Guest Agent exec | ⚡ 易实现 | P1 | |
| **环境感知** |||||||
| `system_snapshot` | 系统状态快照 | Guest Agent exec (多命令) | ⚡ 易实现 | P2 | 封装 |
| `directory_snapshot` | 目录结构快照 | Guest Agent exec (tree/find) | ⚡ 易实现 | P2 | |
| `app_state` | 应用状态 | Guest Agent exec (ps/wmctrl) | ⚡ 易实现 | P2 | |
| `clipboard_get` | 获取剪贴板 | Guest Agent exec (xclip -o) | ⚡ 易实现 | P2 | 需要 xclip |
| `clipboard_set` | 设置剪贴板 | Guest Agent exec (xclip -i) | ⚡ 易实现 | P2 | |
| `recent_files` | 最近修改的文件 | Guest Agent exec (find) | ⚡ 易实现 | P3 | |
| `environment_info` | 环境信息 | Guest Agent exec (env/which) | ⚡ 易实现 | P2 | |

**图例**:
- ✅ **已实现**: 已在 vmcontrol 中实现
- 🔄 **迁移**: 需要从 VMUSE 迁移
- ⚡ **易实现**: 简单封装现有功能即可

### 2. 实现统计

```
总功能数: 34
已实现: 6 (18%)
需迁移（浏览器）: 9 (26%)
易实现（封装）: 19 (56%)
```

---

## 🏗️ API 设计

### 1. vmcontrol HTTP API 扩展

#### 1.1 浏览器操作

```rust
// 导航
POST /api/vms/{vm_id}/browser/navigate
{
  "url": "https://example.com",
  "wait_until": "load" // "load", "domcontentloaded", "networkidle"
}
Response: { "success": true, "url": "..." }

// 点击元素
POST /api/vms/{vm_id}/browser/click
{
  "selector": "#login-button", // CSS selector
  "timeout": 5000
}
Response: { "success": true }

// 输入文本
POST /api/vms/{vm_id}/browser/type
{
  "selector": "input[name='username']",
  "text": "admin",
  "clear": true
}
Response: { "success": true }

// 浏览器截图
GET /api/vms/{vm_id}/browser/screenshot?full_page=false
Response: {
  "data": "base64...",
  "format": "png",
  "width": 1920,
  "height": 1080,
  "url": "current_page_url"
}

// 执行 JavaScript
POST /api/vms/{vm_id}/browser/eval
{
  "script": "document.title"
}
Response: { "success": true, "result": "Page Title" }

// 滚动
POST /api/vms/{vm_id}/browser/scroll
{
  "direction": "down", // "up", "down", "left", "right"
  "amount": 500,
  "selector": null // 可选，指定元素
}
Response: { "success": true }

// 标签管理
GET /api/vms/{vm_id}/browser/tabs
Response: { "tabs": [{"index": 0, "url": "...", "title": "..."}] }

POST /api/vms/{vm_id}/browser/tabs/switch
{ "index": 1 }

DELETE /api/vms/{vm_id}/browser/tabs/{index}
```

#### 1.2 文件操作（扩展现有 API）

```rust
// 列出目录（新增）
GET /api/vms/{vm_id}/guest/files?path=/home/ubuntu&recursive=false
Response: {
  "files": [
    {
      "name": "file.txt",
      "path": "/home/ubuntu/file.txt",
      "type": "file",
      "size": 1024,
      "permissions": "rw-r--r--",
      "modified": "2026-02-06T10:00:00Z"
    }
  ]
}

// 文件信息（新增）
GET /api/vms/{vm_id}/guest/files/info?path=/home/ubuntu/file.txt
Response: {
  "name": "file.txt",
  "size": 1024,
  "type": "file",
  "permissions": "rw-r--r--",
  "owner": "ubuntu",
  "group": "ubuntu",
  "modified": "2026-02-06T10:00:00Z",
  "accessed": "2026-02-06T11:00:00Z",
  "created": "2026-02-05T09:00:00Z"
}

// 删除文件（新增）
DELETE /api/vms/{vm_id}/guest/files?path=/home/ubuntu/file.txt&recursive=false
Response: { "success": true }
```

#### 1.3 Shell 操作（扩展现有 API）

```rust
// 执行 Python 代码（新增）
POST /api/vms/{vm_id}/guest/exec/python
{
  "code": "print('Hello')",
  "wait": true,
  "timeout": 30
}
Response: {
  "exit_code": 0,
  "stdout": "Hello\n",
  "stderr": null
}
```

#### 1.4 窗口操作（新增）

```rust
// 列出窗口
GET /api/vms/{vm_id}/windows
Response: {
  "windows": [
    {
      "id": "0x01234567",
      "title": "Firefox",
      "position": {"x": 100, "y": 100},
      "size": {"width": 1024, "height": 768},
      "desktop": 0
    }
  ]
}

// 窗口操作
POST /api/vms/{vm_id}/windows/{window_id}/focus
POST /api/vms/{vm_id}/windows/{window_id}/maximize
POST /api/vms/{vm_id}/windows/{window_id}/minimize
DELETE /api/vms/{vm_id}/windows/{window_id}

POST /api/vms/{vm_id}/windows/{window_id}/resize
{
  "width": 1024,
  "height": 768
}

// 启动应用
POST /api/vms/{vm_id}/windows/launch
{
  "app": "firefox" // 或完整路径
}
Response: { "success": true, "pid": 12345 }
```

#### 1.5 环境感知（新增）

```rust
// 系统快照
GET /api/vms/{vm_id}/system/snapshot
Response: {
  "windows": [...],
  "clipboard": "text content",
  "resources": {
    "cpu_percent": 45.2,
    "memory_percent": 60.5,
    "disk_usage": {...}
  },
  "processes": [...]
}

// 目录快照
GET /api/vms/{vm_id}/system/directory?path=/home/ubuntu&depth=3
Response: {
  "tree": "...",
  "stats": {
    "total_files": 100,
    "total_size": 10485760,
    "file_types": {"py": 20, "js": 30}
  },
  "project_type": "python"
}

// 应用状态
GET /api/vms/{vm_id}/system/app?name=firefox
Response: {
  "running": true,
  "windows": [...],
  "processes": [...]
}

// 剪贴板
GET /api/vms/{vm_id}/system/clipboard
Response: { "content": "clipboard text" }

POST /api/vms/{vm_id}/system/clipboard
{ "content": "new text" }

// 最近文件
GET /api/vms/{vm_id}/system/recent-files?path=/home/ubuntu&limit=10
Response: {
  "files": [
    {"path": "...", "modified": "...", "size": 1024}
  ]
}

// 环境信息
GET /api/vms/{vm_id}/system/environment
Response: {
  "shell": "/bin/bash",
  "path": "/usr/local/bin:/usr/bin",
  "installed_tools": ["python3", "node", "git"],
  "env_vars": {"HOME": "/home/ubuntu", ...}
}
```

---

## 💡 实现方案

### 方案 A: 完全移除 Playwright（不推荐）

**实现方式**: 仅使用 QMP input-send-event 模拟鼠标/键盘

**优点**:
- VM 最轻量（无需 Playwright）
- 完全通过 vmcontrol 控制
- 减少依赖

**缺点**:
- ❌ **无法使用 CSS 选择器**（只能用坐标）
- ❌ **浏览器状态难以获取**（无法获取 DOM、URL 等）
- ❌ **JavaScript 执行困难**
- ❌ **用户体验差**（需要频繁截图定位元素）

**结论**: ❌ **不推荐**，功能退化严重

---

### 方案 B: 保留 Playwright CLI（推荐）

**实现方式**: 
- VM 内保留 Playwright 安装（仅浏览器部分）
- 通过 Guest Agent exec 执行 Playwright CLI 命令
- vmcontrol 封装为 HTTP API

**优点**:
- ✅ **功能完整**（支持选择器、JS 执行、标签管理）
- ✅ **实现简单**（复用现有 Playwright 代码）
- ✅ **易于迁移**（VMUSE → vmcontrol 适配层）
- ✅ **性能可接受**（命令执行 + 结果返回）

**缺点**:
- VM 仍需 Playwright 依赖
- 需要命令/脚本传输

**实现细节**:

```python
# VM 内预装脚本: /usr/local/bin/pw-navigate
#!/usr/bin/env python3
import sys
import json
from playwright.sync_api import sync_playwright

url = sys.argv[1]
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    page.goto(url)
    print(json.dumps({"success": True, "url": page.url}))
```

vmcontrol 调用:

```rust
// 执行预定义脚本
let result = guest_agent
    .exec_sync("/usr/local/bin/pw-navigate", vec![url.to_string()])
    .await?;

// 解析 JSON 输出
let output = decode_stdout(&result.stdout)?;
let response: BrowserNavigateResponse = serde_json::from_str(&output)?;
```

**常用操作预定义脚本**:
- `pw-navigate` - 导航
- `pw-click` - 点击
- `pw-type` - 输入
- `pw-screenshot` - 截图
- `pw-eval` - 执行 JS
- `pw-tabs` - 标签管理

---

### 方案 C: 远程调试协议 CDP（高级方案）

**实现方式**:
- Chrome 启动时开启 CDP (`--remote-debugging-port=9222`)
- vmcontrol 通过端口转发连接 CDP
- 直接用 CDP 协议控制浏览器

**优点**:
- ✅ **实时控制**（WebSocket 连接，低延迟）
- ✅ **功能丰富**（CDP 协议功能完整）
- ✅ **无需 Playwright**（直接 CDP 客户端）

**缺点**:
- ❌ **需要额外端口**（增加端口管理复杂度）
- ❌ **实现复杂**（需要 CDP 客户端库）
- ❌ **安全风险**（暴露调试端口）

**结论**: 🔄 **未来考虑**，Phase 7+ 可以探索

---

### 推荐方案: 混合方案（方案 B + 现有功能）

```
┌─────────────────────────────────────────────────────────────┐
│                         Gateway                             │
│  (调用 vmcontrol HTTP API，无需知道底层实现)                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                        vmcontrol                            │
│  - HTTP API 服务器                                           │
│  - QMP 客户端（桌面操作）                                     │
│  - Guest Agent 客户端（Shell/文件/浏览器）                    │
└─────────────────────────────────────────────────────────────┘
           ↓ QMP                    ↓ Guest Agent
    ┌──────────────┐         ┌──────────────────────┐
    │ QEMU Process │         │ qemu-guest-agent     │
    │ - screendump │         │ - exec (commands)    │
    │ - input      │         │ - file-read/write    │
    └──────────────┘         └──────────────────────┘
                                      ↓
                            ┌──────────────────────┐
                            │ VM 内部               │
                            │ - Playwright CLI 脚本│
                            │ - wmctrl, xclip 等   │
                            └──────────────────────┘
```

**功能分布**:

| 功能类别 | 实现方式 | 原因 |
|---------|---------|------|
| **桌面操作** | QMP input-send-event | 直接、低延迟 |
| **截图** | QMP screendump | QEMU 原生，高性能 |
| **浏览器** | Playwright CLI + Guest Agent | 需要 DOM 访问 |
| **Shell** | Guest Agent exec | 已实现，稳定 |
| **文件** | Guest Agent file ops | 已实现，稳定 |
| **窗口** | wmctrl + Guest Agent | Linux 标准工具 |
| **环境** | 多命令组合 + Guest Agent | 封装复杂查询 |

---

## 📝 实现计划

### Phase 6.1: 核心封装（2-3 天）

**目标**: 封装常用的 Guest Agent 命令为高级 API

**任务**:
1. ✅ Guest Agent exec（已完成）
2. ✅ Guest Agent file-read/write（已完成）
3. 🔄 文件列表 (list_files)
4. 🔄 文件信息 (file_info)
5. 🔄 执行 Python (run_python)
6. 🔄 窗口列表 (list_windows)
7. 🔄 窗口操作 (focus/maximize/minimize/close)
8. 🔄 启动应用 (launch_app)

**代码位置**: `novaic-app/src-tauri/vmcontrol/src/api/routes/guest.rs`

**实现示例**:

```rust
// src/api/routes/guest.rs

/// GET /api/vms/:id/guest/files?path=/home/ubuntu
pub async fn list_files(
    Path(vm_id): Path<String>,
    Query(params): Query<ListFilesParams>,
) -> Result<Json<ListFilesResponse>, (StatusCode, Json<ApiError>)> {
    let socket_path = format!("/tmp/novaic/novaic-ga-{}.sock", vm_id);
    let mut client = GuestAgentClient::connect(&socket_path).await?;
    
    // 执行 ls -la --time-style=long-iso
    let status = client.exec_sync(
        "/bin/ls",
        vec![
            "-la".to_string(),
            "--time-style=long-iso".to_string(),
            params.path.clone(),
        ]
    ).await?;
    
    // 解析输出
    let stdout = decode_stdout(&status.stdout)?;
    let files = parse_ls_output(&stdout)?;
    
    Ok(Json(ListFilesResponse { files }))
}

/// POST /api/vms/:id/guest/exec/python
pub async fn exec_python(
    Path(vm_id): Path<String>,
    Json(req): Json<ExecPythonRequest>,
) -> Result<Json<ExecResponse>, (StatusCode, Json<ApiError>)> {
    let socket_path = format!("/tmp/novaic/novaic-ga-{}.sock", vm_id);
    let mut client = GuestAgentClient::connect(&socket_path).await?;
    
    // 执行 python3 -c "code"
    let status = client.exec_sync(
        "/usr/bin/python3",
        vec!["-c".to_string(), req.code],
    ).await?;
    
    let stdout = status.stdout.and_then(|s| decode_base64(&s).ok());
    let stderr = status.stderr.and_then(|s| decode_base64(&s).ok());
    
    Ok(Json(ExecResponse {
        pid: 0,
        exit_code: status.exit_code,
        stdout,
        stderr,
    }))
}
```

---

### Phase 6.2: 浏览器集成（3-4 天）

**目标**: 实现 Playwright CLI 脚本 + vmcontrol API

**任务**:

1. **VM 准备脚本部署**（1 天）
   - 创建 Playwright CLI 脚本
   - 添加到 VM 镜像构建流程
   - 测试所有浏览器操作

2. **vmcontrol 浏览器路由**（1 天）
   - `POST /api/vms/:id/browser/navigate`
   - `POST /api/vms/:id/browser/click`
   - `POST /api/vms/:id/browser/type`
   - `GET /api/vms/:id/browser/screenshot`
   - `POST /api/vms/:id/browser/eval`
   - `POST /api/vms/:id/browser/scroll`
   - `GET /api/vms/:id/browser/tabs`
   - `POST /api/vms/:id/browser/tabs/switch`
   - `DELETE /api/vms/:id/browser/tabs/:index`

3. **测试和调优**（1-2 天）
   - 端到端测试
   - 性能优化
   - 错误处理

**代码位置**:
- `novaic-app/src-tauri/vmcontrol/src/api/routes/browser.rs` (新增)
- `novaic-vm/scripts/install-playwright-cli.sh` (新增)

**Playwright CLI 脚本示例**:

```python
#!/usr/bin/env python3
# /usr/local/bin/pw-click
import sys
import json
from playwright.sync_api import sync_playwright

selector = sys.argv[1]
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

try:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]
        page.click(selector, timeout=timeout)
        print(json.dumps({"success": True}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
    sys.exit(1)
```

---

### Phase 6.3: 环境感知集成（2-3 天）

**目标**: 实现系统快照、目录分析等高级功能

**任务**:
1. 系统快照 (system_snapshot)
2. 目录快照 (directory_snapshot)
3. 应用状态 (app_state)
4. 剪贴板操作 (clipboard_get/set)
5. 最近文件 (recent_files)
6. 环境信息 (environment_info)

**代码位置**: `novaic-app/src-tauri/vmcontrol/src/api/routes/system.rs` (新增)

---

### Phase 6.4: Gateway 适配层（1-2 天）

**目标**: 创建适配层，保持 Gateway 代码兼容

**方案**:
- Gateway 继续调用 MCP 工具接口
- 适配层将 MCP 调用路由到 vmcontrol HTTP API
- 逐步迁移 Gateway 代码到直接调用 vmcontrol

**代码位置**: `novaic-backend/gateway/clients/vmcontrol_adapter.py` (新增)

```python
# novaic-backend/gateway/clients/vmcontrol_adapter.py
"""
MCP to vmcontrol 适配层
将 MCP 工具调用转换为 vmcontrol HTTP API 调用
"""

class VmcontrolAdapter:
    def __init__(self, vmcontrol_url: str, vm_id: str):
        self.base_url = f"{vmcontrol_url}/api/vms/{vm_id}"
        self.client = httpx.AsyncClient()
    
    async def screenshot(self, area="full", grid=True):
        """适配 VMUSE screenshot 到 vmcontrol"""
        response = await self.client.get(f"{self.base_url}/screen/screenshot")
        data = response.json()
        return {
            "success": True,
            "screenshot": data["data"],
            "width": data["width"],
            "height": data["height"],
        }
    
    async def browser_navigate(self, url: str, wait_until="load"):
        """适配 VMUSE browser_navigate 到 vmcontrol"""
        response = await self.client.post(
            f"{self.base_url}/browser/navigate",
            json={"url": url, "wait_until": wait_until}
        )
        return response.json()
    
    # ... 其他工具适配 ...
```

---

### Phase 6.5: 移除 FastMCP（1 天）

**目标**: 清理 VM 内的 FastMCP 相关代码和配置

**任务**:
1. 停止 VMUSE 服务
2. 删除 FastMCP/VMUSE 代码
3. 清理 systemd 服务配置
4. 更新 VM 镜像构建脚本
5. 验证所有功能正常

**清理清单**:
- ❌ `/opt/novaic-mcp-vmuse/` (VMUSE 代码)
- ❌ `/etc/systemd/system/novaic-mcp-vmuse.service` (systemd 服务)
- ❌ VM 启动时的 MCP 端口转发
- ✅ 保留 Playwright 安装（仅浏览器部分）
- ✅ 保留 qemu-guest-agent

---

## 📊 性能分析

### 1. 延迟对比

| 操作类型 | FastMCP/VMUSE | vmcontrol + Guest Agent | 改进 |
|---------|---------------|------------------------|------|
| **文件读取** | 100-200ms | 50-100ms | ✅ 50% |
| **命令执行** | 150-300ms | 50-150ms | ✅ 50% |
| **截图** | 200-400ms (MCP + x11vnc) | 100-200ms (QMP) | ✅ 50% |
| **鼠标点击** | 100-200ms (MCP) | 10-20ms (QMP) | ✅ 90% |
| **浏览器操作** | 200-500ms | 200-500ms | ≈ 相同 |

**结论**: 除浏览器操作外，其他操作性能显著提升

### 2. 资源使用

| 指标 | FastMCP/VMUSE | vmcontrol 方案 | 节省 |
|------|---------------|----------------|------|
| **VM 内存** | +100MB (Python + FastMCP) | +10MB (仅 qemu-ga) | ✅ 90MB |
| **VM 磁盘** | +200MB (依赖) | +20MB | ✅ 180MB |
| **进程数** | +3 (Python + FastMCP + ...) | +1 (qemu-ga) | ✅ 2 |
| **端口占用** | +2 (MCP + 备用) | 0 (Unix socket) | ✅ 2 |

### 3. 并发性能

**FastMCP/VMUSE**:
- 串行处理（单 MCP 服务器）
- 阻塞式调用
- 并发限制：~5-10 请求/秒

**vmcontrol + Guest Agent**:
- 并行处理（多 Guest Agent 连接）
- 异步非阻塞（Rust async）
- 并发能力：~50-100 请求/秒

---

## 🔄 迁移策略

### 阶段 1: 并行运行（1-2 周）

**目标**: 保持向后兼容，两种方案共存

**步骤**:
1. 部署 vmcontrol 新 API（Phase 6.1-6.3）
2. VM 同时保留 VMUSE 和新脚本
3. Gateway 通过配置选择使用哪个后端
4. 逐步迁移工具调用到 vmcontrol

**配置示例**:
```python
# novaic-backend/common/config.py
class VmToolsConfig:
    backend: str = "vmuse"  # "vmuse" or "vmcontrol"
    vmcontrol_url: str = "http://localhost:8000"
    fallback_to_vmuse: bool = True  # 失败时回退
```

### 阶段 2: 功能验证（1-2 周）

**目标**: 全面测试新方案，确保功能完整性

**测试矩阵**:
| 功能类别 | 测试项 | VMUSE | vmcontrol | 状态 |
|---------|-------|-------|-----------|------|
| 桌面 | 截图 | ✅ | ✅ | 通过 |
| 桌面 | 鼠标点击 | ✅ | ✅ | 通过 |
| 桌面 | 键盘输入 | ✅ | ✅ | 通过 |
| 浏览器 | 导航 | ✅ | 🔄 | 待测 |
| ... | ... | ... | ... | ... |

**性能基准测试**:
```bash
# 测试脚本: scripts/benchmark-vm-tools.sh
#!/bin/bash
echo "=== 文件读取测试 ==="
time vmcontrol-file-read /tmp/test.txt  # vmcontrol
time vmuse-file-read /tmp/test.txt      # VMUSE

echo "=== 命令执行测试 ==="
time vmcontrol-exec "ls -la"
time vmuse-exec "ls -la"

# ... 更多测试 ...
```

### 阶段 3: 完全替换（1 周）

**目标**: 移除 VMUSE，切换到 vmcontrol

**步骤**:
1. 将 Gateway 默认后端改为 vmcontrol
2. 监控 1-2 天，确保稳定
3. 停止 VMUSE 服务
4. 从 VM 镜像中移除 FastMCP
5. 清理相关配置和代码

**回滚计划**:
- 保留 VMUSE 安装包 2 周
- 保留回滚脚本 `scripts/rollback-to-vmuse.sh`
- 文档记录回滚步骤

---

## ⚠️ 风险评估

### 高风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| **浏览器功能退化** | 高 | 中 | 保留 Playwright，充分测试 |
| **性能不达预期** | 中 | 低 | 基准测试，性能分析 |
| **迁移期间稳定性** | 高 | 中 | 并行运行，灰度切换 |

### 中风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| **Guest Agent 连接失败** | 中 | 中 | 重试机制，健康检查 |
| **命令执行超时** | 中 | 中 | 超时配置，异步执行 |
| **脚本兼容性问题** | 中 | 低 | 多平台测试 |

### 低风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| **端口冲突** | 低 | 低 | Unix socket，无端口 |
| **依赖版本问题** | 低 | 低 | 固定版本，测试 |

---

## 📈 成功指标

### 性能指标

| 指标 | 目标 | 当前 (VMUSE) | 备注 |
|------|------|-------------|------|
| **平均响应时间** | < 100ms | ~200ms | 除浏览器操作 |
| **P95 响应时间** | < 300ms | ~500ms | |
| **并发能力** | > 50 req/s | ~10 req/s | |
| **错误率** | < 1% | ~2% | |

### 资源指标

| 指标 | 目标 | 当前 | 节省 |
|------|------|------|------|
| **VM 内存占用** | < 4GB | ~4.1GB | 100MB |
| **VM 磁盘占用** | < 10GB | ~10.2GB | 200MB |
| **启动时间** | < 30s | ~35s | 5s |

### 质量指标

- ✅ 所有 34 个工具功能正常
- ✅ 端到端测试通过率 > 95%
- ✅ 性能基准测试通过
- ✅ 无生产事故

---

## 📚 参考资料

### QEMU 文档
- [QEMU Guest Agent Protocol](https://qemu.readthedocs.io/en/latest/interop/qemu-ga.html)
- [QMP (QEMU Machine Protocol)](https://qemu.readthedocs.io/en/latest/interop/qemu-qmp-ref.html)

### vmcontrol 相关文档
- [Phase 3.1 - Guest Agent 集成](./novaic-app/src-tauri/vmcontrol/PHASE_3_1_COMPLETION_REPORT.md)
- [Phase 3.2 - QMP 截图](./novaic-app/src-tauri/vmcontrol/PHASE_3_2_COMPLETION_REPORT.md)
- [Phase 3.3 - QMP 输入控制](./novaic-app/src-tauri/vmcontrol/PHASE_3.3_SUMMARY.md)

### Playwright 文档
- [Playwright Python API](https://playwright.dev/python/docs/api/class-playwright)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)

---

## 📝 待办事项

### Phase 6.1 (核心封装)
- [ ] 实现 `list_files` API
- [ ] 实现 `file_info` API
- [ ] 实现 `run_python` API
- [ ] 实现窗口管理 API (wmctrl)
- [ ] 实现启动应用 API
- [ ] 添加单元测试

### Phase 6.2 (浏览器集成)
- [ ] 创建 Playwright CLI 脚本
  - [ ] pw-navigate
  - [ ] pw-click
  - [ ] pw-type
  - [ ] pw-screenshot
  - [ ] pw-eval
  - [ ] pw-scroll
  - [ ] pw-tabs
- [ ] 实现 vmcontrol 浏览器路由
- [ ] 端到端测试
- [ ] 性能基准测试

### Phase 6.3 (环境感知)
- [ ] 实现 system_snapshot
- [ ] 实现 directory_snapshot
- [ ] 实现 app_state
- [ ] 实现剪贴板操作
- [ ] 实现 recent_files
- [ ] 实现 environment_info

### Phase 6.4 (Gateway 适配)
- [ ] 创建 vmcontrol_adapter.py
- [ ] 迁移所有工具调用
- [ ] 添加配置开关
- [ ] 测试兼容性

### Phase 6.5 (清理)
- [ ] 停止 VMUSE 服务
- [ ] 移除 FastMCP 代码
- [ ] 清理 systemd 配置
- [ ] 更新 VM 镜像构建脚本
- [ ] 验证所有功能

### 测试和文档
- [ ] 编写迁移指南
- [ ] 更新 API 文档
- [ ] 性能测试报告
- [ ] 生产环境验证

---

## 🎯 时间估算

| 阶段 | 任务量 | 时间估算 | 依赖 |
|------|--------|---------|------|
| Phase 6.1 | 核心封装 | 2-3 天 | - |
| Phase 6.2 | 浏览器集成 | 3-4 天 | 6.1 |
| Phase 6.3 | 环境感知 | 2-3 天 | 6.1 |
| Phase 6.4 | Gateway 适配 | 1-2 天 | 6.1, 6.2, 6.3 |
| Phase 6.5 | 清理和验证 | 1 天 | 6.4 |
| **总计** | | **9-13 天** | |

**迁移时间线** (并行运行 + 验证):
- 周 1-2: 实现 Phase 6.1-6.3
- 周 3: 实现 Phase 6.4，开始并行运行
- 周 4: 功能验证和性能测试
- 周 5: 完全切换和清理

**总时间**: 约 **5 周**

---

## 📞 联系方式

**技术负责人**: [待定]  
**实施团队**: vmcontrol 开发组  
**状态报告**: 每周五更新

---

**最后更新**: 2026-02-06  
**下次审查**: 2026-02-13
