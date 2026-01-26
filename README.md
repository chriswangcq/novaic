# NovAIC - The AI Computer

> PC 是给人用的电脑，AIC 是给 AI 用的电脑。
> 
> NovAIC 是你的 AI 专属电脑 —— 它记得你、理解你、为你持续工作。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## ✨ 特性

- 🖥️ **完整桌面控制** - 44+ MCP 工具，操作任何 Linux GUI 应用
- 🧠 **持久化记忆** - AI 记得上下文，跨会话保持状态
- 👁️ **环境感知** - 智能理解系统状态和项目结构
- 📦 **结果管理** - 长结果自动截断，分段查询
- 🔒 **隐私优先** - 本地部署，数据不出本机
- 🔓 **开源自由** - MIT 协议，完全可定制

## 🚀 快速开始

```bash
# 安装
pip install novaic

# 启动 VM
cd runtime && ./scripts/start-ubuntu-vm.sh

# 启动 MCP Server
novaic serve
```

## 📖 文档

- [快速开始](docs/getting-started.md)
- [架构设计](docs/architecture.md)
- [API 参考](docs/api-reference.md)
- [产品愿景](docs/novaic-vision.md)
- [重命名指南](docs/novaic-rename-guide.md)
- [产品路线图](docs/novaic-roadmap.md)

## 🎬 演示

AI 通过 NovAIC 发送微信消息：

```
User: 帮我给公主发个消息 "hi --from ai"

NovAIC: 
1. 启动微信应用
2. 搜索联系人 "公主"
3. 输入消息 "hi --from ai"
4. 发送成功 ✅
```

## 📦 组件

| 组件 | 说明 | 路径 |
|------|------|------|
| **novaic-core** | MCP 工具服务器 (44+ 工具) | `packages/novaic-core` |
| **novaic-agent** | AI 智能体框架 | `packages/novaic-agent` |
| **novaic-app** | 桌面客户端 (Tauri) | `packages/novaic-app` |
| **novaic-cloud** | 云服务 | `packages/novaic-cloud` |
| **runtime** | QEMU VM 运行时 | `runtime` |

## 🛠️ MCP 工具列表

### 桌面控制
- `screenshot` - 截取屏幕
- `mouse` - 鼠标操作 (移动、点击、拖拽、滚动)
- `keyboard` - 键盘输入

### 浏览器自动化
- `browser_navigate` - 导航到 URL
- `browser_click` - 点击元素
- `browser_type` - 输入文本
- `browser_screenshot` - 浏览器截图

### Shell 执行
- `run_command` - 执行 Shell 命令
- `run_python` - 执行 Python 代码

### 文件操作
- `read_file` - 读取文件
- `write_file` - 写入文件
- `list_files` - 列出目录

### 窗口管理
- `list_windows` - 列出窗口
- `focus_window` - 聚焦窗口
- `launch_app` - 启动应用

### 记忆系统
- `memory_save` - 保存记忆
- `memory_recall` - 回忆记忆
- `goal_set` - 设置目标
- `session_state` - 会话状态

### 环境感知
- `system_snapshot` - 系统快照
- `directory_snapshot` - 目录分析
- `app_state` - 应用状态

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    NovAIC Platform                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │NovAIC App   │  │ NovAIC Web  │  │ NovAIC CLI  │         │
│  │  (Tauri)    │  │  (React)    │  │  (Python)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  NovAIC Core                         │   │
│  │              MCP Server (44+ Tools)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 NovAIC Runtime                       │   │
│  │  Ubuntu 24.04 VM (QEMU) + XFCE + VNC + SSH          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 配置 Cursor/Claude Desktop

在 `~/.cursor/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "novaic": {
      "url": "http://localhost:8081/sse"
    }
  }
}
```

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

**NovAIC** - The AI Computer | [GitHub](https://github.com/novaic/novaic) | [Docs](https://docs.novaic.dev)
