# Agent Runtime 运行时架构总览

`novaic-agent-runtime` 是 Agent loop 的执行层。它不拥有产品实体数据库，也不承担 Gateway 的接入职责；它围绕 Queue Service、Saga/Task Workers、Cortex、Business 和 LLM Factory 组合出可恢复的异步执行管线。

---

## 1. 核心定位

Runtime 是一组可独立启动的 Python 进程：

- **`queue-service`**：监听 `:19997`，拥有 `queue.db`，负责 Task/Saga/session 串行化、claim、重试、恢复。
- **`main_subscriber`（Business 侧进程）**：扫描 Environment notifications，把可调度通知投递到 Queue Service。
- **`saga-worker`**：认领 Saga，推动 MessageProcess / React loop / finalize 等流程。
- **`task-worker`**：执行原子任务，例如 LLM 调用、工具执行、Cortex 写入。
- **`health`**：恢复超时 Task/Saga。
- **`scheduler`**：定时唤醒扫描者，把 due wake 投递到 Queue Service。

Runtime 的强状态只在 Queue Service 自己的 `queue.db`。Agent 的工作轨迹、scope tree、reasoning/action/observation 进入 Cortex；产品实体和消息投影进入 Business/Entangled。

---

## 2. 消息到回复的当前闭环

```text
1. App 发送消息
   └─ Entangled action: messages.send
      └─ Business: 写 Environment IM event + chat UI projection

2. Business Environment
   └─ 生成 notification
      └─ DispatchSubscriber claim/dispatch
         └─ Queue Service /api/queue/dispatch

3. Queue / Saga
   └─ Session Coordinator 按 agent/thread 串行化
      └─ Saga Worker 认领 MessageProcess / subagent_wake

4. ReactThink
   ├─ Runtime → Cortex: prepare_for_llm，读取 agent-root scope 树和当前 active scope
   ├─ Runtime → LLM Factory: /v1/chat/completions
   └─ Runtime → Cortex: append assistant reasoning / tool calls / observations

5. ReactActions
   ├─ im_read / im_reply / im_send / subagent_spawn → Business Environment/Subagent APIs
   ├─ shell / skill_* / payload_* → CortexBridge → Cortex
   ├─ display / audio_qa / sleep → Runtime native executor
   └─ device-facing tools → Business → Device → CloudBridge/VmControl

6. 本轮结束
   └─ LLM 调用 skill_end(report=...)
      └─ Cortex 折叠当前 wake scope summary.md
         └─ Business/Entangled 已有用户可见回复和 Agent Monitor 投影
```

---

## 3. 服务协作边界

| 服务 | Runtime 视角 |
|---|---|
| **Business** | 产品 API、Environment IM、SubAgent、设备编排、LLM 配置查询 |
| **Queue Service** | Task/Saga/session 的唯一调度状态 |
| **Cortex** | scope tree、LLM context、tool observation、payload ref、summary.md |
| **LLM Factory** | 模型/provider/API key 隔离层，Runtime 只发标准 chat completion |
| **Device** | Runtime 不直接拥有硬件；硬件动作经 Business 编排到 Device |
| **Gateway** | 边缘广播/信令参数仍可能作为配置存在；不拥有 Runtime 输入、Queue DB、产品实体或 LLM 配置 |

---

## 4. 关键不变量

- Runtime 不从 Gateway 读取聊天正文。
- Queue DB 不属于 Gateway。
- LLM 上下文来自 Cortex `prepare_for_llm`。
- LLM 调用只走 LLM Factory。
- 用户/子 Agent 通信走 Environment IM 工具路径。
- 跨 wake 连续性来自 Cortex agent-root scope 树和 `skill_end(report=...)` 写入的 `summary.md`。
- Gateway 不是 Runtime 的业务回调目标；用户可见消息和 activity 投影经 Business/Entangled 落地。

---

## 5. 源码入口

| 需求 | 路径 |
|---|---|
| Queue Service | `novaic-agent-runtime/queue_service/main.py` |
| Queue API | `novaic-agent-runtime/queue_service/routes.py` |
| Saga Worker | `novaic-agent-runtime/task_queue/workers/saga_worker_sync.py` |
| Task Worker | `novaic-agent-runtime/task_queue/workers/task_worker_sync.py` |
| ReactThink / ReactActions | `novaic-agent-runtime/task_queue/sagas/react_think.py`, `react_actions.py` |
| Cortex bridge | `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` |
| LLM Factory client | `novaic-agent-runtime/task_queue/factory_client.py` |
| Environment dispatch subscriber | `novaic-business/main_subscriber.py` |

