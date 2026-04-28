# Agent Runtime → Cortex 调用链（`cortex.prepare_llm_context`）

> 源码：**`novaic-agent-runtime`**：`task_queue/topics.py`、`task_queue/handlers/cortex_handlers.py`、`task_queue/utils/cortex_bridge.py`、`task_queue/sagas/react_think.py`；**Cortex**：`novaic_cortex/api.py` **`context_prepare_for_llm`**、`context_stack/engine.py`。

跨服务约定名：**topic `cortex.prepare_llm_context`**（`TaskTopics.CORTEX_PREPARE_LLM_CONTEXT`）。Cortex 仓库内 **没有** 同名 Python 函数；HTTP 实现为 **`POST /v1/context/prepare_for_llm`**。

---

## 1. 从 Saga 到 Handler

**ReactThink**（`task_queue/sagas/react_think.py`）第一步：

| 字段 | 值 |
|------|-----|
| step name | **`prepare_context`** |
| topic | **`TaskTopics.CORTEX_PREPARE_LLM_CONTEXT`**（字符串 **`cortex.prepare_llm_context`**） |
| payload | **`scope_id`、`agent_id`、`user_id`**（`_build_prepare_context_payload`） |

下一步 **`call_llm`** 使用上一步返回的 **`messages` / `tools`**（见 §3）。

---

## 2. `CortexBridge.prepare_for_llm`

**`cortex_bridge.py`**：

- 若 bridge **未启用**：返回 **`{"messages": [], "stack": []}`**。  
- 否则 **`POST`** 到 Cortex：**`/v1/context/prepare_for_llm`**，JSON body：**`user_id`、`agent_id`、`scope_id`**（与 internal API 约定一致，**无** Bearer）。

---

## 3. Cortex HTTP：`context_prepare_for_llm`

**`api.py`**：

1. **`ws = _get_workspace(user_id, agent_id)`**  
2. **`scope_path = /ro/active/{scope_id}`**（根 scope 前缀常量 **`ROOT_SCOPE_PREFIX`**）  
3. **`load_engine_config(ws)`** → **`engine_config_to_compact_config(...)`** → **`ContextEngine(..., config=compact_cfg)`** → **`await engine.prepare_messages_for_llm()`**（内部 **`budget_compact`** 使用与 **`/ro/config/engine.json`** 对齐的 **`CompactConfig`**，见 [budget-compact-algorithm.md](budget-compact-algorithm.md) §8.1）  
4. **`engine.status(messages)`** → 返回 **`estimated_tokens`、`usage_ratio`** 等  
5. 响应 JSON：**`messages`、`stack`（当前 `status` 里 frames 多为占位）、`estimated_tokens`**

---

## 4. Handler：合并消息 + 注入栈快照 + 可选 `NO_TOOL_WARNING`

**`handle_cortex_prepare_llm_context`**（`cortex_handlers.py`）**五步**：

1. **Step 1 `handle_context_read`**：拉 `context.jsonl` + 从 Entangled `messages` 实体把未读消息 `append_context` 进来并标记已读（过滤规则按 `subagent_id` / `msg_type` 路由，详见 `context_handlers.py`）。
2. **Step 2 `bridge.prepare_for_llm(scope_id)`**：HTTP 调 Cortex（§3），拿回 **`messages`**（已 DFS 合并 + `budget_compact`）与 **`stack`**（frames）。
3. **Step 3 `_load_tool_schemas(bridge)`**：`bridge.load_tool_schemas()` → 转成 OpenAI **`tools[]`**（`type: function`），收集 **`tool_names`**。
4. **Step 4a `_format_skill_stack_system_message(stack)`**：若 `stack` 非空，追加一条瞬态 **system** 消息：
   ```text
   [Active scope stack (LIFO — close innermost first)]
     depth 0: user conversation (scope_id=wake-<id>)
     depth 1: debugging (scope_id=debug-1)
   → Stack top: scope_id=debug-1 ... skill_end(scope_id='debug-1', report='...')
   ```
   LLM 由此知道该给 **`skill_end`** 的 `scope_id` 传什么。**不写 `context.jsonl`**，每轮重新生成。详见 [scope-lifecycle.md §9.4](scope-lifecycle.md#94-llm-上下文中的栈快照瞬态)。
5. **Step 4b `NO_TOOL_WARNING`**：若最后一条是 **`assistant`** 且 **无 `tool_calls`**，追加一条瞬态 system 提示（`system_prompt.NO_TOOL_WARNING`，内容同步更新为要求 `skill_end(scope_id=..., report=...)`）。

返回 **`success`、`messages`、`tools`、`tool_names`、`stack`、`new_messages`**。

随后 Saga 的 **`call_llm`** 用 **`_build_llm_call_payload`**：把 **`prepare_context`** 步骤结果里的 **`messages`、`tools`** 传入 **`llm.call`**（**`llm_handlers.handle_llm_call`**）。**LLM handler 不负责决定工具列表**——由 Cortex 侧 schema 决定。

---

## 5. 其它 Cortex topic（同桥）

同一 **`CortexBridge`** 上还有（与「拼上下文」并列的技能与时间线操作）：

| 方法 | HTTP | 关键参数 |
|------|------|---------|
| **`context_skill_begin`** | `POST /v1/context/skill_begin` | `scope_id`（根）、**`child_scope_id`**（LLM 自选，全局唯一）、`skill_name`、`task?` |
| **`context_skill_end`** | `POST /v1/context/skill_end` | `scope_id`（根）、**`child_scope_id`**（必须 == 当前栈顶）、`report` |
| **`context_check_stack`** | （Runtime 内部 handler，未独立 HTTP） | 通过 `context_status` 判断栈是否为空 |
| **`context_status`** | `POST /v1/context/status` | 返回 `stack_depth`、`frames[{depth,skill_name,scope_id}]` 等 |

对应 handler：**`handle_cortex_skill_begin` / `handle_cortex_skill_end` / `handle_cortex_check_stack`**（`cortex_handlers.py`）。Runtime topic **`CORTEX_CHECK_STACK = "cortex.check_stack"`** 由 **`react_actions`** saga 的 `check_skill_stack` 步调用，决定下一步是 `trigger_finalize` 还是 `trigger_next_think`（见 [agent-runtime-all-topics.md §3](agent-runtime-all-topics.md#3-reactthink-saga与-cortex-的衔接)）。

---

## 6. 一览图（Mermaid）

```mermaid
sequenceDiagram
    participant Saga as react_think Saga
    participant H as cortex_handlers
    participant B as CortexBridge
    participant API as Cortex POST /v1/context/prepare_for_llm
    participant E as ContextEngine

    Saga->>H: cortex.prepare_llm_context
    H->>B: prepare_for_llm(scope_id)
    B->>API: POST user_id, agent_id, scope_id
    API->>E: prepare_messages_for_llm()
    E-->>API: messages (after budget_compact)
    API-->>B: messages, stack, estimated_tokens
    B-->>H: dict
    H->>H: load_tool_schemas, NO_TOOL_WARNING?
    H-->>Saga: messages, tools, tool_names, stack
    Saga->>Saga: llm.call(messages, tools)
```

---

## 相关

- [http-api.md](http-api.md) — 完整路由表  
- [budget-compact-algorithm.md](budget-compact-algorithm.md) — Phase B 细节  
- [context-timeline-and-dfs.md](context-timeline-and-dfs.md) — Phase A 时间线  
