# 统一时间线与 DFS 上下文拼装

> 源码：`novaic_cortex/context_stack/engine.py`（**`ContextEngine`**）、`context_stack/budget.py`、`context_stack/step_tree.py`。

## 1. 单一数据源：`steps/_index.jsonl`

每个 **scope 目录**（逻辑路径如 `/ro/active/xxx` 或归档后的 `/ro/scopes/xxx`）下有：

- **`meta.json`**：会话级配置（见下）
- **`steps/_index.jsonl`**：按 **seq** 递增的**有序**时间线，每一行一个 JSON 对象，`type` 区分步类型

**`ContextEngine.prepare_messages_for_llm`** 只认这条时间线（外加 `meta` 前缀），不单独扫磁盘猜文件。

---

## 2. `meta.json` 里参与拼装的字段

在遍历 **`_index.jsonl`** 之前，`read_session_meta(scope_path)` 提供：

| 字段 | 作用 |
|------|------|
| **`system_prompt`** | 若有，先追加一条 **`role: system`** |
| **`recall_messages`** | 每条有 `content` 则追加为 system（`_metadata.origin: recall`）；与 **`Recall` 类**全局记忆不同，见 [recall.md](recall.md) |
| **`initial_context`** | 可选多条，按 `role` / `content` 追加（常用于种子 user/system 消息） |

---

## 3. `_index.jsonl` 条目类型与渲染

| `type` | 含义 | 渲染结果 |
|--------|------|----------|
| **`env`** | 环境事件 | 若条目含 **`text`**（如 inline env）→ 一条 **system**；若仅 `subtype` 而无 `text`，由具体子类型决定（`_render_env`） |
| **`assistant`** | 指向 `steps/ast_*.json` | 读 JSON：`content`、`tool_calls`、`reasoning_content` → **assistant** 消息 |
| **`tool`** | 指向 tool 的 JSON 文件 | **tool** 消息，`tool_call_id` + `result` 字符串化 |
| **`scope`** | 子 scope 目录名（`file` 指向 `steps/{dirname}/`） | 见 §4 **DFS** |

文件读取：相对当前 **`self._scope_path`**，路径形如 **`{scope_path}/steps/{filename}`**。

---

## 4. 子 scope：折叠 vs DFS 展开（核心）

对 **`type == "scope"`**，先算子路径：**`child_path = {scope_path}/steps/{scope_dir}`**，再读**子** **`meta.json`**。

### 4.1 已归档子 scope：`meta.phase == "archived"`

- 读 **`summary.md`**（`_read_summary`）。
- 输出**一条** system：  
  `"[Skill '{scope_name}' completed]\n{summary}"`  
- **不递归**进入子树（整段已折叠）。

### 4.2 仍活跃子 scope：其它 `phase`

- 构造**子** **`ContextEngine(scope_path=child_path)`**。
- 调用 **`_render_all_steps()`**：与主流程相同，但**不再**读子树根的 `meta` 里 `system_prompt/recall/initial`（避免重复），只遍历子 **`_index.jsonl`**。
- 在主列表前加**头** system：`[Skill '{name}' active]`，再拼接子消息列表。

因此：**开放子 scope = 深度优先展开**（子树内消息全部插入在父时间线中该 scope 条目所在位置之后，因主循环是顺序遍历 `_index.jsonl`）。

---

## 5. `_render_all_steps` 与 `prepare_messages_for_llm` 的差异

- **`prepare_messages_for_llm`**：包含 **`meta`** 前缀 + 根 scope 的完整 `_index.jsonl` + 最后 **`budget_compact`**。
- **`_render_all_steps`**：仅遍历**当前** scope 的 `_index.jsonl`（供递归子 scope 使用），**无**根 `meta` 前缀、**无** `budget_compact`（压缩只在最外层做一次）。

---

## 6. `budget_compact`（`budget.py`）

在 **`prepare_messages_for_llm`** 末尾对**整条消息列表**调用：

- 根据 **`CompactConfig`**（来自 `EngineConfig` / `context_window`、阈值等）计算 **usage ratio**。
- **紧急 / 温和**两档：可丢弃部分旧消息、截断过长 **tool** 内容等（见 `budget.py` 内 `_emergency_compact` / `_warm_compact` / `_micro_compact`）。

**`ContextEngine.status()`** 可基于已生成消息估算 token 与 `usage_ratio`（供上层 `suggest_compact` 等使用）。

---

## 7. `StepTreeBuilder` / `StepNode`（`step_tree.py`）

- 从索引构建 **树形**结构（tool 叶 / scope 节点），**`render_scope_fold`** 等用于与引擎类似的折叠展示。
- **面向 LLM 的最终消息序列**以 **`engine.py` 时间线遍历为准**；树模块更多用于分析、调试或其它调用路径。

---

## 相关文档

- [scope-lifecycle.md](scope-lifecycle.md) — scope 何时 `archived`、summary 谁写  
- [recall.md](recall.md) — 归档**根** scope 如何进入全局记忆索引  
