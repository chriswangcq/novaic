# MCP-VMUSE VM 内桌面控制

## 概述与职责

MCP-VMUSE 是一个运行在 **VM 内部**（Linux 客户机）的 Python 服务包（v0.2.0），为宿主平台提供对虚拟机桌面环境的完整控制能力。它通过 HTTP JSON API 暴露 6 大类共 40+ 个工具端点，涵盖截屏、鼠标/键盘操作、浏览器自动化、Shell 命令执行、文件传输和窗口管理。

外部系统（VmControl）通过 HTTP 或 Virtio-Serial 通道与 MCP-VMUSE 通信，LLM Agent 则通过工具调用间接驱动虚拟机内的操作。

```
┌─────────────────────────────────────────────────┐
│                  宿主 (Host)                     │
│                                                  │
│  ┌──────────┐    HTTP/Virtio    ┌─────────────┐ │
│  │VmControl │ ◄──────────────► │    VM        │ │
│  │ (代理)    │    Serial        │ ┌─────────┐ │ │
│  └──────────┘                   │ │MCP-VMUSE│ │ │
│       ▲                         │ │ :8080   │ │ │
│       │                         │ └─────────┘ │ │
│  ┌────┴─────┐                   │   Linux     │ │
│  │ Runtime  │                   │   Guest     │ │
│  │ (Agent)  │                   └─────────────┘ │
│  └──────────┘                                    │
└─────────────────────────────────────────────────┘
```

## 服务架构

MCP-VMUSE 使用 aiohttp 构建异步 HTTP JSON 服务器，监听 `0.0.0.0:8080`。

**技术细节：**

| 配置项 | 值 |
|-------|-----|
| 框架 | aiohttp（Python 异步 HTTP） |
| 监听地址 | 0.0.0.0:8080 |
| 协议 | HTTP JSON（RESTful 风格） |
| 备用传输 | Virtio-Serial 代理 |
| 运行环境 | Linux 虚拟机内部 |
| 包版本 | v0.2.0 |

**请求/响应格式：**

所有端点接收 JSON 请求体，返回 JSON 响应。二进制数据（如截屏图片、文件内容）使用 Base64 编码传输。

**Virtio-Serial 代理** 作为备用传输通道，在 HTTP 不可用的场景下（如网络未就绪），通过 virtio-serial 设备实现宿主与客户机之间的通信。

## 工具清单

MCP-VMUSE 提供 6 大工具类别，共 40+ 个 API 端点：

### 1. Desktop（桌面控制）

负责截屏和基础输入设备控制。

| 端点 | 工具 | 说明 |
|-----|------|------|
| screenshot | scrot / import | 全屏或区域截屏，返回 Base64 图片 |
| mouse | AimClick 网格 | 两阶段鼠标操作：Aim（瞄准）→ Execute（执行） |
| keyboard | xdotool | 键盘按键、组合键、文本输入 |

**鼠标操作的两阶段模型（Aim-Execute）：**

```
阶段 1: Aim（瞄准）
  → 在屏幕上叠加 AimClick 网格
  → 返回带网格标注的截屏
  → LLM 根据网格坐标确定目标位置

阶段 2: Execute（执行）
  → 根据坐标执行点击/拖拽/双击等操作
  → 返回操作后的截屏确认结果
```

### 2. Browser（浏览器自动化）

基于 Playwright Chromium 的浏览器控制，共 **9 个端点**。

| 端点 | 说明 |
|-----|------|
| navigate | 导航到指定 URL |
| click | 点击页面元素（坐标或选择器） |
| type | 在输入框中输入文本 |
| screenshot | 页面截屏 |
| scroll | 页面滚动 |
| eval | 执行 JavaScript 代码 |
| tabs | 标签页管理（列出/切换/新建/关闭） |
| get_text | 提取页面文本内容 |
| get_html | 获取页面 HTML |

### 3. Shell（命令执行）

| 端点 | 说明 |
|-----|------|
| run_command | 执行 Shell 命令 |

**执行约束：**

- 超时限制：**30 秒**
- 输出截断：超长输出自动截断，防止响应体过大
- 用户隔离：通过 `sudo -u vm_user` 切换到受限用户执行，避免 root 权限滥用

### 4. File（文件操作）

| 端点 | 说明 |
|-----|------|
| pull | 从 VM 拉取文件到宿主 |
| push | 从宿主推送文件到 VM |

- 自动检测二进制文件，选择合适的编码方式传输
- 支持文本和二进制两种文件类型

### 5. Window（窗口管理）

基于 wmctrl 的窗口控制，共 **7 个端点**。

| 端点 | 说明 |
|-----|------|
| list | 列出所有窗口 |
| focus | 聚焦指定窗口 |
| maximize | 最大化窗口 |
| minimize | 最小化窗口 |
| close | 关闭窗口 |
| resize | 调整窗口大小/位置 |
| launch | 启动新应用程序 |

### 6. Context（上下文感知）

提供 VM 环境的全局状态信息，共 **7 个端点**。

| 端点 | 说明 |
|-----|------|
| system_snapshot | 系统整体状态快照（CPU/内存/磁盘等） |
| directory_snapshot | 指定目录的文件列表 |
| app_state | 当前前台应用状态 |
| clipboard | 剪贴板内容 |
| recent_files | 最近访问的文件列表 |
| environment | 环境变量信息 |
| display_info | 显示器分辨率和配置 |

## 配置

MCP-VMUSE 在 VM 内以系统服务形式运行，主要配置项：

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| HOST | 0.0.0.0 | 监听地址 |
| PORT | 8080 | 监听端口 |
| DISPLAY | :0 | X11 显示器编号 |
| VM_USER | vm_user | Shell 命令执行用户 |
| COMMAND_TIMEOUT | 30 | Shell 命令超时（秒） |

## 与 VmControl 的集成

外部系统不直接访问 MCP-VMUSE，而是通过 VmControl 服务进行代理。

**调用链路：**

```
LLM Agent
    │  工具调用: computer_use(action="screenshot")
    ▼
Runtime
    │  解析工具调用，路由到 VmControl
    ▼
VmControl
    │  HTTP: POST /api/vms/:id/vmuse/:tool/:operation
    │  示例: POST /api/vms/abc123/vmuse/desktop/screenshot
    ▼
MCP-VMUSE (VM 内部 :8080)
    │  执行操作，返回结果
    ▼
VmControl
    │  透传响应
    ▼
Runtime → LLM Agent
```

**URL 映射规则：**

VmControl 的路由 `/api/vms/:id/vmuse/:tool/:operation` 中：
- `:id` — 目标虚拟机的唯一标识
- `:tool` — 工具类别（desktop / browser / shell / file / window / context）
- `:operation` — 具体操作（screenshot / navigate / run_command 等）

VmControl 根据 VM ID 查找对应的虚拟机网络地址，将请求转发到该 VM 内部的 MCP-VMUSE 服务。这层代理屏蔽了 VM 内部网络细节，并提供统一的鉴权和访问控制。
