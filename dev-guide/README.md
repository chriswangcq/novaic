# NovAIC 开发指南

本目录包含 NovAIC 项目的开发文档和工具。

## 文档结构

| 文件 | 内容 |
|------|------|
| [architecture.md](./architecture.md) | 系统架构总览 (v17 Three-Task) |
| [services-architecture.md](./services-architecture.md) | Services 详细设计 |
| [state-machines.md](./state-machines.md) | 状态机文档 (SubAgent/Runtime/Task) |
| [debugging-dev.md](./debugging-dev.md) | **开发调试指南 (API 测试，无 Web UI)** |
| [debugging-mcp.md](./debugging-mcp.md) | MCP 调试技巧 |
| [troubleshooting.md](./troubleshooting.md) | 常见问题排查 |
| [case-study-agent-id-mismatch.md](./case-study-agent-id-mismatch.md) | Case Study: agent_id 问题 |
| [run-dev.sh](./run-dev.sh) | 开发环境启动脚本 |

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/novaic/novaic.git
cd novaic

# 安装 Gateway 依赖
cd novaic-gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 安装 Tauri 前端依赖
cd novaic-app
npm install
cd ..
```

### 2. 启动开发环境

```bash
# 方式 1: 使用脚本启动后端
./dev-guide/run-dev.sh

# 方式 2: 分步启动
./dev-guide/run-dev.sh gateway      # Gateway (19999)
./dev-guide/run-dev.sh mcp-gateway  # MCP Gateway (19998)
./dev-guide/run-dev.sh monitor      # Monitor Service (消息监听)
./dev-guide/run-dev.sh launcher     # Launcher Service
./dev-guide/run-dev.sh collector    # Collector Service
./dev-guide/run-dev.sh executor     # Executor Service (LLM/MCP)
./dev-guide/run-dev.sh health       # Health Service

# 方式 3: Tauri 开发模式 (自动启动所有后端)
cd novaic-app
npm run tauri dev
```

### 3. 验证服务状态

```bash
# Gateway 健康检查
curl http://127.0.0.1:19999/api/health

# MCP Gateway 健康检查
curl http://127.0.0.1:19998/api/health

# 查看 pipeline tasks
curl http://127.0.0.1:19999/internal/pipeline-tasks
```

## 架构概览

v17 采用 Three-Task Architecture：

```
┌─────────────────────────────────────────────────────────┐
│                    Tauri App                             │
│  (进程管理 + 前端 UI)                                     │
└─────────────────────────────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌─────────┐       ┌─────────────┐       ┌─────────────┐
│ Gateway │       │ MCP Gateway │       │  Services   │
│ (19999) │       │   (19998)   │       │             │
├─────────┤       ├─────────────┤       ├─────────────┤
│ REST API│       │ MCP Manager │       │ Launcher    │
│ SQLite  │       │ Runtime MCP │       │ Collector   │
│ Internal│       │ Aggregate   │       │ Async       │
│ API     │       │ Gateway     │       │ Health      │
└─────────┘       └─────────────┘       └─────────────┘
    │                     │                     │
    └─────────────────────┴─────────────────────┘
                          │
                  ┌───────┴───────┐
                  │    SQLite     │
                  │ pipeline_tasks│
                  │ subagents     │
                  │ runtimes      │
                  └───────────────┘
```

### 服务组件 (v19)

| 服务 | 职责 | 端口/文件 |
|------|------|--------|
| **Gateway** | REST API + SQLite | `19999` |
| **MCP Gateway** | MCP 管理 | `19998` |
| **Monitor** | 消息监听 + 唤醒 SubAgent | `monitor_main.py` |
| **Launcher** | 准备逻辑 + 创建任务 | `launcher_main.py` |
| **Executor** | 纯执行 (LLM / MCP) | `executor_main.py` |
| **Collector** | 等待 + 后处理 + 触发下一阶段 | `collector_main.py` |
| **Health** | 健康监控 + 任务恢复 | `health_main.py` |

### Stage 流转

```
monitor → runtime → think ←→ actions → summarize
                      ↑          │
                      └──────────┘ (ReACT loop)
```

## 开发工作流

### 添加新 Stage

1. **创建 Launcher** (`services/launchers/your_stage.py`)
```python
@LauncherWorker.register("your_stage_launcher")
class YourStageLauncher(BaseLauncher):
    async def prepare_and_launch(self, task, runtime_id, stage_id, agent_id, args):
        # 准备逻辑
        # 创建 async 任务
        return {
            "async_task_ids": [...],
            "collector_args": {...},
            "next_stage_type": "next_stage_launcher",
        }
```

2. **创建 Collector** (`services/collectors/your_stage.py`)
```python
@CollectorWorker.register("your_stage_collector")
class YourStageCollector(BaseCollector):
    async def collect_and_trigger(self, task, runtime_id, stage_id, agent_id, args):
        # 收集结果
        # 后处理
        return {"next_stage_type": "next_stage_launcher"}
```

3. **创建 Executor** (如需要, `services/executors/your_executor.py`)
```python
@ExecutorWorker.register("your_executor")
class YourExecutor(BaseExecutor):
    async def execute(self, task, runtime_id, stage_id, agent_id, args):
        # 纯执行
        return {"result": ...}
```

### 调试技巧

```bash
# 查看任务状态
curl http://127.0.0.1:19999/internal/pipeline-tasks?status=pending

# 查看 Runtime 状态
curl http://127.0.0.1:19999/internal/runtimes/{agent_id}

# 查看 SubAgent 状态
curl http://127.0.0.1:19999/internal/subagents/{agent_id}

# 手动创建 bootstrap 任务
curl -X POST http://127.0.0.1:19999/internal/pipeline-tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type":"launcher","task_subtype":"monitor_launcher","runtime_id":"system","stage_id":"bootstrap","agent_id":"system","args":{}}'
```

## 相关文档

- [架构详解](./architecture.md) - 完整系统架构
- [Services 设计](./services-architecture.md) - 服务层详细设计
- [MCP 调试](./debugging-mcp.md) - MCP 相关问题排查
- [故障排查](./troubleshooting.md) - 常见问题解决
- [Case Study: agent_id 问题](./case-study-agent-id-mismatch.md) - 真实调试案例
