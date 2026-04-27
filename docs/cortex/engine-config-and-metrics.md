# Engine 配置、上下文预算与指标

> 源码：`novaic_cortex/config.py`（**`EngineConfig`**、**`load_engine_config`**）、`context_stack/budget.py`（**`budget_compact`**）、`context_budget.py`（**`usage_ratio` / `compact_level`** 等）、`types.py`（**`CortexMetrics`**）。

## 1. `EngineConfig`（`/ro/config/engine.json`）

路径常量：**`ENGINE_JSON_PATH = "/ro/config/engine.json"`**（逻辑路径，经 Workspace 读）。

| 字段 | 含义（默认摘自 `config.py`） |
|------|------------------------------|
| `context_window` | 上下文窗口 token 上限（200_000） |
| `compact_threshold` | 温和压缩阈值比例（0.70） |
| `emergency_threshold` | 紧急压缩阈值（0.95） |
| `micro_max_tool_output_chars` | 微压缩时 tool 输出截断 |
| `micro_preserve_recent` | 保留最近若干「轮」 |
| `fuzzy_memory_token_budget` | **Recall** 默认 token 预算（与 `Recall` 构造一致） |
| `max_skill_depth` | 技能嵌套深度 |
| `sandbox_timeout_default` / `sandbox_timeout_max` | Shell 超时 |

文件不存在或 JSON 坏：**回退默认 `EngineConfig()`**。

---

## 2. `Cortex.initialize()` 如何应用配置

`runtime.py` 中 **`initialize()`**：

1. **`workspace.initialize()`**（建目录占位等）  
2. **`load_engine_config(workspace)`**  
3. 用新 **`cfg`** 重建 **`Sandbox`**（`max_wall_timeout`）

---

## 3. `budget_compact`（与 `ContextEngine`）

- **`ContextEngine.prepare_messages_for_llm`** 末尾调用 **`budget_compact(messages, self.config, counter=self._counter)`**，使用 **`CompactConfig`**（`context_stack/types.py`）。字段与 **`EngineConfig`** 在 **`engine.json`** 中语义对应，但 **字段名**在 **`EngineConfig`** 与 **`CompactConfig`** 之间不完全相同（例如 **`micro_preserve_recent`** ↔ **`micro_preserve_recent_rounds`** 由 **`engine_config_to_compact_config`** 映射）。  
- **`Cortex.initialize()`** 会 **`load_engine_config`** 并作用于 **`Sandbox`**。  
- **`POST /v1/context/prepare_for_llm`**（`api.py`）在构造 **`ContextEngine`** 前同样 **`load_engine_config(ws)`**，再 **`engine_config_to_compact_config(engine_cfg)`** 传入 **`config=`**，因此 **修改** **`/ro/config/engine.json`** 中的 **`context_window`、`compact_threshold`、`emergency_threshold`、`micro_*`、`max_skill_depth`** 等**会影响**拼 LLM 上下文时的 **`budget_compact`**。详见 [budget-compact-algorithm.md](budget-compact-algorithm.md) §8.1。  
- 算法逐步说明：[budget-compact-algorithm.md](budget-compact-algorithm.md)；时间线前半段：[context-timeline-and-dfs.md](context-timeline-and-dfs.md)。

---

## 4. `usage_ratio` / `compact_level`（`context_budget.py`）

供 **`Cortex.suggest_compact`** 等使用：根据当前消息估算 token 与 **`EngineConfig`** 阈值，返回压缩建议档位（具体字段见源码）。

---

## 5. `CortexMetrics`（`types.py`）

在 **`tool_shell`**、scope 创建/归档、技能安装等路径上累加，例如：**`shell_executions`**、**`shell_timeouts`**、**`scopes_created`**、**`scopes_archived`** 等（以 **`types.CortexMetrics`** 定义为准）。

---

## 相关

- [context-timeline-and-dfs.md](context-timeline-and-dfs.md)  
- [budget-compact-algorithm.md](budget-compact-algorithm.md)  
- [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md)  
- [sandbox-shell.md](sandbox-shell.md)  
