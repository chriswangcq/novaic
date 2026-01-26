"""
NovAIC Core - The AI Computer Engine

NovAIC = Nov(a) + AIC (AI Computer)

A MCP (Model Context Protocol) server that exposes desktop capabilities to AI agents.
Supports both HTTP API and SSE (Server-Sent Events) for Cursor/Claude Desktop integration.

Features:
- 44+ MCP tools for desktop, browser, shell, files, windows
- Persistent memory system
- Context awareness (system snapshot, directory analysis)
- Result caching for large outputs
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from .config import settings
from .tools.desktop import DesktopTools
from .tools.browser import BrowserTools, get_browser_tools
from .tools.shell import ShellTools
from .tools.files import FileTools
from .tools.windows import WindowTools
from .tools.memory import MemoryTools, get_memory_tools
from .tools.context import ContextTools, get_context_tools
from .tools.result_cache import ResultCache, get_result_cache, truncate_if_needed


# ==================== MCP Schema ====================

class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPCallRequest(BaseModel):
    """MCP tool call request"""
    name: str
    arguments: Dict[str, Any]


# ==================== Server Instructions ====================

SERVER_INSTRUCTIONS = """# NovAIC - AI Computer Engine 使用指南

NovAIC 提供 44+ MCP 工具，让你能够控制桌面、浏览器、文件系统等。请遵循以下策略以获得最佳效果。

## 🖥️ 桌面操作策略 (Desktop)

### 点击前必须确认准星位置！
这是最重要的规则。盲目点击会导致操作失败。

**强制工作流程：**
1. `screenshot()` → 获取全屏截图，估算目标坐标 (X, Y)
2. `screenshot(center={"x":X, "y":Y}, zoom_factor=2)` → 放大查看，确认 MAGENTA 准星是否在目标上
3. 准星在目标上？ → 执行 `mouse(action="click", x=X, y=Y)`
4. 准星不在目标上？ → 调整坐标，重复步骤 2-3

### Zoom Factor 选择
- 大按钮: zoom_factor=2
- 中等图标: zoom_factor=3
- 小元素: zoom_factor=4-5

## 🌐 浏览器 vs 桌面

| 场景 | 推荐工具 |
|------|----------|
| 网页操作 | `browser_*` 系列（更可靠） |
| 本地应用（微信、VSCode等） | `screenshot` + `mouse` + `keyboard` |
| 需要看到页面 | `browser_screenshot` 或 `screenshot` |

### 浏览器工具使用
- 优先用选择器：`browser_click(selector="text=登录")` 比坐标点击更可靠
- 等待加载：`browser_navigate(url, wait_until="networkidle")`

## 🧠 记忆系统策略 (Memory)

### 何时保存记忆
- 重要上下文：项目信息、用户偏好
- 多步骤任务的中间状态
- 需要跨会话保持的信息

```
memory_save("project_context", {"name": "xxx", "tech_stack": [...]})
memory_recall("project_context")  # 下次对话时回忆
```

### 目标跟踪
复杂任务使用 goal 系列工具：
```
goal_set("完成用户认证模块", subtasks=["设计数据库", "实现API", "测试"])
goal_progress(completed_subtask="设计数据库")
goal_complete(summary="已完成所有子任务")
```

## 📁 文件操作

- 读取前检查文件是否存在：`list_files(path)`
- 大文件会被截断，使用 `result_get(result_id)` 获取完整内容

## 🪟 窗口管理

1. 先 `list_windows()` 获取窗口列表
2. 使用 `window_id` 进行操作：`focus_window`, `maximize_window` 等
3. 启动应用：`launch_app("firefox")` 是非阻塞的

## 💻 Shell 命令

- GUI 应用必须后台运行：`run_command(command="firefox", background=True)`
- 长时间命令设置超时：`run_command(command="...", timeout=120)`

## 📦 结果缓存

当输出被截断时，会返回 `result_id`：
```
result_get(result_id="xxx", start_line=1, end_line=100)  # 按行获取
result_get(result_id="xxx", start_char=0, length=5000, mode="chars")  # 按字符获取
```

## 🔍 环境感知

开始任务前，了解当前状态：
- `system_snapshot()` - 系统全貌（窗口、资源、剪贴板）
- `directory_snapshot()` - 项目结构分析
- `environment_info()` - 开发环境信息

## ⚠️ 常见错误避免

1. ❌ 不要盲目点击，总是先截图确认
2. ❌ 不要在 browser_* 和 desktop 工具之间混用坐标
3. ❌ 不要忘记 GUI 应用需要 background=True
4. ✅ 操作失败时，先截图查看当前状态再重试
"""


# ==================== Tool Definitions ====================

MCP_TOOLS: List[MCPTool] = [
    # ==================== Desktop Tools ====================
    MCPTool(
        name="screenshot",
        description="""Capture desktop screenshot with RED coordinate grid overlay.

HOW TO USE COORDINATES:
1. Look at the RED numbers on grid lines
2. Find where your target intersects with grid lines
3. Use those EXACT numbers in mouse(x=..., y=...)

🚨 CRITICAL: MUST CONFIRM CROSSHAIR ON TARGET BEFORE CLICKING!

Use zoom to verify - the MAGENTA CROSSHAIR shows exactly where you'll click:
  screenshot(center={"x":TARGET_X, "y":TARGET_Y}, zoom_factor=2)

MANDATORY WORKFLOW:
1. screenshot() → full view, estimate button at (600, 450)
2. screenshot(center={"x":600,"y":450}, zoom_factor=2) → check crosshair
3. CONFIRM: Is crosshair EXACTLY on the target center?
   - YES → proceed to mouse(action="click", x=600, y=450)
   - NO → estimate new coordinates, zoom again, repeat until confirmed
4. Click ONLY after confirming crosshair is on target

⚠️ NEVER click if crosshair is off-target! Always adjust and re-verify.""",
        inputSchema={
            "type": "object",
            "properties": {
                "center": {
                    "type": "object",
                    "description": "Center point {x,y} for zoomed capture. Use -1 for screen center.",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"}
                    }
                },
                "zoom_factor": {
                    "type": "number",
                    "description": "2.0=2x zoom (smaller area), 0.5=wider view"
                },
                "region": {
                    "type": "object",
                    "description": "Legacy: exact area {x,y,width,height}",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "width": {"type": "integer"},
                        "height": {"type": "integer"}
                    }
                },
                "grid_density": {
                    "type": "string",
                    "enum": ["fine", "normal", "coarse"],
                    "description": "fine=100px, normal=200px(default), coarse=400px"
                }
            }
        }
    ),
    MCPTool(
        name="mouse",
        description="""Control mouse: click, double-click, drag, scroll.

🚨 CRITICAL: You MUST confirm the crosshair is ON THE TARGET before clicking!

MANDATORY WORKFLOW:
1. screenshot() → estimate target at (X, Y)
2. screenshot(center={"x":X, "y":Y}, zoom_factor=2) → check CROSSHAIR position
3. CONFIRM: Is the MAGENTA CROSSHAIR exactly on the target?
   - YES → proceed to click
   - NO → adjust coordinates, zoom again, repeat until crosshair is on target
4. mouse(action="click", x=X, y=Y) → click ONLY after crosshair confirmation

⚠️ DO NOT CLICK if crosshair is not on target! Adjust and re-verify first.

ZOOM FACTOR GUIDE:
- Large buttons: zoom_factor=2
- Medium icons: zoom_factor=3  
- Small elements: zoom_factor=4-5

Actions: click | double | drag | scroll | move
Example: mouse(action="click", x=450, y=320)""",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["move", "click", "double", "drag", "scroll"]
                },
                "x": {"type": "integer", "description": "X from screenshot grid"},
                "y": {"type": "integer", "description": "Y from screenshot grid"},
                "button": {
                    "type": "string",
                    "enum": ["left", "middle", "right"],
                    "description": "Default: left"
                },
                "to_x": {"type": "integer", "description": "Drag destination X"},
                "to_y": {"type": "integer", "description": "Drag destination Y"},
                "direction": {
                    "type": "string",
                    "enum": ["up", "down", "left", "right"],
                    "description": "For scroll action"
                },
                "amount": {"type": "integer", "description": "Scroll clicks, default 3"}
            },
            "required": ["action", "x", "y"]
        }
    ),
    MCPTool(
        name="keyboard",
        description="""Type text or press hotkeys.

Modes:
- type: keyboard(action="type", text="Hello")
- key: keyboard(action="key", keys=["ctrl","s"])

Keys: ctrl, alt, shift, super, enter, tab, escape, backspace, delete, arrows, f1-f12""",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["type", "key"]
                },
                "text": {"type": "string", "description": "Text to type"},
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keys to press: ['ctrl','c']"
                }
            },
            "required": ["action"]
        }
    ),
    
    # ==================== Browser Tools (Playwright) ====================
    MCPTool(
        name="browser_navigate",
        description="""Open URL in managed Chromium browser.

Separate from user's browser. Use browser_screenshot to see result.""",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL: https://google.com"},
                "wait_until": {
                    "type": "string",
                    "enum": ["load", "domcontentloaded", "networkidle"],
                    "description": "networkidle=most reliable"
                }
            },
            "required": ["url"]
        }
    ),
    MCPTool(
        name="browser_click",
        description="""Click element by selector.

Selectors: text=Login | #id | .class | [name="x"] | role=button[name='Submit']""",
        inputSchema={
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "timeout": {"type": "integer", "description": "ms, default 5000"}
            },
            "required": ["selector"]
        }
    ),
    MCPTool(
        name="browser_type",
        description="""Type into input field. Clears existing content by default.""",
        inputSchema={
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "text": {"type": "string"},
                "clear": {"type": "boolean", "description": "Default true"}
            },
            "required": ["selector", "text"]
        }
    ),
    MCPTool(
        name="browser_screenshot",
        description="""Capture browser viewport. For desktop apps use screenshot() instead.""",
        inputSchema={
            "type": "object",
            "properties": {
                "full_page": {"type": "boolean", "description": "Capture full scrollable page"}
            }
        }
    ),
    MCPTool(
        name="browser_scroll",
        description="""Scroll page or element.""",
        inputSchema={
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
                "amount": {"type": "integer", "description": "Pixels, default 500"},
                "selector": {"type": "string", "description": "Scroll within element"}
            },
            "required": ["direction"]
        }
    ),
    MCPTool(
        name="browser_eval",
        description="""Execute JavaScript in page context.

Example: document.querySelector('h1').innerText""",
        inputSchema={
            "type": "object",
            "properties": {
                "script": {"type": "string"}
            },
            "required": ["script"]
        }
    ),
    MCPTool(
        name="browser_get_tabs",
        description="""List open browser tabs with index, url, title.""",
        inputSchema={"type": "object", "properties": {}}
    ),
    MCPTool(
        name="browser_switch_tab",
        description="""Switch to tab by index (0-based).""",
        inputSchema={
            "type": "object",
            "properties": {
                "index": {"type": "integer"}
            },
            "required": ["index"]
        }
    ),
    MCPTool(
        name="browser_close_tab",
        description="""Close tab. Current tab if index omitted.""",
        inputSchema={
            "type": "object",
            "properties": {
                "index": {"type": "integer"}
            }
        }
    ),
    
    # ==================== Shell Tools ====================
    MCPTool(
        name="run_command",
        description="""Execute shell command.

IMPORTANT: GUI apps need background=true!

Examples:
- run_command(command="ls -la")
- run_command(command="firefox", background=true)""",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string", "description": "Working dir, default ~/work"},
                "timeout": {"type": "integer", "description": "Seconds, default 60"},
                "visible": {"type": "boolean", "description": "Show in xterm window"},
                "background": {"type": "boolean", "description": "Required for GUI apps!"}
            },
            "required": ["command"]
        }
    ),
    MCPTool(
        name="run_python",
        description="""Execute Python code directly.""",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "visible": {"type": "boolean"}
            },
            "required": ["code"]
        }
    ),
    
    # ==================== File Tools ====================
    MCPTool(
        name="read_file",
        description="""Read text file. Large files may be truncated with result_id.""",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    ),
    MCPTool(
        name="write_file",
        description="""Write file. Creates dirs, overwrites existing.""",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    ),
    MCPTool(
        name="list_files",
        description="""List directory (ls -la style).""",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Default: cwd"}
            }
        }
    ),
    MCPTool(
        name="file_info",
        description="""Get file metadata: size, type, permissions, timestamps.""",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    ),
    
    # ==================== Window Tools ====================
    MCPTool(
        name="list_windows",
        description="""List all desktop windows with window_id, title, position, size.""",
        inputSchema={"type": "object", "properties": {}}
    ),
    MCPTool(
        name="focus_window",
        description="""Bring window to front. Get window_id from list_windows.""",
        inputSchema={
            "type": "object",
            "properties": {
                "window_id": {"type": "string", "description": "Hex format: 0x1234567"}
            },
            "required": ["window_id"]
        }
    ),
    MCPTool(
        name="maximize_window",
        description="""Maximize window to fill screen.""",
        inputSchema={
            "type": "object",
            "properties": {
                "window_id": {"type": "string"}
            },
            "required": ["window_id"]
        }
    ),
    MCPTool(
        name="minimize_window",
        description="""Minimize window to taskbar.""",
        inputSchema={
            "type": "object",
            "properties": {
                "window_id": {"type": "string"}
            },
            "required": ["window_id"]
        }
    ),
    MCPTool(
        name="close_window",
        description="""Close window.""",
        inputSchema={
            "type": "object",
            "properties": {
                "window_id": {"type": "string"}
            },
            "required": ["window_id"]
        }
    ),
    MCPTool(
        name="resize_window",
        description="""Resize window to specific dimensions.""",
        inputSchema={
            "type": "object",
            "properties": {
                "window_id": {"type": "string"},
                "width": {"type": "integer"},
                "height": {"type": "integer"}
            },
            "required": ["window_id", "width", "height"]
        }
    ),
    MCPTool(
        name="launch_app",
        description="""Launch app by name (non-blocking).

Apps: firefox, chromium, code, terminal, files""",
        inputSchema={
            "type": "object",
            "properties": {
                "app_name": {"type": "string"}
            },
            "required": ["app_name"]
        }
    ),
    
    # ==================== Memory Tools ====================
    MCPTool(
        name="memory_save",
        description="""Save data to persistent memory.""",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"description": "Any JSON value"},
                "namespace": {"type": "string", "description": "Default: default"},
                "persistent": {"type": "boolean", "description": "Save to disk, default true"}
            },
            "required": ["key", "value"]
        }
    ),
    MCPTool(
        name="memory_recall",
        description="""Retrieve memory. Omit key to get all in namespace.""",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "namespace": {"type": "string"}
            }
        }
    ),
    MCPTool(
        name="memory_delete",
        description="""Delete memory by key.""",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "namespace": {"type": "string"}
            },
            "required": ["key"]
        }
    ),
    MCPTool(
        name="task_log",
        description="""Log action for history tracking.""",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "details": {"type": "string"},
                "status": {"type": "string", "enum": ["completed", "failed", "in_progress"]}
            },
            "required": ["action"]
        }
    ),
    MCPTool(
        name="task_history",
        description="""Get logged action history.""",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Default 20"},
                "status_filter": {"type": "string", "enum": ["completed", "failed", "in_progress"]}
            }
        }
    ),
    MCPTool(
        name="goal_set",
        description="""Set goal with subtasks for complex operations.""",
        inputSchema={
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "subtasks": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["goal"]
        }
    ),
    MCPTool(
        name="goal_progress",
        description="""Update goal progress.""",
        inputSchema={
            "type": "object",
            "properties": {
                "completed_subtask": {"type": "string"},
                "progress_note": {"type": "string"}
            }
        }
    ),
    MCPTool(
        name="goal_complete",
        description="""Mark goal as completed.""",
        inputSchema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"}
            }
        }
    ),
    MCPTool(
        name="session_state",
        description="""Get session overview: goal, recent actions, stats.""",
        inputSchema={"type": "object", "properties": {}}
    ),
    
    # ==================== Context Tools ====================
    MCPTool(
        name="system_snapshot",
        description="""Get system state: windows, clipboard, resources, processes.""",
        inputSchema={"type": "object", "properties": {}}
    ),
    MCPTool(
        name="directory_snapshot",
        description="""Analyze directory: tree, project type, stats.""",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Default: cwd"},
                "max_depth": {"type": "integer", "description": "Default 3"},
                "include_hidden": {"type": "boolean"}
            }
        }
    ),
    MCPTool(
        name="app_state",
        description="""Get app state: windows, processes.""",
        inputSchema={
            "type": "object",
            "properties": {
                "app_name": {"type": "string"}
            },
            "required": ["app_name"]
        }
    ),
    MCPTool(
        name="clipboard_get",
        description="""Get clipboard text.""",
        inputSchema={"type": "object", "properties": {}}
    ),
    MCPTool(
        name="clipboard_set",
        description="""Set clipboard text.""",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {"type": "string"}
            },
            "required": ["content"]
        }
    ),
    MCPTool(
        name="recent_files",
        description="""Find recently modified files.""",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "limit": {"type": "integer", "description": "Default 10"},
                "extensions": {"type": "array", "items": {"type": "string"}, "description": "['.py','.txt']"}
            }
        }
    ),
    MCPTool(
        name="environment_info",
        description="""Get environment: shell, PATH, installed tools, env vars.""",
        inputSchema={"type": "object", "properties": {}}
    ),
    
    # ==================== Result Cache Tools ====================
    MCPTool(
        name="result_get",
        description="""Get truncated result by ID. Use when output shows result_id.""",
        inputSchema={
            "type": "object",
            "properties": {
                "result_id": {"type": "string"},
                "start_line": {"type": "integer", "description": "1-based"},
                "end_line": {"type": "integer"},
                "start_char": {"type": "integer", "description": "0-based"},
                "length": {"type": "integer"},
                "mode": {"type": "string", "enum": ["lines", "chars"], "description": "Default: lines"}
            },
            "required": ["result_id"]
        }
    ),
    MCPTool(
        name="result_info",
        description="""Get cached result metadata.""",
        inputSchema={
            "type": "object",
            "properties": {
                "result_id": {"type": "string"}
            },
            "required": ["result_id"]
        }
    ),
    MCPTool(
        name="result_list",
        description="""List all cached results.""",
        inputSchema={"type": "object", "properties": {}}
    ),
]


# ==================== Tool Executor ====================

async def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool by name"""
    
    # Desktop tools
    if name == "screenshot":
        return await DesktopTools.screenshot(
            region=arguments.get("region"),
            center=arguments.get("center"),
            zoom_factor=arguments.get("zoom_factor"),
            grid_density=arguments.get("grid_density")
        )
    elif name == "mouse":
        return await DesktopTools.mouse(**arguments)
    elif name == "keyboard":
        return await DesktopTools.keyboard(**arguments)
    
    # Browser tools
    elif name == "browser_navigate":
        browser = get_browser_tools()
        return await browser.navigate(
            arguments["url"],
            arguments.get("wait_until", "load")
        )
    elif name == "browser_click":
        browser = get_browser_tools()
        return await browser.click(
            arguments["selector"],
            arguments.get("timeout", 5000)
        )
    elif name == "browser_type":
        browser = get_browser_tools()
        return await browser.type_text(
            arguments["selector"],
            arguments["text"],
            arguments.get("clear", True)
        )
    elif name == "browser_screenshot":
        browser = get_browser_tools()
        return await browser.screenshot(arguments.get("full_page", False))
    elif name == "browser_scroll":
        browser = get_browser_tools()
        return await browser.scroll(
            arguments["direction"],
            arguments.get("amount", 500),
            arguments.get("selector")
        )
    elif name == "browser_eval":
        browser = get_browser_tools()
        return await browser.evaluate(arguments["script"])
    elif name == "browser_get_tabs":
        browser = get_browser_tools()
        return await browser.get_tabs()
    elif name == "browser_switch_tab":
        browser = get_browser_tools()
        return await browser.switch_tab(arguments["index"])
    elif name == "browser_close_tab":
        browser = get_browser_tools()
        return await browser.close_tab(arguments.get("index"))
    
    # Shell tools
    elif name == "run_command":
        return await ShellTools.run_command(
            arguments["command"],
            arguments.get("cwd"),
            arguments.get("timeout", 60),
            arguments.get("visible", False),
            arguments.get("background", False)
        )
    elif name == "run_python":
        return await ShellTools.run_python(
            arguments["code"],
            arguments.get("visible", False)
        )
    
    # File tools
    elif name == "read_file":
        return await FileTools.read_file(arguments["path"])
    elif name == "write_file":
        return await FileTools.write_file(arguments["path"], arguments["content"])
    elif name == "list_files":
        return await FileTools.list_files(arguments.get("path", "."))
    elif name == "file_info":
        return await FileTools.file_info(arguments["path"])
    
    # Window tools
    elif name == "list_windows":
        return await WindowTools.list_windows()
    elif name == "focus_window":
        return await WindowTools.focus_window(arguments["window_id"])
    elif name == "maximize_window":
        return await WindowTools.maximize_window(arguments["window_id"])
    elif name == "minimize_window":
        return await WindowTools.minimize_window(arguments["window_id"])
    elif name == "close_window":
        return await WindowTools.close_window(arguments["window_id"])
    elif name == "resize_window":
        return await WindowTools.resize_window(
            arguments["window_id"],
            arguments["width"],
            arguments["height"]
        )
    elif name == "launch_app":
        return await WindowTools.launch_app(arguments["app_name"])
    
    # Memory & State tools
    elif name == "memory_save":
        memory = get_memory_tools()
        return await memory.memory_save(
            arguments["key"],
            arguments["value"],
            arguments.get("namespace", "default"),
            arguments.get("persistent", True)
        )
    elif name == "memory_recall":
        memory = get_memory_tools()
        return await memory.memory_recall(
            arguments.get("key"),
            arguments.get("namespace", "default")
        )
    elif name == "memory_delete":
        memory = get_memory_tools()
        return await memory.memory_delete(
            arguments["key"],
            arguments.get("namespace", "default")
        )
    elif name == "task_log":
        memory = get_memory_tools()
        return await memory.task_log(
            arguments["action"],
            arguments.get("details"),
            arguments.get("status", "completed")
        )
    elif name == "task_history":
        memory = get_memory_tools()
        return await memory.task_history(
            arguments.get("limit", 20),
            arguments.get("status_filter")
        )
    elif name == "goal_set":
        memory = get_memory_tools()
        return await memory.goal_set(
            arguments["goal"],
            arguments.get("subtasks")
        )
    elif name == "goal_progress":
        memory = get_memory_tools()
        return await memory.goal_progress(
            arguments.get("completed_subtask"),
            arguments.get("progress_note")
        )
    elif name == "goal_complete":
        memory = get_memory_tools()
        return await memory.goal_complete(arguments.get("summary"))
    elif name == "session_state":
        memory = get_memory_tools()
        return await memory.session_state()
    
    # Context Awareness tools
    elif name == "system_snapshot":
        return await ContextTools.system_snapshot()
    elif name == "directory_snapshot":
        return await ContextTools.directory_snapshot(
            arguments.get("path", "."),
            arguments.get("max_depth", 3),
            arguments.get("include_hidden", False)
        )
    elif name == "app_state":
        return await ContextTools.app_state(arguments["app_name"])
    elif name == "clipboard_get":
        return await ContextTools.clipboard_get()
    elif name == "clipboard_set":
        return await ContextTools.clipboard_set(arguments["content"])
    elif name == "recent_files":
        return await ContextTools.recent_files(
            arguments.get("path", "."),
            arguments.get("limit", 10),
            arguments.get("extensions")
        )
    elif name == "environment_info":
        return await ContextTools.environment_info()
    
    # Result Cache tools
    elif name == "result_get":
        cache = get_result_cache()
        mode = arguments.get("mode", "lines")
        if mode == "chars":
            return cache.get_by_chars(
                arguments["result_id"],
                arguments.get("start_char", 0),
                arguments.get("length"),
                arguments.get("max_length", 4000)
            )
        else:
            return cache.get_by_lines(
                arguments["result_id"],
                arguments.get("start_line", 1),
                arguments.get("end_line"),
                arguments.get("max_lines", 100)
            )
    elif name == "result_info":
        cache = get_result_cache()
        return cache.get_info(arguments["result_id"])
    elif name == "result_list":
        cache = get_result_cache()
        return cache.list_cached()
    
    else:
        return {"success": False, "error": f"Unknown tool: {name}"}


# ==================== FastAPI App ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan - startup and shutdown"""
    print(f"🚀 NovAIC Server starting on {settings.host}:{settings.port}")
    print(f"📦 {len(MCP_TOOLS)} tools available")
    yield
    # Cleanup
    browser = get_browser_tools()
    await browser.close()
    print("👋 NovAIC Server stopped")


app = FastAPI(
    title="NovAIC",
    description="Linux Desktop MCP Server",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== MCP Endpoints ====================

@app.get("/")
async def root():
    """Server info"""
    return {
        "name": "NovAIC",
        "version": "0.1.0",
        "description": "Linux Desktop MCP Server",
        "tools": len(MCP_TOOLS)
    }


@app.get("/mcp/tools")
async def list_tools():
    """MCP tools/list endpoint"""
    return {"tools": [tool.model_dump() for tool in MCP_TOOLS]}


@app.post("/mcp/tools/call")
async def call_tool(request: MCPCallRequest):
    """MCP tools/call endpoint"""
    try:
        result = await execute_tool(request.name, request.arguments)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


# ==================== SSE Endpoints for Cursor/Claude Desktop ====================

# 存储 SSE 连接的消息队列
_sse_connections: Dict[str, asyncio.Queue] = {}


async def sse_event_generator(request: Request, connection_id: str):
    """生成 SSE 事件流"""
    queue = _sse_connections[connection_id]
    
    try:
        # 发送初始化消息
        init_msg = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "novaic",
                    "version": "0.1.0"
                },
                "capabilities": {
                    "tools": {}
                },
                "instructions": SERVER_INSTRUCTIONS
            }
        }
        yield f"data: {json.dumps(init_msg)}\n\n"
        
        while True:
            # 检查客户端是否断开
            if await request.is_disconnected():
                break
            
            try:
                # 等待消息，超时后发送心跳
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(message)}\n\n"
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                yield f": heartbeat\n\n"
    finally:
        # 清理连接
        if connection_id in _sse_connections:
            del _sse_connections[connection_id]


@app.get("/sse")
async def sse_endpoint(request: Request):
    """
    SSE 端点 - Cursor/Claude Desktop 通过此端点连接
    
    配置方式 (~/.cursor/mcp.json):
    {
        "mcpServers": {
            "novaic": {
                "url": "http://localhost:8081/sse"
            }
        }
    }
    """
    connection_id = str(uuid.uuid4())
    _sse_connections[connection_id] = asyncio.Queue()
    
    return StreamingResponse(
        sse_event_generator(request, connection_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Connection-Id": connection_id
        }
    )


@app.post("/sse")
async def sse_message(request: Request):
    """
    处理来自 SSE 客户端的 JSON-RPC 消息
    """
    body = await request.json()
    method = body.get("method", "")
    msg_id = body.get("id")
    params = body.get("params", {})
    
    # 处理 MCP 标准方法
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "novaic",
                    "version": "0.1.0"
                },
                "capabilities": {
                    "tools": {}
                },
                "instructions": SERVER_INSTRUCTIONS
            }
        }
    
    elif method == "tools/list":
        tools = []
        for tool in MCP_TOOLS:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": tools
            }
        }
    
    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        try:
            result = await execute_tool(tool_name, arguments)
            
            # 将结果转换为 MCP 格式
            content = []
            if isinstance(result, dict):
                if result.get("success") == False:
                    content.append({
                        "type": "text",
                        "text": f"Error: {result.get('error', 'Unknown error')}"
                    })
                elif "screenshot" in result:
                    # MCP 图片格式 - 使用 data + mimeType
                    content.append({
                        "type": "image",
                        "data": result["screenshot"],
                        "mimeType": "image/png"
                    })
                elif "image" in result:
                    # MCP 图片格式 - 浏览器截图等
                    content.append({
                        "type": "image",
                        "data": result["image"],
                        "mimeType": "image/png"
                    })
                else:
                    # 将结果转为 JSON 字符串
                    text_result = json.dumps(result, ensure_ascii=False, indent=2)
                    
                    # 检查是否需要截断
                    truncated_text, meta = truncate_if_needed(text_result, max_length=4000)
                    
                    content.append({
                        "type": "text",
                        "text": truncated_text
                    })
                    
                    # 如果被截断，添加元信息提示
                    if meta:
                        content.append({
                            "type": "text",
                            "text": f"\n📋 结果已截断 | ID: {meta['result_id']} | 总计 {meta['total_lines']} 行 / {meta['total_chars']} 字符\n💡 使用 result_get(result_id='{meta['result_id']}', start_line=N, end_line=M) 查询完整内容"
                        })
            else:
                text_result = str(result)
                truncated_text, meta = truncate_if_needed(text_result, max_length=4000)
                
                content.append({
                    "type": "text",
                    "text": truncated_text
                })
                
                if meta:
                    content.append({
                        "type": "text",
                        "text": f"\n📋 结果已截断 | ID: {meta['result_id']} | 总计 {meta['total_lines']} 行 / {meta['total_chars']} 字符\n💡 使用 result_get(result_id='{meta['result_id']}', start_line=N, end_line=M) 查询完整内容"
                    })
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": content,
                    "isError": result.get("success") == False if isinstance(result, dict) else False
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                    "isError": True
                }
            }
    
    elif method == "notifications/initialized":
        # 客户端确认初始化完成，不需要响应
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


# ==================== Main ====================

def main():
    """Run the server"""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )


if __name__ == "__main__":
    main()

