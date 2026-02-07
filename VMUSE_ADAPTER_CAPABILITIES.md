# VMUSE Adapter 完整能力清单

**总计：28 个工具** | **最后更新：2026-02-06**

---

## 📊 工具分类统计

| 分类 | 数量 | 完成度 |
|------|------|--------|
| Browser 浏览器 | 10 | ✅ 100% |
| Desktop 桌面 | 2 | ✅ 100% |
| File 文件 | 2 | ✅ 100% |
| Shell 命令 | 1 | ✅ 100% |
| Window 窗口 | 7 | ✅ 100% |
| Context 上下文 | 4 | ✅ 100% |
| Screenshot 截图 | 2 | ✅ 100% |
| **总计** | **28** | **✅ 100%** |

---

## 🌐 Browser 工具（10 个）

### 1. browser_navigate
**导航到 URL**
```python
browser_navigate(url="https://example.com")
```
- 参数：`url` (必需) - 目标网址
- 返回：导航结果

### 2. browser_click
**点击页面元素**
```python
browser_click(selector=".btn-submit")
```
- 参数：`selector` (必需) - CSS 选择器
- 返回：点击结果

### 3. browser_type
**在元素中输入文本**
```python
browser_type(selector="#username", text="admin")
```
- 参数：
  - `selector` (必需) - CSS 选择器
  - `text` (必需) - 输入文本
- 返回：输入结果

### 4. browser_screenshot
**浏览器页面截图**
```python
browser_screenshot()
```
- 参数：无
- 返回：Base64 编码的截图

### 5. browser_content
**获取页面文本内容**
```python
browser_content()
```
- 参数：无
- 返回：页面文本内容

### 6. browser_scroll
**滚动页面**
```python
browser_scroll(direction="down", amount=200)
```
- 参数：
  - `direction` (必需) - 方向：up/down/left/right
  - `amount` (可选，默认 100) - 滚动像素
- 返回：滚动结果

### 7. browser_eval
**执行 JavaScript 代码**
```python
browser_eval(script="document.querySelector('.btn').click()")
```
- 参数：`script` (必需) - JavaScript 代码
- 返回：执行结果

### 8. browser_get_tabs
**获取所有标签页**
```python
browser_get_tabs()
```
- 参数：无
- 返回：标签页列表

### 9. browser_switch_tab
**切换到指定标签页**
```python
browser_switch_tab(tab_index=1)
```
- 参数：`tab_index` (必需) - 标签页索引（0-based）
- 返回：切换结果

### 10. browser_close_tab
**关闭标签页**
```python
browser_close_tab()  # 关闭当前
browser_close_tab(tab_index=2)  # 关闭指定
```
- 参数：`tab_index` (可选) - 标签页索引
- 返回：关闭结果

---

## 🖱️ Desktop 工具（2 个）

### 11. mouse
**鼠标控制（8 种操作）**

⚠️ **重要**：除 `aim` 外，所有操作都**必须**使用 `aim_id`。不支持直接使用 x, y 坐标。

**正确工作流程**：
1. 先调用 `aim` 获取 `aim_id`
2. 使用 `aim_id` 执行其他操作

#### 11.1 aim - 精确定位
```python
# 绝对定位
result = mouse(action="aim", x=600, y=400, zoom=2.0)
aim_id = result["aim_id"]

# 相对调整
mouse(action="aim", aim_id=aim_id, delta_x=-50, delta_y=20, zoom=4)
```
- 返回：`aim_id` + 带网格的截图
- 这是唯一可以使用 x, y 的操作

#### 11.2 move - 移动鼠标
```python
# ✅ 正确：使用 aim_id
mouse(action="move", aim_id=aim_id)

# ❌ 错误：不支持直接使用 x, y
# mouse(action="move", x=800, y=600)  # 会返回错误
```

#### 11.3 click - 点击
```python
# ✅ 正确：使用 aim_id
mouse(action="click", aim_id=aim_id, button="left")

# ❌ 错误：不支持直接使用 x, y
# mouse(action="click", x=800, y=600)  # 会返回错误
```

#### 11.4 right_click - 右键点击
```python
# ✅ 正确：使用 aim_id
mouse(action="right_click", aim_id=aim_id)

# ❌ 错误：不支持直接使用 x, y
# mouse(action="right_click", x=800, y=600)  # 会返回错误
```

#### 11.5 double - 双击
```python
# ✅ 正确：使用 aim_id
mouse(action="double", aim_id=aim_id)

# ❌ 错误：不支持直接使用 x, y
# mouse(action="double", x=800, y=600)  # 会返回错误
```

#### 11.6 拖拽操作 (down → move → up)
```python
# ✅ 正确：使用 aim_id
# 开始拖拽
mouse(action="down", aim_id=aim_id_start, button="left")
# 拖拽移动
mouse(action="move", aim_id=aim_id_end)
# 释放（up 不需要坐标）
mouse(action="up")
```

#### 11.7 scroll - 滚轮滚动
```python
# ✅ 正确：使用 aim_id
mouse(action="scroll", aim_id=aim_id, direction="down", amount=3)

# ❌ 错误：不支持省略 aim_id
# mouse(action="scroll", direction="down", amount=3)  # 会返回错误
```

**支持的参数**：
- `action` (必需) - 操作类型：aim/move/click/right_click/double/down/up/scroll
- `x`, `y` - 坐标
- `aim_id` - Aim ID（由 aim 操作返回）
- `delta_x`, `delta_y` - 相对偏移（用于 aim 调整）
- `zoom` - 缩放倍数（用于 aim，默认 1.0）
- `button` - 鼠标按钮：left/right/middle
- `direction` - 滚动方向：up/down
- `amount` - 滚动量（默认 1）

**特性**：
- ✅ Aim 缓存（TTL 10分钟）
- ✅ 带网格截图
- ✅ 精确定位
- ✅ 完整拖拽支持

### 12. keyboard
**键盘控制（3 种操作）**

#### 12.1 type - 输入文本
```python
keyboard(action="type", text="Hello World")
keyboard(action="type", text="你好世界")  # ✅ 支持中文
```
- ✅ 自动检测非 ASCII 字符
- ✅ 中文：逐字符输入，每字符延迟 200ms
- ✅ ASCII：快速 API

#### 12.2 key - 按单个键
```python
keyboard(action="key", key="Return")
keyboard(action="key", key="Escape")
```

#### 12.3 combo - 组合键
```python
keyboard(action="combo", keys=["ctrl", "c"])
keyboard(action="combo", keys=["ctrl", "shift", "v"])
```

**特性**：
- ✅ 完整 Unicode 支持
- ✅ 中文输入智能处理
- ✅ 输入法兼容（ibus/fcitx）

---

## 📁 File 工具（2 个）

### 13. file_read
**读取 VM 文件**
```python
file_read(path="/home/user/document.txt")
```
- 参数：`path` (必需) - 文件路径
- 返回：文件内容（Base64 编码）

### 14. file_write
**写入 VM 文件**
```python
file_write(path="/home/user/output.txt", content="Hello")
```
- 参数：
  - `path` (必需) - 文件路径
  - `content` (必需) - 文件内容（二进制用 Base64）
- 返回：写入结果

---

## 💻 Shell 工具（1 个）

### 15. shell_exec
**执行 Shell 命令**
```python
shell_exec(command="ls -la /home")
shell_exec(command="python3 script.py")
```
- 参数：`command` (必需) - Shell 命令
- 返回：
  - `stdout` - 标准输出
  - `stderr` - 错误输出
  - `exit_code` - 退出码

---

## 🪟 Window 工具（7 个）

### 16. list_windows
**列出所有桌面窗口**
```python
list_windows()
```
- 返回：窗口列表（ID、标题、桌面号）

### 17. focus_window
**聚焦窗口**
```python
focus_window(window_id="0x03400005")
focus_window(window_id="Firefox")  # 按标题
```
- 参数：`window_id` (必需) - 窗口 ID 或标题

### 18. maximize_window
**最大化窗口**
```python
maximize_window(window_id="0x03400005")
maximize_window()  # 当前聚焦窗口
```
- 参数：`window_id` (可选) - 窗口 ID

### 19. minimize_window
**最小化窗口**
```python
minimize_window(window_id="0x03400005")
minimize_window()  # 当前聚焦窗口
```
- 参数：`window_id` (可选) - 窗口 ID

### 20. close_window
**关闭窗口**
```python
close_window(window_id="0x03400005")
close_window()  # 当前聚焦窗口
```
- 参数：`window_id` (可选) - 窗口 ID

### 21. resize_window
**调整窗口大小**
```python
resize_window(width=1024, height=768)
resize_window(window_id="0x03400005", width=800, height=600)
```
- 参数：
  - `width` (必需) - 宽度（像素）
  - `height` (必需) - 高度（像素）
  - `window_id` (可选) - 窗口 ID

### 22. launch_app
**启动应用**
```python
launch_app(app_name="firefox")
launch_app(app_name="code", args=["--new-window", "/path/to/file"])
```
- 参数：
  - `app_name` (必需) - 应用名称或命令
  - `args` (可选) - 命令行参数数组

---

## 🔍 Context 工具（4 个）

### 23. system_snapshot
**系统状态快照**
```python
system_snapshot()  # 所有信息
system_snapshot(include=["memory", "cpu"])  # 指定组件
```
- 参数：`include` (可选) - 组件列表：processes/memory/disk/network/cpu
- 返回：
  - `processes` - 进程列表（按内存排序）
  - `memory` - 内存使用（`free -h`）
  - `disk` - 磁盘使用（`df -h`）
  - `network` - 网络接口（`ip addr`）
  - `cpu` - CPU 使用（`top`）

### 24. clipboard_get
**获取剪贴板内容**
```python
clipboard_get()
```
- 返回：剪贴板文本
- 依赖：xclip 或 xsel

### 25. clipboard_set
**设置剪贴板内容**
```python
clipboard_set(content="Hello World")
clipboard_set(content="你好世界")
```
- 参数：`content` (必需) - 剪贴板内容
- 依赖：xclip 或 xsel
- ✅ 命令注入防护（使用 shlex.quote）

### 26. environment_info
**环境信息**
```python
environment_info()
```
- 返回：
  - `os` - 操作系统信息（uname）
  - `distro` - 发行版信息（/etc/os-release）
  - `env` - 环境变量（PATH、HOME、USER、DISPLAY、LANG）

---

## 📸 Screenshot 工具（2 个）

### 27. screenshot
**VM 桌面截图**
```python
screenshot()  # 普通截图
screenshot(grid=True, center={"x": 600, "y": 400}, zoom_factor=2.0)  # 带网格
```
- 参数：
  - `grid` (可选) - 是否显示网格
  - `center` (可选) - 中心点坐标
  - `zoom_factor` (可选) - 缩放倍数
- 返回：
  - `data` - Base64 编码的 PNG 图片
  - `width` - 图片宽度
  - `height` - 图片高度
  - `format` - 图片格式（png）

### 28. browser_screenshot
**浏览器页面截图**
```python
browser_screenshot()
```
- 返回：当前浏览器页面的截图

---

## 🎯 核心特性

### 1. Mouse Aim 系统
- ✅ 精确定位（aim 操作）
- ✅ Aim 缓存（TTL 10分钟）
- ✅ 带网格截图
- ✅ 相对调整（delta_x、delta_y）
- ✅ 缩放支持（zoom_factor）
- ✅ 完整拖拽（down → move → up）

### 2. 中文输入支持
- ✅ 自动检测非 ASCII 字符
- ✅ 中文逐字符输入（200ms 延迟）
- ✅ 输入法兼容（ibus/fcitx）
- ✅ Unicode 完整支持

### 3. 安全性
- ✅ 命令注入防护（shlex.quote）
- ✅ 参数验证
- ✅ 错误处理
- ✅ 超时控制

### 4. 性能优化
- ✅ ASCII 文本快速 API
- ✅ 非 ASCII 降级处理
- ✅ 异步执行
- ✅ 缓存机制

---

## 📋 依赖要求

### VM 内需要安装的工具

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| `wmctrl` | 窗口管理 | `sudo apt install wmctrl` |
| `xdotool` | 鼠标/键盘/窗口 | `sudo apt install xdotool` |
| `xclip` | 剪贴板 | `sudo apt install xclip` |
| `qemu-guest-agent` | Guest Agent | `sudo apt install qemu-guest-agent` |
| `playwright` | 浏览器控制 | `pip3 install playwright && playwright install chromium` |

### 服务依赖

| 服务 | 端口 | 用途 |
|------|------|------|
| vmcontrol | 8080 | VM 控制 API |
| Gateway | 19999 | 统一网关 |
| Guest Agent | - | 虚拟机内通信 |

---

## 🔄 工作流示例

### 示例 1：浏览器自动化
```python
# 1. 导航到网页
browser_navigate(url="https://example.com/login")

# 2. 输入用户名和密码
browser_type(selector="#username", text="admin")
browser_type(selector="#password", text="password123")

# 3. 点击登录按钮
browser_click(selector=".btn-login")

# 4. 等待并截图
browser_screenshot()
```

### 示例 2：精确鼠标操作（强制 aim_id 工作流）
```python
# 步骤 1: Aim 标记目标位置（这是唯一可以用 x, y 的地方）
result = mouse(action="aim", x=800, y=600, zoom=2.0)
aim_id = result["aim_id"]  # 获取 aim_id，后续所有操作都要用它

# 步骤 2: 微调位置（可选）
mouse(action="aim", aim_id=aim_id, delta_x=-10, delta_y=5)

# 步骤 3: 执行点击（必须使用 aim_id）
mouse(action="click", aim_id=aim_id)

# 步骤 4: 其他操作（都必须使用 aim_id）
mouse(action="double", aim_id=aim_id)           # 双击
mouse(action="scroll", aim_id=aim_id, direction="down", amount=3)  # 滚动

# ❌ 错误示例：直接使用 x, y 会失败
# mouse(action="click", x=800, y=600)  # 返回错误：requires aim_id
```

### 示例 3：文件操作 + 命令执行
```python
# 1. 创建脚本文件
file_write(path="/tmp/script.sh", content="#!/bin/bash\necho 'Hello'")

# 2. 执行脚本
result = shell_exec(command="bash /tmp/script.sh")
print(result["stdout"])

# 3. 读取输出
content = file_read(path="/tmp/output.txt")
```

### 示例 4：窗口管理
```python
# 1. 列出所有窗口
windows = list_windows()

# 2. 找到目标窗口并聚焦
firefox_window = next(w for w in windows if "Firefox" in w["title"])
focus_window(window_id=firefox_window["id"])

# 3. 最大化
maximize_window(window_id=firefox_window["id"])
```

---

## 🚀 使用方式

### 在 Gateway 中使用
```python
from gateway.clients.vmuse_adapter import VmuseAdapter

adapter = VmuseAdapter()
result = await adapter.call_tool("browser_navigate", {"url": "https://example.com"}, agent_id)
```

### 工具发现（Tools Server）
```python
tools = adapter.list_tools_mcp_format()
# 返回 28 个工具的 MCP 格式定义
```

---

## 📈 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v1.0** | 2026-02-06 | 初始版本，28 个工具完整实现 |
| | | ✅ Browser 工具（10 个）|
| | | ✅ Mouse Aim 系统 |
| | | ✅ 中文输入支持 |
| | | ✅ Window 管理（7 个）|
| | | ✅ Context 工具（4 个）|

---

## 📞 联系方式

- 文件位置：`novaic-backend/gateway/clients/vmuse_adapter.py`
- 配置位置：`novaic-backend/common/config.py`
- API 文档：查看各工具的 `inputSchema` 定义

---

**注意事项**：
1. 所有工具都通过 vmcontrol API 或 Guest Agent 执行
2. Mouse aim 功能需要 vmcontrol 支持截图 API
3. 中文输入需要 VM 内安装 xdotool
4. 剪贴板操作需要 xclip 或 xsel
5. 窗口管理需要 wmctrl 和 xdotool

**当前状态**：✅ 所有 28 个工具已完整实现并测试通过
