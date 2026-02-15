# Novaic 服务启动指南

本文档记录了各个服务的启动方法和注意事项，基于实际运行经验总结。

## 项目架构概览

```
novaic/
├── novaic-app/              # Tauri 前端应用 (React + TypeScript)
├── novaic-backend/          # Python 后端服务 (FastAPI)
├── novaic-app/src-tauri/vmcontrol/  # Rust VM 控制服务
├── novaic-mcp-vmuse/        # MCP 服务器 (Python)
└── build.sh                 # 统一构建脚本
```

## 端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| Gateway | 19999 | 核心 API + SSE 事件推送 |
| Tools Server | 19998 | 工具执行 HTTP API |
| Queue Service | 19997 | Task/Saga 队列管理 |
| VMControl | 19996 | VM 控制 + VNC WebSocket |

---

## 一、前端应用 (novaic-app)

### 技术栈
- React 18 + TypeScript
- Tauri 2.x (桌面应用框架)
- Vite (构建工具)
- Zustand (状态管理)

### 启动步骤

```bash
cd novaic-app

# 1. 安装依赖
npm install

# 2. 开发模式（仅前端）
npm run dev

# 3. Tauri 开发模式（前端 + 桌面应用）
npm run tauri:dev

# 4. 构建生产版本
npm run tauri:build
```

### 常见问题

1. **依赖安装失败**: 确保 Node.js 版本 >= 18
2. **Tauri 启动失败**: 需要先安装 Rust 和 Tauri CLI
   ```bash
   cargo install tauri-cli
   ```

---

## 二、后端服务 (novaic-backend)

后端是一个统一的 Python 应用，包含多个子服务。

### 技术栈
- Python 3.13
- FastAPI
- SQLite (数据库)
- PyInstaller (打包)

### 环境准备

```bash
cd novaic-backend

# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt
```

### 服务启动顺序（重要！）

后端服务有依赖关系，必须按以下顺序启动：

```
1. Gateway (核心) - 端口 19999
   ↓
2. Queue Service (队列) - 端口 19997
   ↓
3. Tools Server (工具) - 端口 19998
   ↓
4. File Service (文件) - 端口 19995
   ↓
5. Tool Result Service (TRS) - 端口 19994
   ↓
6. Watchdog (监控) - 1个
   ↓
7. Task Workers (执行任务) - 3个
   ↓
8. Saga Workers (编排) - 3个
   ↓
9. Health Worker (健康检查) - 1个
   ↓
10. Scheduler (定时任务) - 1个
```

### 各服务启动命令

#### 2.1 Gateway (端口 19999)

核心服务，提供 REST API 和数据库管理。

```bash
# 开发模式
python -m novaic_main gateway --port 19999 --data-dir ./data

# 或直接运行
python main_gateway.py
```

**验证启动**:
```bash
curl http://127.0.0.1:19999/health
```

#### 2.2 Queue Service (端口 19997)

管理任务队列和 Saga 队列。

```bash
python -m novaic_main queue-service --port 19997 --data-dir ./data
```

**验证启动**:
```bash
curl http://127.0.0.1:19997/health
```

#### 2.3 Tools Server (端口 19998)

执行各种工具调用。

```bash
python -m novaic_main tools-server --port 19998 --data-dir ./data --gateway-url http://127.0.0.1:19999
```

#### 2.4 File Service (端口 19995)

文件管理服务，存储和检索文件（图片、文档等）。

```bash
python -m novaic_main file-service --port 19995 --data-dir ./data
```

**验证启动**:
```bash
curl http://127.0.0.1:19995/api/health
```

#### 2.5 Tool Result Service (端口 19994)

工具结果规范化服务（TRS），处理和存储工具执行结果。

```bash
python -m novaic_main tool-result-service --port 19994 --data-dir ./data
```

**验证启动**:
```bash
curl http://127.0.0.1:19994/api/health
```

#### 2.6 Watchdog

监控新消息，触发处理流程。

```bash
python -m novaic_main watchdog --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997
```

#### 2.7 Task Worker (可启动多个)

执行具体任务。

```bash
# 启动 3 个 worker
python -m novaic_main task-worker --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997
```

#### 2.8 Saga Worker (可启动多个)

处理 Saga 编排流程。

```bash
python -m novaic_main saga-worker --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997
```

#### 2.9 Health Worker

监控并回收超时的任务和 Saga。

```bash
python -m novaic_main health --queue-service-url http://127.0.0.1:19997
```

#### 2.10 Scheduler

定时唤醒 sleeping agents。

```bash
python -m novaic_main scheduler --gateway-url http://127.0.0.1:19999
```

### 一键启动脚本

```bash
cd novaic-backend
./start_all_services.sh
```

### 常见问题

1. **端口被占用**: 检查是否有残留进程
   ```bash
   lsof -i :19999
   lsof -i :19998
   lsof -i :19997
   ```

2. **数据库锁定**: SQLite 并发写入问题，确保只有一个 Gateway 实例

3. **依赖缺失**: 确保安装了所有依赖
   ```bash
   pip install -r requirements.txt
   ```

---

## 三、VM 控制服务 (vmcontrol)

### 技术栈
- Rust
- Actix-web

### 启动步骤

```bash
cd novaic-app/src-tauri/vmcontrol

# 1. 构建
cargo build --release

# 2. 运行
./target/release/vmcontrol --port 19996 --host 127.0.0.1
```

### 功能
- QMP (QEMU Machine Protocol) 通信
- Guest Agent 管理
- VNC WebSocket 代理
- Android scrcpy 支持

---

## 四、MCP 服务器 (novaic-mcp-vmuse)

### 启动步骤

```bash
cd novaic-mcp-vmuse

# 安装依赖（如有 requirements.txt）
pip install -r requirements.txt

# 运行
python -m novaic_mcp_vmuse.main
```

---

## 五、完整开发环境启动流程

### 方式一：分别启动各服务（推荐调试时使用）

打开多个终端窗口：

**终端 1 - Gateway**:
```bash
cd novaic-backend
source venv/bin/activate
python main_gateway.py
```

**终端 2 - Queue Service**:
```bash
cd novaic-backend
source venv/bin/activate
python -m novaic_main queue-service --port 19997 --data-dir ./data
```

**终端 3 - Tools Server**:
```bash
cd novaic-backend
source venv/bin/activate
python -m novaic_main tools-server --port 19998 --data-dir ./data --gateway-url http://127.0.0.1:19999
```

**终端 4 - Workers**:
```bash
cd novaic-backend
source venv/bin/activate
python -m novaic_main watchdog --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997 &
python -m novaic_main task-worker --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997 &
python -m novaic_main saga-worker --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997 &
```

**终端 5 - 前端**:
```bash
cd novaic-app
npm run dev
```

### 方式二：使用 Tauri 开发模式

Tauri 会自动管理后端服务的启动：

```bash
cd novaic-app
npm run tauri:dev
```

---

## 六、生产环境构建

### 完整构建

```bash
./build.sh
```

构建流程：
1. PyInstaller 打包 Python 后端为单一二进制
2. Cargo 构建 vmcontrol
3. 打包 QEMU 及依赖
4. Tauri 构建桌面应用

### 输出
- macOS: DMG 安装包
- 位置: `novaic-app/src-tauri/target/release/bundle/`

---

## 七、数据目录结构

```
$NOVAIC_DATA_DIR/
├── novaic.db          # Gateway 数据库
├── queue.db           # Queue Service 数据库
├── logs/              # 日志文件
└── vms/               # 虚拟机文件
```

---

## 八、调试技巧

### 查看日志

```bash
# Gateway 日志
tail -f $NOVAIC_DATA_DIR/logs/gateway.log

# 查看所有服务日志
tail -f $NOVAIC_DATA_DIR/logs/*.log
```

### 检查服务状态

```bash
# Gateway
curl http://127.0.0.1:19999/health

# Queue Service
curl http://127.0.0.1:19997/health

# Tools Server
curl http://127.0.0.1:19998/health
```

### 清理环境

```bash
# 停止所有 Python 进程
pkill -f novaic

# 清理端口
lsof -ti :19999 | xargs kill -9
lsof -ti :19998 | xargs kill -9
lsof -ti :19997 | xargs kill -9
```

---

## 九、常见错误及解决方案

### 1. "Address already in use"

```bash
# 查找占用端口的进程
lsof -i :19999
# 杀死进程
kill -9 <PID>
```

### 2. "ModuleNotFoundError"

```bash
# 确保在虚拟环境中
source venv/bin/activate
pip install -r requirements.txt
```

### 3. "Connection refused"

检查服务启动顺序，Gateway 必须先启动。

### 4. "Database is locked"

SQLite 并发问题，确保没有多个 Gateway 实例运行。

### 5. Tauri 构建失败

```bash
# 更新 Rust
rustup update

# 重新安装 Tauri CLI
cargo install tauri-cli --force
```

---

## 十、环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| NOVAIC_DATA_DIR | 数据目录 | `./data` |
| NOVAIC_LOG_LEVEL | 日志级别 | `INFO` |
| GATEWAY_PORT | Gateway 端口 | `19999` |
| TOOLS_PORT | Tools Server 端口 | `19998` |
| QUEUE_PORT | Queue Service 端口 | `19997` |

---

*最后更新: 2026-02-13*
