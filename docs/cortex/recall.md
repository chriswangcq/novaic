# Recall：归档 Scope 记忆注入

> 源码：`novaic_cortex/recall.py`（`**Recall**`）。与 `**ContextEngine**` 里 `**meta.recall_messages**` 是**不同入口**，见 §3。

## 1. 职责

在**不展开完整步骤树**的前提下，把**历史上已归档的根 scope** 的 `**summary.md`** 以 **system** 消息形式注入当前上下文，受 **token 预算**约束。

Agent 若要细节，仍可通过工具读 `**/ro/scopes/{id}/steps/`**（见模块 docstring）。

---

## 2. 数据源：全局索引 `/ro/scopes/_index.jsonl`

- `**Recall._load_index()**`：读取 `**/ro/scopes/_index.jsonl**`（JSONL，每行一个对象）。
- 该文件在 `**Workspace.archive_root_scope**` 时由 `**_walk_scope_tree**` 生成多行（根 + 嵌套子 scope 元数据），见 [scope-lifecycle.md](scope-lifecycle.md)。

---

## 3. 选 scope：只要「根」且 depth==0

```python
root_entries = [e for e in index if e.get("depth", 0) == 0]
```

- **子 scope**（`depth > 0`）不单独进 Recall；其内容已随**根**归档在目录树里，或由 **ContextEngine** 在对话时间线里展开。

---

## 4. 选入顺序与 token 策略

1. `**root_entries.reverse()`**：索引文件顺序视为 **旧→新**，反向后按 **新→旧** 迭代。
2. 对每个根：读 `**/ro/scopes/{scope_id}/summary.md`**，拼 `**[Memory: {label}]\n{summary}**`，用 `**token_budget**`（默认 **50_000**，构造参数可改）累加 **估计 token**。
3. **超预算则停止**（优先保留**更近**的根 scope 摘要）。
4. `**selected.reverse()`**：最终返回的 **system** 消息列表为 **时间正序（旧→新）**，叙事自然。

---

## 5. 标签 `_make_label`

- 若索引里 `**name`** 非空且不是通用占位名（如 `session`、`system wake` 等），用 **name**。  
- 否则取 `**summary` 第一行有意义文本**，再否则用 `**scope_id` 前缀**。

---

## 6. 消息形态与元数据

每条消息：

- `**role: system`**
- `**content**`：`[Memory: …]\n…`
- `**_metadata**`：`origin: recall`、`scope_id`、`memory_scope: True`
- `**_message_type**`：`SYSTEM_MESSAGE`

---

## 7. 与 `meta.recall_messages` 的区别


| 机制                                              | 来源                                                | 用途                                                                                                                   |
| ----------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `**Recall.generate_messages()` / `generate()**` | 类 `**Recall**`，读 **全局** `/ro/scopes/_index.jsonl` | 跨会话「长期记忆」摘要条；由 `**Cortex.prepare_system_prompt`**（`runtime.py`）等拉取                                                   |
| `**meta.json` 的 `recall_messages**`             | 存在**当前 scope** 的 `meta`                           | 由 `**ContextEngine.prepare_messages_for_llm`** 在拼时间线**前**插入，带 `_metadata.origin: recall`（无 `memory_scope` 等字段时依实现而定） |


两者可同时存在：前者偏 **系统级拼接**，后者偏 **本会话 meta 里预置的 recall 块**。

---

## 8. HTTP / Runtime

- Registry 按 `**(user_id, agent_id)`** 缓存 `**Recall(workspace, token_budget, token_counter)**`（`registry.py`）。  
- API 暴露 `**GET /v1/recall**`（JWT）及 internal 变体，具体见 `**api.py**`。

---

## 相关文档

- [scope-lifecycle.md](scope-lifecycle.md) — 归档如何写入 `_index.jsonl`  
- [context-timeline-and-dfs.md](context-timeline-and-dfs.md) — 当前轮对话如何拼消息

