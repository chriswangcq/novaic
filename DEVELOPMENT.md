# NovAIC 开发指南

本文档介绍如何搭建本地开发环境。

## 项目结构

```
nb-cc/
├── │   ├── novaic-core/          # MCP 工具服务器 (Python)
│   │   └── src/novaic_core/
│   │       ├── tools/        # 工具实现
│   │       │   ├── desktop.py    # 桌面控制 (screenshot, mouse, keyboard)
│   │       │   ├── browser.py    # 浏览器自动化
│   │       │   ├── shell.py      # Shell 执行
│   │       │   ├── files.py      # 文件操作
│   │       │   ├── windows.py    # 窗口管理
│   │       │   ├── memory.py     # 记忆系统
│   │       │   └── context.py    # 环境感知
│   │       ├── main.py       # MCP Server 入口
│   │       └── cli.py        # CLI 命令
│   │
│   ├── novaic-app/           # 桌面客户端 (Tauri + React)
│   │   ├── src/              # React 前端
│   │   │   ├── components/   # UI 组件
│   │   │   ├── hooks/        # React Hooks
│   │   │   ├── services/     # API 服务
│   │   │   └── store/        # 状态管理 (Zustand)
│   │   └── src-tauri/        # Rust 后端
│   │       └── src/
│   │           ├── commands/ # Tauri 命令
│   │           └── vm/       # VM 管理
│   │
│   └── novaic-vm/            # VM 管理 + MCP 工具服务
│       ├── src/novaic_mcp_vmuse/
│       │   └── tools/        # browser, desktop, shell...
│       └── scripts/
│           ├── create-vm.sh  # 创建 VM
│           ├── start-vm.sh   # 启动 VM
│           ├── stop-vm.sh    # 停止 VM
│           └── deploy.sh     # 部署 MCP Server
│
├── docs/                     # 文档
└── paper/                    # 案例研究
```

## 开发环境配置

### 前置依赖

**macOS:**

```bash
# 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install python@3.11 node@20 rust qemu
```

**Python 版本:** 3.11+
**Node.js 版本:** 20+
**Rust 版本:** 1.70+
**QEMU 版本:** 8.x+

### 启动开发环境

#### 1. 启动虚拟机

```bash
cd novaic-vm

# 首次运行：创建 VM
./setup.sh

# 后续启动
./scripts/start-vm.sh      # 前台模式（带窗口）
./scripts/start-vm.sh -d   # 后台模式

# 查看状态
./scripts/status-vm.sh

# 停止
./scripts/stop-vm.sh
```

#### 2. 部署 MCP Server

```bash
cd novaic-vm
./scripts/deploy.sh
```

#### 3. 启动各服务

**完整模式（推荐）**

```bash
# 终端 1: 启动 Gateway 后端
cd novaic-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 启动所有服务
python main.py &                                           # Gateway (19999)
python mcp_main.py &                                       # MCP Gateway (19997)
python launcher_main.py --gateway-url http://127.0.0.1:19999 --bootstrap &
python collector_main.py --gateway-url http://127.0.0.1:19999 &
python async_main.py --gateway-url http://127.0.0.1:19999 &

# 终端 2: 启动桌面 App（Tauri）
cd novaic-app
npm install
npm run tauri:dev

# 终端 3: (可选) 启动 VM
cd novaic-vm && ./scripts/start-vm.sh -d
```

**使用开发脚本**

```bash
# 一键启动所有后端服务
./dev-guide/run-dev.sh

# 或分步启动
./dev-guide/run-dev.sh gateway
./dev-guide/run-dev.sh mcp-gateway
./dev-guide/run-dev.sh launcher
./dev-guide/run-dev.sh collector
./dev-guide/run-dev.sh async
```

## 端口映射

| 服务 | 端口 | 说明 |
|------|------|------|
| VNC Server | 5900 | 虚拟机桌面 |
| SSH | 2222 | VM SSH 访问 |
| MCP Server | 8080 | MCP 工具服务 |
| Agent API | 8080 | Agent HTTP API |
| Cloud API | 8000 | 云服务 API |
| Frontend | 1420 | Vite 开发服务器 |

## VNC 连接

**方式 1：直接连接**
```
vnc://localhost:5900
密码: novaic
```

**方式 2：通过 noVNC（App 内置）**

前端通过 noVNC 库连接到虚拟机:
```
Frontend (noVNC) --[WebSocket]--> websockify:6080 --[TCP]--> VNC:5900
```

## SSH 访问

```bash
ssh -p 2222 ubuntu@localhost
# 密码: ubuntu
```

## 架构流程

```
用户
  │
  ▼
┌──────────────────┐
│   NovAIC.app     │  ← Tauri 桌面应用
│  ┌────────────┐  │
│  │  React UI  │  │  ← 聊天界面 + VNC 画面
│  └────────────┘  │
│  ┌────────────┐  │
│  │   Rust     │  │  ← VM 管理、文件传输
│  └────────────┘  │
└──────────────────┘
        │
        ▼ HTTP/WebSocket
┌──────────────────┐
│   虚拟机 (QEMU)  │
│  ┌────────────┐  │
│  │ MCP Server │  │  ← novaic-core (44+ 工具)
│  └────────────┘  │
│  ┌────────────┐  │
│  │ VNC Server │  │  ← x11vnc + XFCE
│  └────────────┘  │
└──────────────────┘
        │
        ▼ HTTPS (可选)
┌──────────────────┐
│   Cloud Service  │
│  ├── 用户认证    │
│  ├── 订阅管理    │
│  └── LLM 代理    │  ← 转发到 Claude/GPT API
└──────────────────┘
```

## 常见问题

### VNC 连不上

```bash
# 1. 检查 VM 是否运行
cd novaic-vm
./scripts/status-vm.sh

# 2. 检查 VNC 服务
ssh -p 2222 ubuntu@localhost
sudo systemctl status x11vnc
sudo systemctl restart x11vnc
```

### MCP Server 无响应

```bash
# 1. 检查服务状态
curl http://localhost:8080/health

# 2. 进入 VM 检查
ssh -p 2222 ubuntu@localhost
sudo systemctl status novaic
sudo journalctl -u novaic -f

# 3. 重新部署
cd novaic-vm
./scripts/deploy.sh
```

### Agent API 无响应

```bash
# 检查日志
curl http://localhost:8080/api/health

# 确保 VM 已启动并且 MCP Server 正常
```

## 测试 MCP Server

```bash
# 健康检查
curl http://localhost:8080/health

# 获取工具列表
curl http://localhost:8080/tools

# 测试截图
curl -X POST http://localhost:8080/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "screenshot", "arguments": {}}'
```

## 测试 LLM 代理

```bash
# 登录获取 token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# 测试 LLM 调用
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

## 代码风格

### Python

```bash
# 格式化
black .
isort .

# 类型检查
mypy .
```

### TypeScript

```bash
cd novaic-app

# 格式化
npm run format

# 检查
npm run lint
```

### Rust

```bash
cd novaic-app/src-tauri

# 格式化
cargo fmt

# 检查
cargo clippy
```

## 版本信息

- **Node.js**: 20.x
- **Python**: 3.11+
- **Rust**: 1.70+
- **QEMU**: 8.x
- **Ubuntu VM**: 24.04 LTS
