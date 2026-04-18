# 后端服务与 Agent 管线（§12）

> 与当前 **`novaic-agent-runtime`** / **`novaic-gateway`** / **`novaic-cortex`** 一致；对应原 **`HANDOVER.md` §12**（文中无单独「十二章」标题，此处为完整后端管线篇）。

## 12.1 后端服务组件

| 进程 | 职责 |
|------|------|
| Business | `:19998`，中枢编排：所有 `/internal/*` API、Entangled entity proxy、Device 编排 |
| Gateway | 薄边缘网关：Auth、App WS、TURN、File Proxy |
| Device | `:19993`，设备 registry、CloudBridge WS、硬件执行 API |
| Cortex | `:19996`，Workspace + ContextEngine（DFS）+ Recall + Sandbox |
| Queue Service | Task / Saga 队列 |
| Watchdog | `sending` 消息 → MessageProcess Saga |
| Task Worker | LLM、工具、context |
| Saga Worker | 流程编排 |
| Health / Scheduler Workers | 回收、定时唤醒 |
| ~~Tools Server~~ | **已退役**（`tool_handlers` + Cortex / Gateway） |

## 12.2 消息 → Runtime 完整链路

```
用户发消息
  → Gateway → Business: MessageRepository → Entangled `messages`（status=sending）
  → Watchdog: find_sending() → MessageProcess Saga
  → Step 1 claim_message: sending → sent
  → Step 2 route_message: Runtime 获取/创建
  → Step 3 decide: start_runtime
  → Step 4 trigger: RuntimeStart → ReactThink
```

## 12.3 Agent Loop

```
ReactThink:
  1. cortex.prepare_llm_context
  2. llm.call → LLM Factory（仅传输）
  3. context.save
  4. decide → ReactActions 或结束

ReactActions:
  1. execute_tools
  2. save_results（统一 JSON content）
  3. check_continue
  4. decide → RuntimeComplete 或下一轮 ReactThink
```

## 12.4 工具执行（无独立 Tools Server）

```
LLM tool_call
  → TOOL_EXECUTE → tool_handlers.handle_tool_execute
  → chat_reply / subagent_* / sleep → Business internal
  → shell / skill_* → CortexBridge → Cortex
  → JSON content → context.append
```

| 类别 | 示例 | 路由 |
|------|------|------|
| 生命周期 | chat_reply, subagent_*, sleep | Business `internal/` |
| Cortex | shell, skill_begin, skill_end | CortexBridge |

## 12.5 LLM Factory

- 统一 **`POST /v1/chat/completions`**；api_key 仅在 Factory 内解密。
- Gateway 返回 `model_id`、`factory_url` 等，**不含**密钥。
- 用户偏好：`gateway` `config` 表；模型名 TTL 缓存（5min，不可达时 30s）。

## 12.6 关键数据库分布

详见 [**data-ownership.md**](data-ownership.md)（Entangled vs `gateway.db` v63、Queue、Cortex）。

## 12.7 已知问题：消息积压与重复 Runtime

`SYSTEM_WAKE` 风暴 → 多条唤醒触发并发进入队列。当前方案：由 **Scheduler + Queue Session Coordinator** 按 `(agent_id, subagent_id)` 串行化，每组同一时刻只允许一个活跃 Saga。

## 12.8 源码速查

路径相对于各子模块仓库根（父仓 submodule）：

| 需求 | 路径 |
|------|------|
| Scheduler | `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py` |
| MessageProcess Saga | `novaic-agent-runtime/task_queue/sagas/message_process.py` |
| ReactThink / ReactActions | `novaic-agent-runtime/task_queue/sagas/react_think.py`、`react_actions.py` |
| Cortex 上下文 | `novaic-agent-runtime/.../cortex_handlers.py`；引擎 `novaic-cortex/novaic_cortex/context_stack/engine.py` |
| LLM 传输 | `novaic-agent-runtime/task_queue/handlers/llm_handlers.py` |
| 工具 dispatch | `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` |
| BUILTIN 工具 schema | `novaic-cortex/novaic_cortex/tool_schemas.py` |
| Factory 客户端 | `novaic-agent-runtime/task_queue/factory_client.py` |
| LLM Factory 日志页 | `novaic-llm-factory/static/factory-logs.html` |
| Agent 绑定 / VM 工具 | `novaic-device/device/agent_binding.py` |
| VM 代理 | `novaic-business/business/internal/agent.py` |
| VMUSE Shell | `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/shell.py` |

长文设计稿：[historical-doc-links.md](../historical-doc-links.md)。

**Cortex 与 Runtime 专题（父仓）**：[cortex/README.md](../cortex/README.md)；Runtime 全部 Cortex topic 与 `context.append`：[cortex/agent-runtime-all-topics.md](../cortex/agent-runtime-all-topics.md)。
