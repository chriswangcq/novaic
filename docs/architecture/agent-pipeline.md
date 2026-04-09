# Agent Runtime：消息、Saga、工具与 LLM

> 对应 **`HANDOVER.md` §12**。代码在 **`novaic-agent-runtime`**、**`novaic-gateway`**、**`novaic-cortex`**。

## 后端进程（摘要）

| 进程 | 职责 |
|------|------|
| Gateway | HTTP、WS Push、`gateway.db` 运维表；业务实体经 Entangled |
| Cortex | 认知服务 `:19996`（Workspace、DFS 上下文、Recall、Sandbox） |
| Queue Service | Task / Saga 队列 |
| Watchdog | `sending` 消息 → MessageProcess Saga |
| Task / Saga / Health / Scheduler Workers | 执行与回收 |
| ~~Tools Server~~ | **已退役**；工具由 Task Worker `tool_handlers` + Cortex / Gateway |

## 消息 → Runtime（链路）

```
用户消息 → Entangled 写入 → Watchdog → MessageProcess Saga
  → claim / route → RuntimeStart → ReactThink → …
```

## ReactThink / ReactActions（概念）

**ReactThink**：`cortex.prepare_llm_context` → `llm.call`（Factory，仅传输）→ `context.save` → `decide`（工具或结束）。

**ReactActions**：并行 `execute_tools` → `save_results`（统一 JSON `content`）→ `check_continue` → 下一轮或 `RuntimeComplete`。

## 工具路由（无独立 Tools Server）

```
tool_call → task_queue TOOL_EXECUTE → tool_handlers
  → chat_reply / subagent_* / sleep → Gateway internal API
  → shell / skill_* → CortexBridge → Cortex
```

## LLM Factory

- 统一 **`POST /v1/chat/completions`**；密钥只在 Factory 内解密。
- Gateway 侧返回 `model_id`、`factory_url` 等，**不含** api_key。
- 用户默认模型等：`gateway` `config` 表 + TTL 缓存。

## 已知问题（规划）

- **Watchdog v2**：`SYSTEM_WAKE` 风暴可能导致重复 Saga；方向为 **按 agent 分组**批量处理（见 HANDOVER §12.7）。

## 文件速查（子模块路径）

| 主题 | 路径 |
|------|------|
| Watchdog | `novaic-agent-runtime/.../watchdog_sync.py` |
| MessageProcess | `.../sagas/message_process.py` |
| ReactThink / ReactActions | `.../sagas/react_think.py`、`react_actions.py` |
| 工具 dispatch | `.../handlers/tool_handlers.py` |
| LLM 传输 | `.../handlers/llm_handlers.py` |
| Cortex 上下文 | `novaic-cortex/novaic_cortex/context_stack/engine.py` |
| Factory 客户端 | `.../factory_client.py` |
| LLM Factory 日志页 | `novaic-llm-factory/static/factory-logs.html` |

长文设计稿见 [`historical-doc-links.md`](../historical-doc-links.md)（Cortex / no-tool 等）。
