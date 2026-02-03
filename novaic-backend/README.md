# NovAIC Backend

NovAIC AI Agent 的后端服务，基于 v2 Saga/Task 架构。

## 架构

```
novaic-backend/
├── Gateway (api/, main.py)      # REST API + DB 管理
├── MCP (mcp_gateway/, mcp_servers/)  # MCP 服务聚合
├── task_queue/                   # v2 Saga/Task 核心
│   ├── sagas/                    # Saga 定义 (ReactThink, ReactActions...)
│   ├── handlers/                 # Task handlers
│   └── business/                 # 业务逻辑层
├── services/                     # Worker 进程
│   ├── watchdog.py               # 消息监控
│   ├── task_worker_v2.py         # Task 执行
│   ├── saga_worker_v2.py         # Saga 编排
│   └── health_worker_v2.py       # 健康监控
└── db/                           # SQLite 数据库
```

## 进程架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri App                                │
│  启动和管理所有 Backend 进程                                  │
└─────────────────────────────────────────────────────────────┘
          │
          ├──► Gateway (port 19999)      # API + DB
          ├──► MCP Gateway (port 19998)  # MCP 聚合
          ├──► Watchdog                  # 消息 → Saga
          ├──► Task Worker               # 执行 Task
          ├──► Saga Worker               # 编排 Saga
          └──► Health Worker             # 超时回收
```

## 快速开始

```bash
# 开发模式
cd novaic-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动 Gateway
python main.py

# 启动 Workers (另开终端)
python message_main_v2.py   # Watchdog
python task_main_v2.py      # Task Worker
python saga_main_v2.py      # Saga Worker
python health_main_v2.py    # Health Worker
```

## 环境变量

- `NOVAIC_DATA_DIR` - 数据目录 (必需)
- `NOVAIC_HOST` - Gateway 绑定地址 (默认: 127.0.0.1)
- `NOVAIC_PORT` - Gateway 端口 (默认: 19999)
- `NOVAIC_MCP_PORT` - MCP Gateway 端口 (默认: 19998)
- `NOVAIC_GATEWAY_URL` - Worker 连接 Gateway 的 URL

## 测试

```bash
cd novaic-backend
NOVAIC_DATA_DIR=/tmp/novaic-test pytest tests/ -v
```
