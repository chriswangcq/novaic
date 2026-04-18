# Agent Runtime → Cortex：全部 Topic 与 Saga

> 源码：`novaic-agent-runtime/task_queue/topics.py`、`handlers/cortex_handlers.py`、`handlers/context_handlers.py`、`sagas/react_think.py`、`utils/cortex_bridge.py`。

与 [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md)（仅 **`cortex.prepare_llm_context`**）互补：本文列 **所有 Cortex 相关 topic** 及 **`context.append`**（写时间线）。

---

## 1. Topic 常量 → Handler → Cortex HTTP

| Topic 常量 | 字符串 | Handler | Cortex HTTP（或说明） |
|------------|--------|---------|------------------------|
| **`CORTEX_PREPARE_LLM_CONTEXT`** | `cortex.prepare_llm_context` | `handle_cortex_prepare_llm_context` | **`POST /v1/context/prepare_for_llm`** + `load_tool_schemas` + `[Active skill stack]` + 可选 `NO_TOOL_WARNING` |
| **`CORTEX_SKILL_BEGIN`** | `cortex.skill_begin` | `handle_cortex_skill_begin` | **`POST /v1/context/skill_begin`**（payload 要带 `child_scope_id`） |
| **`CORTEX_SKILL_END`** | `cortex.skill_end` | `handle_cortex_skill_end` | **`POST /v1/context/skill_end`**（payload 要带 `child_scope_id`，严格 LIFO） |
| **`CORTEX_CHECK_STACK`** | `cortex.check_stack` | `handle_cortex_check_stack` | 调 **`/v1/context/status`** 取 `stack_depth`，返回 `{stack_depth, current_skill, stack_known}`。Cortex 异常时返回 `stack_depth=1, stack_known=False`（fail-safe：异常时**不 rest**） |
| **`CONTEXT_APPEND`** | `context.append` | `handle_context_append` | **`POST /v1/steps/write`** 或 **`POST /v1/scope/write_assistant`**（见 §2） |

---

## 2. `context.append`（写统一时间线）

**`context_handlers.handle_context_append`** 三种模式：

1. **`write_as_step` + `step`** → **`CortexBridge.write_step`** → **`POST /v1/steps/write`**（`step` dict 透传 **`Workspace.write_step`**）。  
2. **`write_as_assistant` + `message`**（或仅 **`message`**）→ **`write_assistant(...)`** → **`POST /v1/scope/write_assistant`**（见 [internal-api-schemas.md](internal-api-schemas.md)）。

**典型调用链**：**ReactThink** saga 在 **`save_response`** 步使用 **`TaskTopics.CONTEXT_APPEND`**，把 LLM 回复写入 assistant 步；**ReactActions** 在工具执行后也可能追加 **tool** 步。

---

## 3. ReactThink / ReactActions / SubagentWake Saga（与 Cortex 的衔接）

### 3.1 ReactThink — **`task_queue/sagas/react_think.py`**

1. **`prepare_context`** → **`CORTEX_PREPARE_LLM_CONTEXT`**  
2. **`call_llm`** → **`LLM_CALL`**  
3. **`save_response`** → **`CONTEXT_APPEND`**  
4. **`decide_actions`** → 若有 tool_calls 则 **`SAGA_TRIGGER`** → **react_actions** saga  

### 3.2 ReactActions — **`task_queue/sagas/react_actions.py`**（新流程）

1. **`execute_tools`**（parallel）：按 `tool_calls` 逐条 dispatch（含 `skill_begin` / `skill_end` → **`CORTEX_SKILL_BEGIN/END`**，payload 透传 LLM 传入的 `scope_id` 作为 **`child_scope_id`**）。`skill_begin` / `skill_end` 的工具结果现在会**正常写入 steps**（不再被跳过），LLM 能直接看到成功/失败与最新 LIFO 栈。
2. **`save_results`**（parallel）：把工具结果写回时间线。
3. **`check_skill_stack`** → **`CORTEX_CHECK_STACK`**：返回 `{stack_depth, stack_known}`。
4. **`decide_rest`**（decision step，`_decide_rest_or_continue`）按如下优先级判断：  
   1. `round_num >= ServiceConfig.MAX_ROUNDS_BEFORE_FORCE_REST`（默认 **40**，来自 `services.json runtime.max_rounds_before_force_rest`）→ 强制 `trigger_rest`，避免 LLM 无限调用 `chat_reply` 不 `skill_end` 导致死循环。  
   2. `stack_known == False`（Cortex 查栈异常）→ fail-safe 视为「非空」，继续 **`trigger_next_think`**。  
   3. `stack_depth == 0` → **`trigger_rest`**（`SAGA_TRIGGER` → `subagent_rest` saga）。  
   4. 否则 → **`trigger_next_think`**（`SAGA_TRIGGER` → `react_think` saga 下一轮）。
5. **`subagent_rest` 工具已删除**：rest 完全由此处栈空判据驱动。

**为什么是「栈空」而不是「没有 tool_calls」？**  
用户语义是「**没有任何进行中的技能**才休息」，而非「这一轮 LLM 碰巧没调工具」。配合 §3.3 的 Meta skill 自动入栈，栈空等价于「Meta 也被关了 = 真的收工」。

### 3.3 SubagentWake — **`task_queue/sagas/subagent_wake.py`**

1. `session_init` → 会话初始化（含 `current_scope_id` 落到 `subagents` 表）。
2. **`auto_meta_skill`**（**必需**，非 optional）→ **`CORTEX_SKILL_BEGIN`**，`_build_auto_meta_skill_payload` 产出：
   ```python
   {
     "scope_id": root_scope_id,
     "child_scope_id": f"meta-{root_scope_id}",
     "name": "meta",
     "task": "",
   }
   ```
   这样**唤醒后栈至少 1 层**，防止 LLM 第一轮就判定「栈空」立刻休息。  
   关键点：该步骤**不再是 `optional=True`**，`handle_cortex_skill_begin` 在 Cortex 返回 `ok: False` 或抛异常时都会 raise，使整个 wake saga 失败而不是静默降级。
3. `set_subagent_awake` → 翻状态。
4. `trigger_think` → 触发首轮 `react_think`。

**Dispatch 入口校验**：**`/api/queue/dispatch`**（`queue_service/routes.py:DispatchRequest`）**`user_id` 必填**（空串或缺失返回 400），因为 `auto_meta_skill` 需要 `user_id` 才能在 Cortex 建立 scope。`scheduler_worker_sync` 扫到没有 `user_id` 的 agent 会跳过并打日志。

详见各 saga 文件内 **`_build_*_payload`**。

---

## 4. 相关配置（`services.json`）

| Key | 默认 | 作用 |
|-----|------|------|
| `services.cortex.url` | `http://127.0.0.1:19996` | Cortex 基址 |
| `cortex.enabled` | `true` | `false` 时 bridge 为 no-op |
| `cortex.timeout` | `30` | 秒 |
| `runtime.max_rounds_before_force_rest` | `40` | ReactActions 硬上限，超过强制 `trigger_rest` |

---

## 5. 与 `agent-pipeline.md` 的关系

父仓 **[architecture/agent-pipeline.md](../architecture/agent-pipeline.md)** 提供全栈管线表；本文仅 **Cortex 相关 topic** 的细表。  

---

## 相关

- [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md)  
- [internal-api-schemas.md](internal-api-schemas.md)  
- [step-index-and-payload-schema.md](step-index-and-payload-schema.md)  
