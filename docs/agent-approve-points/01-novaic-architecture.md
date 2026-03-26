# NovAIC Agent Runtime 架构

## 一、系统总览

NovAIC Agent Runtime 是一个**分布式 Python 系统**，使用 Saga/DAG 编排模式实现 ReAct agent loop。各服务通过 Redis-based 任务队列通信。

```
用户消息 → Gateway(WS) → MessageProcess → RuntimeStart Saga
                                              ↓
                                         ReactThink Saga ←─────────┐
                                              ↓                    │
                                         ReactActions Saga ───────→│ (循环)
                                              ↓
                                         RuntimeComplete Saga
                                              ↓
                                         Summarize Saga (异步)
```

## 二、服务架构

```
main_novaic.py (统一入口)
├── Gateway           — WebSocket 网关，消息路由
├── Tools Server      — MCP 工具执行服务
├── Queue Service     — Redis pub/sub 管理
├── Task Worker       — Saga step 消费和调度
├── Saga Worker       — Saga 实例管理和 DAG 执行
└── Watchdog          — 超时检测和异常恢复
```

### 核心目录结构

```
novaic-agent-runtime/
├── task_queue/
│   ├── sagas/                    # Saga 定义（DAG 编排）
│   │   ├── runtime_start.py      # 启动：初始化 → MCP → awake → Think
│   │   ├── react_think.py        # Think：读 context → LLM → 保存 → 决策
│   │   ├── react_actions.py      # Actions：并行执行工具 → 保存 → 决策
│   │   ├── runtime_complete.py   # 完成：summary → HRL → sleeping → MCP 销毁
│   │   ├── summarize.py          # 异步 summary merge
│   │   └── message_process.py    # 消息路由（根据 subagent 状态分发）
│   ├── handlers/                 # 任务处理器（每个 topic 一个 handler）
│   │   ├── llm_handlers.py       # LLM 调用（含 multimodal 处理）
│   │   ├── tool_handlers.py      # 工具执行（通过 MCPBusiness）
│   │   ├── context_handlers.py   # Context CRUD
│   │   ├── runtime_handlers.py   # Runtime 生命周期
│   │   ├── summary_handlers.py   # Summary 生成和合并
│   │   ├── subagent_handlers.py  # SubAgent 状态管理
│   │   └── message_handlers.py   # 消息处理
│   ├── business/                 # 业务逻辑层
│   │   ├── llm.py                # LLM 调用封装
│   │   ├── mcp.py                # MCP 工具管理
│   │   ├── runtime.py            # Runtime CRUD
│   │   ├── subagent.py           # SubAgent 管理
│   │   └── message.py            # 消息管理
│   ├── saga.py                   # Saga 核心（SagaDefinition, SagaStep）
│   ├── dag_builder.py            # DAG 构建器
│   └── workers/                  # Worker 实现
├── common/                       # 共享工具
├── config/                       # 配置
└── queue_service/                # Redis 队列服务
```

## 三、ReAct Loop 详解

### 3.1 RuntimeStart Saga

```
init_runtime → create_mcp → set_subagent_awake → trigger(react_think)
```

- 在 `message_process` 中原子创建 Runtime（CAS）
- 初始化：构建 system prompt、匹配技能、注入历史 context
- MCP Server 为每个 runtime 创建独立工具集

### 3.2 ReactThink Saga

```
read_context → call_llm → save_response → decide_actions → trigger(react_actions)
```

- `read_context`: 从 DB 读取最新 context，过滤 `sending` 消息
- `call_llm`: 调用 LLM（支持 multimodal、tool result 展开）
- `decide_actions`: 提取 tool_calls；无 tool_calls 时：
  - 第 1 次：注入 warning + sleep(1s) 给纠正机会
  - 第 2 次：自动 `subagent_rest` 终止
- 工具名标准化：`done/final/finish/complete/rest` → `subagent_rest`

### 3.3 ReactActions Saga

```
execute_tools(并行) → save_results(并行) → check_continue → decide → trigger(think/complete)
```

- 工具**并行执行**：每个 tool_call 独立发到 `tool.execute` topic
- 结果保存只存 `result_id`（TRS 引用），不存完整 content
- 决策逻辑：`need_rest=1 且无新消息` → complete，否则继续 think

### 3.4 RuntimeComplete Saga

```
generate_simple_summary → add_to_hrl → set_completed → set_sleeping/completed
  → notify_parent(条件) → destroy_mcp → trigger(summarize)
```

- Main SubAgent → `sleeping`（可被新消息唤醒）
- Sub SubAgent → `completed`（附带 result 通知 parent）
- HRL（History Runtime List）确保新消息进来时 context 不丢失

## 四、关键设计特点

### 4.1 Saga/DAG 编排

每个 Saga 由 `SagaDefinition` 声明式定义，支持：
- **Sequential steps**: `add_task_step()` — 顺序执行
- **Parallel steps**: `add_parallel_step()` — 并行执行多个任务
- **Decision steps**: `add_decision_step()` — 根据结果动态决策
- **Conditional steps**: `condition=lambda` — 条件执行
- **Optional steps**: `optional=True` — 失败不阻塞

Saga 可 trigger 其他 Saga，形成链式执行：
```
runtime_start → react_think ⇌ react_actions → runtime_complete → summarize
```

### 4.2 Context 管理

- **存储**: DB 中的 messages 列表
- **写入**: `context.append`（带 `idempotency_key` 防重复）
- **读取**: `context.read`（支持 `filter_sending`）
- **TRS**: Tool Result Service 存储大结果，context 只存 `result_id`
- **CAS**: Compare-And-Swap 保证状态原子更新

### 4.3 Summary 体系（四级）

```
Simple Summary  ────→  Hot Summary  ────→  Cold Summary  ────→  Historical Summary
  (runtime 结束时)    (最近 N 个 runtime)  (周期性合并 hot)    (永久存储，高度压缩)
```

### 4.4 事件广播

通过 `broadcast_event` 推送状态：
- `thinking` — LLM 开始推理
- `think_complete` — LLM 返回完整结果
- `tool_running` / `tool_complete` — 工具执行状态
- `runtime_stopped` — Runtime 结束

### 4.5 SubAgent 系统

- **Main SubAgent** (`main-*`): 处理用户消息的主 agent
- **Sub SubAgent** (`sub-*`): 被 main agent spawn 的子 agent
  - 通过 `subagent_spawn` 工具创建
  - 完成后通过 `notify_parent` 回传结果
  - Parent 可通过 `check_new_messages` 获取子 agent 结果

## 五、当前已有优势

| 特性 | 说明 |
|------|------|
| **Saga 崩溃恢复** | 任何步骤失败后可从断点恢复，不丢状态 |
| **TRS result_id** | 工具结果只存引用，context 不膨胀 |
| **事件广播** | 实时推送 agent 状态给前端 |
| **分布式可扩展** | 多 worker 消费，天然水平扩展 |
| **CAS 原子状态** | 无竞态的状态转换 |
| **并行工具执行** | 多个 tool_calls 真正并行（不是顺序 for 循环） |
| **四级 Summary** | 长期记忆的渐进压缩 |
| **幂等性保证** | `idempotency_key` 防止 retry 重复执行 |
