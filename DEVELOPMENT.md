# NovAIC 开发指南

## 项目结构

```
novaic/
├── app/                    # Tauri 桌面应用
│   ├── src/               # React 前端
│   │   ├── components/    # UI 组件
│   │   ├── hooks/         # React Hooks
│   │   ├── services/      # API 服务
│   │   ├── store/         # 状态管理
│   │   └── types/         # TypeScript 类型
│   └── src-tauri/         # Rust 后端
│       └── src/
│           ├── commands/  # Tauri 命令
│           └── vm/        # VM 管理
├── agent/                  # AI Agent 服务
│   ├── api/               # HTTP API
│   ├── core/              # 核心逻辑
│   └── tools/             # 工具执行器
├── cloud/                  # 云服务
│   └── api/               # API 端点
├── vm/                     # 虚拟机相关
│   ├── scripts/           # 构建和管理脚本
│   ├── config/            # 配置文件
│   └── images/            # VM 镜像 (gitignored)
└── docs/                   # 文档
```

## 开发环境配置

### 前置依赖

```bash
# macOS
brew install qemu python node rust
```

### 启动开发环境

#### 1. 构建虚拟机镜像 (首次)

```bash
# 下载 Ubuntu ISO
./vm/scripts/create-ubuntu-vm.sh

# 构建基础镜像
./vm/scripts/build-image.sh

# 配置桌面环境
./vm/scripts/setup-desktop.sh

# 配置 Agent 服务
./vm/scripts/setup-agent.sh
```

#### 2. 启动虚拟机

```bash
# 前台模式 (带窗口)
./vm/scripts/start-vm.sh

# 后台模式
./vm/scripts/start-vm.sh -d

# 查看状态
./vm/scripts/status-vm.sh

# 停止
./vm/scripts/stop-vm.sh
```

#### 3. 启动各服务

**仅支持完整模式 (使用虚拟机):**

```bash
# 终端 1: 启动 VM
./vm/scripts/start-vm.sh -d

# 终端 2: 启动 Cloud 服务
cd cloud && source venv/bin/activate && python main.py

# 终端 3: 启动 websockify (如果 VM 未自动启动)
./vm/scripts/start-websockify.sh

# 终端 4: 启动桌面 App（Tauri）
cd app && npm run tauri:dev
```

## 端口映射

| 服务 | 端口 | 说明 |
|------|------|------|
| VNC Server | 5900 | 虚拟机 VNC (原生) |
| WebSocket | 6080 | websockify (noVNC 代理) |
| Agent API | 8080 | Agent HTTP API |
| Cloud API | 8000 | Cloud 服务 |
| Frontend | 1420 | Vite 开发服务器 |

## VNC 连接

前端通过 noVNC 库连接到虚拟机:

1. **websockify** 在端口 6080 监听 WebSocket 连接
2. **websockify** 将 WebSocket 转发到 VNC 端口 5900
3. **noVNC (RFB)** 通过 WebSocket 显示 VNC 画面

```
Frontend (noVNC) --[WebSocket]--> websockify:6080 --[TCP]--> VNC:5900
```

## 架构流程

```
用户
  │
  ▼
┌──────────────────┐
│   NovAIC.app      │  ← Tauri 桌面应用
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
│   虚拟机 (QEMU)   │
│  ┌────────────┐  │
│  │ Agent API  │  │  ← Python FastAPI
│  └────────────┘  │
│  ┌────────────┐  │
│  │ VNC Server │  │  ← TigerVNC + XFCE
│  └────────────┘  │
└──────────────────┘
        │
        ▼ HTTPS
┌──────────────────┐
│   Cloud Service  │
│  ├── 用户认证    │
│  ├── 订阅管理    │
│  └── LLM 代理    │  ← 转发到 Claude/GPT API
└──────────────────┘
```

## 常见问题

### VNC 连不上

1. 检查 VM 是否运行: `./vm/scripts/status-vm.sh`
2. 检查 websockify 是否运行: `lsof -i :6080`
3. 检查 VNC 服务: `lsof -i :5900`

### Agent API 无响应

1. 检查 Agent 日志: `curl http://localhost:8080/api/health`
2. 进入 VM 检查: `ssh -p 2222 user@localhost`

### 开发模式 vs 生产模式

NovAIC 仅支持 **完整模式**：Agent 在 VM 内运行，更安全隔离。

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

## 版本信息

- **Node.js**: 20.x
- **Python**: 3.11+
- **Rust**: 1.70+
- **QEMU**: 8.x
