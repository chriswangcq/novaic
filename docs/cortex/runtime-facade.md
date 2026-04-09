# Cortex 运行时门面（`Cortex`）

> 源码：`novaic_cortex/runtime.py`（**`Cortex`**）。聚合 **`Workspace`、`Sandbox`、`Recall`、`Compactor`**、可选 **`Summarizer` / `TokenCounter` / `CortexHooks`**、**`CortexMetrics`**。

## 1. 构造与 `initialize()`

- 构造时用 **`EngineConfig()` 默认值**先建好 **`Sandbox` / `Recall` / `Compactor`**（避免在 `initialize()` 前调用时未初始化）。  
- **`await initialize()`** 会：  
  1. **`workspace.initialize()`**  
  2. **`_seed_builtin_tools()`**：若不存在则把 **`BUILTIN_TOOL_SCHEMAS`** 写入 **`/ro/config/tools/{name}.json`** 与 **`_index.json`**（键空间见 `store` 前缀 `agents/{agent_id}/ro/...`）。  
  3. **`load_engine_config(workspace)`** 读 **`/ro/config/engine.json`**，并用新配置 **重建** `Sandbox`、`Recall`、`Compactor`。

---

## 2. Agent 面向的「工具」方法（与 HTTP 对齐）

| 方法 | 作用（概要） |
|------|----------------|
| **`tool_read` / `tool_write`** | 校验路径在 `/ro/` 或 `/rw/`，经 `Workspace` 读写 |
| **`tool_shell`** | `Sandbox.exec`，超时取 `min(请求, config.sandbox_timeout_max)`，并更新 metrics |
| **`skill_begin` / `skill_end`** | 子 scope 生命周期；**`skill_end`** 触发 **`compactor.compact`**（见 [compactor-and-gem-fusion.md](compactor-and-gem-fusion.md)） |
| **`load_tool_schemas`** | 合并 builtin + skill 目录下的 schema |
| **`prepare_system_prompt` / `suggest_compact`** | Recall 与压缩建议（`context_budget`） |

路径校验：**`_validate_agent_tool_path`** — 必须以 **`/ro/`** 或 **`/rw/`** 开头。

---

## 3. 与 Agent Runtime 名称的对应

仓库内 **没有** 名为 **`prepare_llm_context`** 的 Python 方法；跨服务约定在 Runtime 侧叫该名，Cortex 侧实现为 **`POST /v1/context/prepare_for_llm`** + **`ContextEngine`**（见 [http-api.md](http-api.md)）。

---

## 相关

- [engine-config-and-metrics.md](engine-config-and-metrics.md)  
- [sandbox-shell.md](sandbox-shell.md)  
- [recall.md](recall.md)  
