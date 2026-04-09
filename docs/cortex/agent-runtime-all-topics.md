# Agent Runtime → Cortex：全部 Topic 与 Saga

> 源码：`novaic-agent-runtime/task_queue/topics.py`、`handlers/cortex_handlers.py`、`handlers/context_handlers.py`、`sagas/react_think.py`、`utils/cortex_bridge.py`。

与 [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md)（仅 **`cortex.prepare_llm_context`**）互补：本文列 **所有 Cortex 相关 topic** 及 **`context.append`**（写时间线）。

---

## 1. Topic 常量 → Handler → Cortex HTTP

| Topic 常量 | 字符串 | Handler | Cortex HTTP（或说明） |
|------------|--------|---------|------------------------|
| **`CORTEX_PREPARE_LLM_CONTEXT`** | `cortex.prepare_llm_context` | `handle_cortex_prepare_llm_context` | **`POST /v1/context/prepare_for_llm`** + **`load_tool_schemas`** + 可选 `NO_TOOL_WARNING` |
| **`CORTEX_SKILL_BEGIN`** | `cortex.skill_begin` | `handle_cortex_skill_begin` | **`POST /v1/context/skill_begin`** |
| **`CORTEX_SKILL_END`** | `cortex.skill_end` | `handle_cortex_skill_end` | **`POST /v1/context/skill_end`** |
| **`CONTEXT_APPEND`** | `context.append` | `handle_context_append` | **`POST /v1/steps/write`** 或 **`POST /v1/scope/write_assistant`**（见 §2） |

---

## 2. `context.append`（写统一时间线）

**`context_handlers.handle_context_append`** 三种模式：

1. **`write_as_step` + `step`** → **`CortexBridge.write_step`** → **`POST /v1/steps/write`**（`step` dict 透传 **`Workspace.write_step`**）。  
2. **`write_as_assistant` + `message`**（或仅 **`message`**）→ **`write_assistant(...)`** → **`POST /v1/scope/write_assistant`**（见 [internal-api-schemas.md](internal-api-schemas.md)）。

**典型调用链**：**ReactThink** saga 在 **`save_response`** 步使用 **`TaskTopics.CONTEXT_APPEND`**，把 LLM 回复写入 assistant 步；**ReactActions** 在工具执行后也可能追加 **tool** 步。

---

## 3. ReactThink Saga（与 Cortex 的衔接）

**`task_queue/sagas/react_think.py`**：

1. **`prepare_context`** → **`CORTEX_PREPARE_LLM_CONTEXT`**  
2. **`call_llm`** → **`LLM_CALL`**  
3. **`save_response`** → **`CONTEXT_APPEND`**  
4. **`decide_actions`** → 若有 tool_calls 则 **`SAGA_TRIGGER`** → **react_actions** saga  

详见该文件内 **`_build_payload`** / **`build_payload`**。

---

## 4. CortexBridge 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| **`NOVAIC_CORTEX_URL`** | `http://127.0.0.1:19996` | Cortex 基址 |
| **`NOVAIC_CORTEX_ENABLED`** | `true` | `false` 时 bridge 为 no-op |
| **`NOVAIC_CORTEX_TIMEOUT`** | `30` | 秒 |

---

## 5. 与 `agent-pipeline.md` 的关系

父仓 **[architecture/agent-pipeline.md](../architecture/agent-pipeline.md)** 提供全栈管线表；本文仅 **Cortex 相关 topic** 的细表。  

---

## 相关

- [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md)  
- [internal-api-schemas.md](internal-api-schemas.md)  
- [step-index-and-payload-schema.md](step-index-and-payload-schema.md)  
