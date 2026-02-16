# NovAIC Backend

NovAIC AI Agent 的后端服务，基于 v2 Saga/Task 架构。

## 架构

```
novaic-backend/
├── Gateway (api/, main.py)      # REST API + DB 管理
├── MCP (mcp_client/, mcp_servers/)  # MCP 服务聚合
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
          ├──► Runtime Orchestrator (port 19993)  # 内部 API，需先启动
          ├──► Gateway (port 19999)               # API + DB（依赖 RO 健康）
          ├──► MCP Gateway (port 19998)           # MCP 聚合
          ├──► Watchdog                           # 消息 → Saga
          ├──► Task Worker                        # 执行 Task
          ├──► Saga Worker                        # 编排 Saga
          └──► Health Worker                      # 超时回收
```

**Strict dependency:** Gateway requires Runtime Orchestrator to be healthy at startup; no fallback.

## 快速开始

```bash
# 开发模式
cd novaic-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 1. 启动 Runtime Orchestrator（必须先启动）
python main_novaic.py runtime-orchestrator

# 2. 启动 Gateway（另开终端）
python main_novaic.py gateway

# 3. 启动 Workers（另开终端）
python main_novaic.py watchdog
python main_novaic.py task-worker
python main_novaic.py saga-worker
python main_novaic.py health
```

## 配置

运行时配置不再从环境变量读取。统一使用单一配置文件：

- `config/services.json`

关键项包括：

- `paths.data_dir` - 数据目录（必填）
- `services.*.host/port/url` - 各服务网络配置
- `timeouts.*`、`worker.*` - 超时与并发参数

## 测试

```bash
cd novaic-backend
pytest tests/ -v
```

进程级严格启动契约：

```bash
pytest -q tests/contract/test_runtime_orchestrator_process_startup.py
```

一键运行严格链路验收（自动处理本地代理环境）：

```bash
bash scripts/run_strict_runtime_orchestrator_contracts.sh
```

一键严格启动（先 Runtime Orchestrator，再 Gateway）：

```bash
bash scripts/start_strict_runtime_stack.sh /path/to/data [RO_PORT] [GW_PORT]
```

停止严格链路（Gateway + Runtime Orchestrator）：

```bash
bash scripts/stop_strict_runtime_stack.sh /path/to/data
```
