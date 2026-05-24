# 后端服务与 Agent 管线（§12）

> 与当前 **`novaic-agent-runtime`** / **`novaic-gateway`** / **`novaic-cortex`** 一致；对应原 **`HANDOVER.md` §12**（文中无单独「十二章」标题，此处为完整后端管线篇）。

## 12.1 后端服务组件

| 进程 | 职责 |
|------|------|
| Business | `:19998`，中枢编排：所有 `/internal/*` API、Entangled entity proxy、Device 编排 |
| Gateway | 薄边缘网关：Auth、App WS、TURN、Blob edge |
| Device | `:19993`，设备 registry、CloudBridge WS、硬件执行 API |
| Cortex | `:19996`，Workspace + LIFO Scope Tree + ContextEngine（DFS）+ Sandbox |
| Queue Service | Task / Saga 队列 |
| Watchdog | 已退出生产主路径；不要把它当作消息唤醒或定时唤醒 owner |
| Task Worker | LLM、工具、context |
| Saga Worker | 流程编排 |
| Health / Scheduler Workers | 回收、定时唤醒 |

## 12.2 消息 → Runtime 完整链路

```
用户发消息
  → Entangled action hook → Business: Environment IM event + chat UI projection
  → DispatchSubscriber（Environment notification）/ Scheduler（定时唤醒）
  → Queue dispatch: subagent_wake
  → session.init: ensure agent_root scope + create current wake scope
  → ReactThink
```

## 12.3 Agent Loop

```
ReactThink:
  1. cortex.prepare_llm_context
  2. llm.call → LLM Factory（仅传输）
  3. 保存 assistant message 到当前 active scope
  4. decide → ReactActions 或结束

ReactActions:
  1. execute_tools
  2. save_results（tool step，统一 JSON content）
  3. check_continue
  4. 若 scope stack 仍非空，继续下一轮 ReactThink，让 LLM 有机会 `skill_end(report=...)`
  5. 栈空后触发 wake_finalize 做结构性收尾
```

## 12.4 工具执行

```
LLM tool_call
  → TOOL_EXECUTE → tool_handlers.handle_tool_execute
  → shell → Cortex sandbox command surface
     → agentctl im reply/send/read/history/search/context → Business Environment APIs
     → agentctl subagent spawn / media audio-qa → Business/SubAgent/Runtime APIs
     → cortex payload read/search/summarize/qa → Cortex APIs
     → devicectl hd ... → Business → Device
  → skill_begin / skill_end → Cortex scope lifecycle
  → display / sleep → Runtime native executor
  → JSON content → Cortex step timeline
```

| 类别 | 示例 | 路由 |
|------|------|------|
| 通信 | shell `agentctl im ...`, `agentctl subagent ...` | Business `internal/` / Environment IM |
| Cortex | shell `cortex payload ...`, skill_begin, skill_end | CortexBridge |
| Runtime native | display, sleep; shell `agentctl media audio-qa ...` | Runtime executor |

## 12.5 LLM Factory

- 统一 **`POST /v1/chat/completions`**；api_key 仅在 Factory 内解密。
- Gateway 返回 `model_id`、`factory_url` 等，**不含**密钥。
- 用户偏好：`gateway` `config` 表；模型名 TTL 缓存（5min，不可达时 30s）。

## 12.6 关键数据库分布

详见 [**data-ownership.md**](data-ownership.md)（Entangled vs `gateway.db` v63、Queue、Cortex）。

## 12.7 Sync-by-default（PR-34 Worker-Sync 终态）

内部 Wake / dispatch 链路一律 **同步**，`async` 只保留在 FastAPI 边缘：

| 组件 | 运行形态 | 说明 |
|------|---------|------|
| DispatchAssembler | `assemble_sync` / `dispatch_sync`（同步） | PR-34 34e 起删除 async 孪生，唯一调用面 |
| AgentOwnershipResolver | `resolve_sync`（同步，`threading.Lock` + FIFO 缓存） | PR-34 34e 删除 `async resolve` 与 `asyncio.Lock` 字典 |
| DispatchSubscriber | **独立子进程** (`main_subscriber.py`) | 从 Business lifespan 的后台 task 拆出；崩溃以 `ps` 可见、退出码非零的方式"大声死亡"，而不是静默停止处理 Environment notifications |
| HealthWorker / SchedulerWorker | 同步线程 (`health_worker.py` / `scheduler_worker.py`) | `threading.Event` + `time.sleep`，`_sync` 后缀已去除 |
| SagaWorker / TaskWorker | 同步线程 (`saga_worker.py` / `task_worker.py`) | `threading` / process boundary；文件名已与同步主路径一致 |

为什么：前版 DispatchSubscriber 作为 FastAPI lifespan 的 `asyncio.create_task` 运行，任意未捕获异常会让调度循环静默停止；现在把内部路径搬到"一个失败 = 一个进程/线程退出"的模型，故障必然外显。

CI 守门：[`scripts/ci/check_no_internal_async.py`](../../scripts/ci/check_no_internal_async.py) 对上述核心文件禁用 `async def` / `import asyncio` / `httpx.AsyncClient` / `await`，并在 `.github/workflows/lint.yml` 中强制运行。新增守门文件时按该脚本 `GUARDED` 列表注释说明理由。

## 12.8 已知问题：消息积压与重复 Runtime

`SYSTEM_WAKE` 风暴 → 多条唤醒触发并发进入队列。当前方案：由 **Scheduler + Queue Session Coordinator** 按 `(agent_id, subagent_id)` 串行化，每组同一时刻只允许一个活跃 Saga。

## 12.9 源码速查

路径相对于各子模块仓库根（父仓 submodule）：

| 需求 | 路径 |
|------|------|
| Scheduler | `novaic-agent-runtime/task_queue/workers/scheduler_worker.py` |
| Health | `novaic-agent-runtime/task_queue/workers/health_worker.py` |
| DispatchSubscriber (subprocess) | `novaic-business/business/subscribers/dispatch_subscriber.py`；入口 `novaic-business/main_subscriber.py` |
| MessageProcess Saga | `novaic-agent-runtime/task_queue/sagas/message_process.py` |
| ReactThink / ReactActions | `novaic-agent-runtime/task_queue/sagas/react_think.py`、`react_actions.py` |
| Cortex 上下文 | `novaic-agent-runtime/.../cortex_handlers.py`；引擎 `novaic-cortex/novaic_cortex/context_stack/engine.py` |
| LLM 传输 | `novaic-agent-runtime/task_queue/handlers/llm_handlers.py` |
| 工具 dispatch | `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` |
| BUILTIN 工具 schema | `novaic-common/common/tools/llm_builtin.py`；Cortex `/v1/internal/tools` 只转发 common schema |
| Factory 客户端 | `novaic-agent-runtime/task_queue/factory_client.py` |
| LLM Factory 日志页 | `novaic-llm-factory/static/factory-logs.html` |
| Agent 绑定 / VM 工具 | `novaic-device/device/agent_binding.py` |
| VM 代理 | `novaic-business/business/internal/agent.py` |
| VMUSE Shell | `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/shell.py` |

长文设计稿：[historical-doc-links.md](../historical-doc-links.md)。

**Cortex 与 Runtime 专题（父仓）**：[cortex/README.md](../cortex/README.md)；Runtime 全部 Cortex topic 与 `context.append`：[cortex/agent-runtime-all-topics.md](../cortex/agent-runtime-all-topics.md)。
