# `budget_compact` 算法（Phase B）

> 源码：`novaic_cortex/context_stack/budget.py`、**`CompactConfig`** / **`TokenCounter`** / **`count_all_tokens`**：`context_stack/types.py`。设计参考：`context-stack-v2-passive-design.md` §4.4（若仓库内有该文档）。

## 1. 在流水线中的位置

**`ContextEngine.prepare_messages_for_llm`**（`context_stack/engine.py`）在读完 **`meta.json`**、拼完 **`_index.jsonl`** 对应消息之后，**最后一步**调用：

```text
messages = budget_compact(messages, self.config, counter=self._counter)
```

因此压缩作用于 **已展开为 OpenAI 风格 `messages[]`** 的列表（含 `role` / `content` / `tool_calls` 等）。

---

## 2. 总 token 与分支

1. **`total_tokens = count_all_tokens(messages, counter)`**  
   - 若注入 **`TokenCounter`**，用 **`counter.count_messages(messages)`**；  
   - 否则对每条消息 **`estimate_message_tokens`**（内容长度 + `tool_calls` 里 name/arguments + 少量 overhead）。

2. **`ratio = total_tokens / config.context_window`**（`context_window <= 0` 时 ratio 视为 0）。

3. 分支（**互斥优先级**：先判紧急，再温和，否则走 micro）：

| 条件 | 调用 |
|------|------|
| `ratio >= emergency_threshold` | **`_emergency_compact`** |
| `ratio >= compact_threshold` | **`_warm_compact`**（内部会先走一遍 micro 逻辑） |
| 否则 | **`_micro_compact`** |

**日志**：紧急打 **WARNING**，温和打 **INFO**，前缀 **`[budget]`**。

---

## 3. 「轮」边界：`_round_boundaries`

下标 **`i`** 计入一轮的起点，当且仅当：

- **`messages[i].role == "user"`**，且  
- **`(messages[i].get("_metadata") or {}).get("skill_stack_snapshot")` 为假**

即：**普通 user 消息**开启新轮；带 **`skill_stack_snapshot`** 的 user 不计为新轮（避免把技能栈快照当「一轮」切开）。

---

## 4. 安全下标：`_safe_boundary(stack_top)`

若存在 **`StackFrame`**，**`message_start_idx`** 之前的消息属于当前 scope 前缀，压缩时 **不能破坏**（与技能栈帧对齐）。  
当前 **`api.context_prepare_for_llm`** 构造的 **`ContextEngine`** 调用 **`budget_compact` 时未传入 `stack_top`**，故 **`stack_top is None`** → **`safe = 0`**（见 `budget.py`）。若将来在引擎侧传入 **`stack_top`**，**`safe`** 可大于 0。

---

## 5. Micro：`_micro_compact`

目的：**在「较旧」的轮次里截断过长的 tool 结果**，保留最近若干轮完整。

- 若 **`micro_max_tool_output_chars <= 0`**：直接返回原列表。  
- **`rounds = _round_boundaries(...)`**；若 **`len(rounds) <= micro_preserve_recent_rounds`**：不截断（轮数太少）。  
- **`cutoff`**：保留最近 **`micro_preserve_recent_rounds`** 轮；**`preserve == 0`** 时 cutoff 为 **`len(messages)`**（即所有消息都视为「旧侧」，与注释一致）。  
- 对 **`cutoff <= i < len(messages)`** 且 **`i >= safe`** 且 **`role in ("tool", "tool_result")`** 的字符串 **`content`**，超长则截断并追加 **`[truncated: …]`** 说明。

> **注意**：实现里 **`role == "tool_result"`** 与上游渲染是否一致，以 **`engine.py`** 实际产出的 `role` 为准（常见为 **`tool`**）。

---

## 6. Warm：`_warm_compact`

1. 先 **`_micro_compact`**。  
2. 再用与 micro 类似的 **`cutoff` / `safe`**，对 **旧段**做额外裁剪：  
   - **`assistant`**：内容 **>800** 字符时截到 **400** + `[trimmed: …]`；  
   - **`tool` / `tool_result`**：**>200** 字符时截到 **200** + `[trimmed]`。

---

## 7. Emergency：`_emergency_compact`

1. 把消息拆成 **`system_prefix`**（连续开头的 **`role == "system"`**）与 **`rest`**。  
2. 在 **`rest`** 上算 **`_round_boundaries`**；若 **`len(rounds) > 2`**，则 **`keep_from = max(rounds[-2], safe_in_rest)`**，否则 **`keep_from = 0`**。  
   - 含义：在 **`rest`** 里尽量只保留 **最后约两轮**（**`rounds[-2]`** 起），同时不低于 **`safe_in_rest`**（由 **`stack_top`** 与 system 前缀长度换算）。  
3. 若 **`keep_from > 0`**：插入一条 **system** 说明 **`[Context compacted: … older messages removed …]`**，**`_metadata.origin = "engine"`**、**`compact: "emergency"`**。  
4. 最后再跑一遍 **`_micro_compact`**。

---

## 8. 与 `EngineConfig`、`suggest_compact` 的关系

- **`CompactConfig`**（`types.py`）字段与 **`budget_compact`** 一一对应：`context_window`、`compact_threshold`、`emergency_threshold`、`micro_max_tool_output_chars`、`micro_preserve_recent_rounds` 等。  
- **`EngineConfig`**（`config.py`）里 **`micro_preserve_recent`** 等字段 **语义对应** 预算侧，但 **字段名不完全相同**（`micro_preserve` vs `micro_preserve_recent_rounds`）。  
- **`Cortex.suggest_compact`**（`context_budget.py` + `runtime.py`）用 **`usage_ratio` / `compact_level`** 给 **宿主** 提示档位，**不执行** `budget_compact`；与 [extension-points.md](extension-points.md) 一致。

### 8.1 HTTP `prepare_for_llm` 与 `engine.json`

**`POST /v1/context/prepare_for_llm`**（`api.py` **`context_prepare_for_llm`**）会：

1. **`engine_cfg = await load_engine_config(ws)`** — 读 **`/ro/config/engine.json`**（缺失或坏 JSON 时同 **`load_engine_config`** 既有规则）。  
2. **`compact_cfg = engine_config_to_compact_config(engine_cfg)`** — 见 **`config.py`** 中 **`engine_config_to_compact_config`**（`micro_preserve_recent` → **`micro_preserve_recent_rounds`** 等）。  
3. **`ContextEngine(..., config=compact_cfg)`** — 故 **`budget_compact`** 使用的窗口与阈值与 **`EngineConfig`** 对齐。

仅存在于 **`CompactConfig`** 的项（如 **`nested_skill_fold`**、**`nested_fold_stash_threshold`**）仍取 **`CompactConfig`** 默认值；若将来要可配，需扩展 **`engine.json`** 与映射函数。

---

## 相关

- [context-timeline-and-dfs.md](context-timeline-and-dfs.md) — 时间线渲染  
- [engine-config-and-metrics.md](engine-config-and-metrics.md) — `engine.json`  
- [extension-points.md](extension-points.md) — `suggest_compact`  
