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
| `auto_summary_max_tokens` | 摘要器 token 上限 |
| `gem_fusion_enabled` / `gem_fusion_merge_factor` / `gem_fusion_max_level` | Gem 融合开关与深度 |
| `fuzzy_memory_token_budget` | **Recall** 默认 token 预算（与 `Recall` 构造一致） |
| `max_skill_depth` | 技能嵌套深度 |
| `sandbox_timeout_default` / `sandbox_timeout_max` | Shell 超时 |

文件不存在或 JSON 坏：**回退默认 `EngineConfig()`**。

---

## 2. `Cortex.initialize()` 如何应用配置

`runtime.py` 中 **`initialize()`**：

1. **`workspace.initialize()`**（建目录占位等）  
2. **`load_engine_config(workspace)`**  
3. 用新 **`cfg`** 重建 **`Sandbox`**（`max_wall_timeout`）、**`Recall`**（`token_budget=fuzzy_memory_token_budget`）、**`Compactor`**（fusion 参数、`summarizer_max_tokens=auto_summary_max_tokens`）

---

## 3. `budget_compact`（与 `ContextEngine`）

- **`ContextEngine.prepare_messages_for_llm`** 末尾调用 **`budget_compact(messages, CompactConfig, counter)`**。  
- **`CompactConfig`** 由 **`EngineConfig`** 映射而来（见 `context_stack/types.py` 与 engine 构造链）。  
- 行为摘要见 [context-timeline-and-dfs.md](context-timeline-and-dfs.md) §6；细节读 **`budget.py`**。

---

## 4. `usage_ratio` / `compact_level`（`context_budget.py`）

供 **`Cortex.suggest_compact`** 等使用：根据当前消息估算 token 与 **`EngineConfig`** 阈值，返回压缩建议档位（具体字段见源码）。

---

## 5. `CortexMetrics`（`types.py`）

在 **`tool_shell`**、**`compactor`**、fusion 等路径上累加，例如：**`shell_executions`**、**`shell_timeouts`**、**`total_tokens_saved`**、**`total_fusions`** 等（以 **`types.CortexMetrics`** 定义为准）。

---

## 相关

- [context-timeline-and-dfs.md](context-timeline-and-dfs.md)  
- [compactor-and-gem-fusion.md](compactor-and-gem-fusion.md)  
- [sandbox-shell.md](sandbox-shell.md)  
