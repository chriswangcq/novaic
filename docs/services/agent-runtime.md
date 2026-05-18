# Agent Runtime + Queue Service

## 概述与职责

Agent Runtime 是 Novaic 平台的核心执行引擎，负责驱动 AI Agent 的推理循环、工具调用和多步骤任务编排。它由两个协作进程组成：

- **Queue Service**：HTTP 服务（端口 `:19997`），负责任务队列管理、调度分发和 API 暴露。
- **Agent Runtime Worker**：工作进程，从队列中消费任务并执行具体的 Agent 逻辑。

技术栈为 Python / FastAPI，通过子命令体系统一管理进程生命周期。

## 进程角色与启动方式

Agent Runtime 提供 9 个子命令，覆盖服务运行、健康检查和调度等场景：

| 子命令 | 角色 | 说明 |
|--------|------|------|
| `serve` | 主服务 | 启动完整的 Agent Runtime 服务（含 Queue Service） |
| `queue-service` | 队列服务 | 单独启动 Queue Service HTTP 服务 |
| `worker` | 工作进程 | 启动 Worker 消费任务 |
| `health-check` | 健康检查 | 检查服务及 Worker 健康状态 |
| `scheduler` | 调度器 | 启动定时任务调度进程 |
| 其他 4 个 | 辅助命令 | 包括迁移、调试、配置等工具命令 |

典型部署中，`queue-service` 和 `worker` 分别独立启动，通过 Redis 队列进行解耦通信。

## Worker 类型清单

系统定义了 6 种 Worker 类型，每种负责特定的执行域：

| Worker 类型 | 职责 | 典型触发场景 |
|-------------|------|-------------|
| `react_loop` | ReAct 推理循环 | Agent 接收用户消息后启动推理 |
| `shell_execute` | Shell 命令执行 | Agent 决定执行终端命令 |
| `observe_screen` | 屏幕观察 | Agent 需要获取设备当前屏幕状态 |
| `shell_display` | Shell 显示渲染 | 将 Shell 输出投射到前端展示 |
| `perception_action` | 感知-动作循环 | Agent 执行基于视觉的操作流程 |
| `mcp_tool` | MCP 工具调用 | Agent 调用 MCP 协议注册的外部工具 |

每个 Worker 类型对应独立的消费队列，支持按类型横向扩缩容。

## Saga/Task 处理流程

Agent Runtime 定义了 5 个 Saga（传奇模式），用于编排需要多步骤协调的复杂工作流：

1. **Agent 推理 Saga**：编排 `react_loop` → 工具选择 → 工具执行 → 结果回写的完整循环。
2. **Shell 执行 Saga**：协调命令下发、执行监控、输出采集和超时处理。
3. **屏幕观察 Saga**：触发截屏 → 图像获取 → 视觉分析的链式流程。
4. **感知-动作 Saga**：将屏幕观察与鼠标/键盘操作串联为闭环。
5. **MCP 工具 Saga**：处理 MCP 协议的请求/响应生命周期。

Saga 通过状态机驱动，每一步的失败都有补偿逻辑，确保任务最终一致性。

```
用户消息 → Queue Service 入队
       → Scheduler 分发到对应 Worker 队列
       → Worker 消费并执行
       → Saga 编排多步骤（如需要）
       → 结果写回 Cortex
       → 通知前端
```

## Queue Service 架构

Queue Service 以 FastAPI 应用形式运行在端口 `:19997`，承担任务队列的中枢角色：

- **任务入队**：接收来自 Business 和 Gateway 的任务请求，写入 Redis 队列。
- **任务调度**：根据 Worker 类型和优先级分发任务。
- **状态查询**：提供任务状态、队列深度、Worker 负载等查询接口。
- **Saga 协调**：作为 Saga 的协调者，管理多步骤任务的状态流转。

## API 路由

Queue Service 对外暴露 45+ 条 HTTP API 路由，主要分类如下：

| 路由前缀 | 数量 | 说明 |
|----------|------|------|
| `/task` | ~15 | 任务提交、查询、取消、重试 |
| `/queue` | ~8 | 队列状态、深度、清理 |
| `/worker` | ~6 | Worker 注册、心跳、状态 |
| `/saga` | ~8 | Saga 创建、步骤推进、状态查询 |
| `/health` | ~3 | 健康检查、就绪探针 |
| `/internal` | ~5 | 内部调试和管理接口 |

## 依赖关系

```
Agent Runtime
├── Cortex          — 读写上下文事件，获取对话历史
├── Device          — 下发设备操作命令（键鼠、截屏）
├── LLM Factory     — 调用大模型推理
├── Sandbox Service — 在隔离沙箱中执行 Shell 命令
└── Business        — 获取 Agent 配置和实体数据
```

Agent Runtime 是平台中依赖最广泛的服务，作为 Agent 执行的核心枢纽，与几乎所有后端服务产生交互。
