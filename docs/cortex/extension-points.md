# 扩展点：Hooks、协议、StepTree、压缩建议

> 源码：`hooks.py`、`protocols.py`、`context_stack/step_tree.py`、`context_stack/engine.py`、`context_budget.py`、`runtime.py`（**`suggest_compact`**、**`_fire_hook`**）。

## 1. `CortexHooks`（`hooks.py`）

可选生命周期观察者，**不控制主流程**，仅列表回调：

| 字段 | 含义 |
|------|------|
| `on_scope_created` / `on_scope_archived` | scope 创建 / 归档 |
| `on_skill_loaded` | 技能安装完成 |
| `on_skill_begin` / `on_skill_end` | 技能 scope 起止 |

**`Cortex._fire_hook`**：同步调用；若回调为 **async**，用 **`asyncio.ensure_future`**  fire-and-forget（不阻塞主逻辑）。异常 → **`warnings.warn`**。

**`Workspace._emit`**：对同名 hook 列表的 **async** 友好封装（用于 workspace 内部事件）。

## 2. 协议（`protocols.py`）

| 协议 | 方法 |
|------|------|
| **`TokenCounter`** | `count` / `count_messages` — token 预算 |

由 **宿主**（测试或上层服务）在构造 **`Cortex`** 时可选传入。

## 3. `suggest_compact`（`context_budget.py` + `runtime`）

**`usage_ratio(used_tokens, context_window)`**、**`compact_level(used_tokens, cfg)`** → 返回 **`none` / `normal` / `emergency`**（与 **`EngineConfig.compact_threshold` / `emergency_threshold`** 比较）。

**`Cortex.suggest_compact(used_tokens)`** 把上述结果与配置阈值一并打成 **dict**，供外部根据「已用 token」提示是否压缩（**不**自动执行 `budget_compact`；**实际压缩**在 **`ContextEngine.prepare_messages_for_llm`** 末尾）。

## 4. StepTree vs ContextEngine

- **`ContextEngine`**（[context-timeline-and-dfs.md](context-timeline-and-dfs.md)）：读 **`steps/_index.jsonl`**，**按时间线**渲染为 LLM messages，是 **面向 LLM 的权威路径**。
- **`StepTreeBuilder` / `StepNode` / `StepTree`**：从 workspace 步骤构建 **树**，便于分析、折叠辅助、**`collect_tool_results`** 等；**`engine.py`** 会 import **`render_scope_fold`** 等与树协作。

**结论**：最终消息列表以 **`engine`** 为准；**`step_tree`** 是分析与辅助结构。

## 相关

- [engine-config-and-metrics.md](engine-config-and-metrics.md) — 阈值与 `budget_compact`  
