# NovAIC 打包流程文档

## 架构概述

NovAIC 使用 Tauri 框架打包，包含以下组件：

```
NovAIC.app
├── MacOS/
│   └── novaic                    # Tauri 主程序 (Rust)
└── Resources/
    ├── novaic-backend/           # Python Backend (PyInstaller)
    │   ├── novaic-backend        # 统一入口二进制
    │   └── _internal/            # Python 运行时和依赖
    └── novaic-mcp-vmuse/         # VM 端 MCP Server (Python 源码)
```

## 打包流程

执行 `./build.sh` 完成完整打包：

### Step 1: 构建 Python Backend

```bash
cd novaic-backend
pyinstaller --clean --noconfirm novaic-backend.spec
```

输出: `dist/novaic-backend/`

### Step 2: 复制资源到 Tauri

```bash
cp -r novaic-backend/dist/novaic-backend novaic-app/src-tauri/resources/
cp -r novaic-vm/src novaic-app/src-tauri/resources/novaic-mcp-vmuse/
```

### Step 3: 构建 Tauri App

```bash
cd novaic-app
npm run tauri build
```

输出: `src-tauri/target/release/bundle/dmg/*.dmg`

---

## Backend 组件架构 (v4.0 Saga/Task)

| 组件 | 命令 | 端口 | 职责 |
|------|------|------|------|
| Gateway | `gateway` | 19999 | API + DB + SSE |
| MCP Gateway | `mcp-gateway` | 19998 | MCP 聚合 |
| Watchdog | `watchdog` | - | 监控消息，触发 Saga |
| Task Worker | `task-worker` | - | 执行任务 |
| Saga Worker | `saga-worker` | - | 编排工作流 |
| Health | `health` | - | 超时回收 |

### 启动命令

```bash
# 生产模式 (PyInstaller 打包后)
./novaic-backend gateway --port 19999 --data-dir /path/to/data
./novaic-backend mcp-gateway --port 19998 --data-dir /path/to/data
./novaic-backend watchdog --gateway-url http://127.0.0.1:19999
./novaic-backend task-worker --gateway-url http://127.0.0.1:19999
./novaic-backend saga-worker --gateway-url http://127.0.0.1:19999
./novaic-backend health --gateway-url http://127.0.0.1:19999

# 开发模式 (直接 Python)
python main_novaic.py gateway --port 19999 --data-dir /path/to/data
# 或直接运行入口文件
python main_gateway.py
python main_mcp.py
python main_watchdog.py
python main_task.py
python main_saga.py
python main_health.py
```

---

## PyInstaller Spec 配置

关键配置 (`novaic-backend.spec`):

```python
# 入口点
Analysis(['main_novaic.py'], ...)

# 打包的模块和文件
datas=[
    ('gateway', 'gateway'),           # Gateway 包
    ('mcp_gateway', 'mcp_gateway'),   # MCP Gateway 包
    ('task_queue', 'task_queue'),     # Task Queue 包
    ('main_gateway.py', '.'),         # 入口文件
    ('main_mcp.py', '.'),
    ('main_watchdog.py', '.'),
    ('main_task.py', '.'),
    ('main_saga.py', '.'),
    ('main_health.py', '.'),
]
```

---

## Tauri 进程管理

Tauri (`main.rs`) 负责启动和管理所有 Backend 进程：

1. **启动顺序**:
   - Gateway (等待 health check)
   - MCP Gateway
   - Watchdog
   - Task Worker
   - Saga Worker
   - Health

2. **关闭顺序** (反向):
   - Health
   - Saga Worker
   - Task Worker
   - Watchdog
   - MCP Gateway
   - Gateway (停止所有 VM)

---

## 开发调试

### 手动启动服务

```bash
cd novaic-backend

# 只启动 Gateway + MCP Gateway
./run_gateways.sh

# 启动全部 6 个服务
./run_gateways.sh --all
```

### 日志位置

| 服务 | 日志文件 |
|------|----------|
| Gateway | `/tmp/gateway.log` |
| MCP Gateway | `/tmp/mcp_gateway.log` |
| Watchdog | `/tmp/watchdog.log` |
| Task Worker | `/tmp/task_worker.log` |
| Saga Worker | `/tmp/saga_worker.log` |
| Health | `/tmp/health_worker.log` |

### 运行测试

```bash
cd novaic-backend
python -m pytest tests/ -v
```

---

## 常见问题

### 1. PyInstaller 找不到模块

检查 `novaic-backend.spec` 中的 `datas` 和 `hiddenimports`。

### 2. Tauri 启动服务失败

检查 `main.rs` 中的命令名称是否与 `main_novaic.py` 一致。

### 3. 服务间通信失败

确保环境变量正确：
- `NOVAIC_DATA_DIR`: 数据目录
- `NOVAIC_GATEWAY_URL`: Gateway URL (默认 http://127.0.0.1:19999)
- `NOVAIC_MCP_GATEWAY_URL`: MCP Gateway URL (默认 http://127.0.0.1:19998)
