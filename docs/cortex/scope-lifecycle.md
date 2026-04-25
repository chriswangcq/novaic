# Scope 生命周期与存储布局

> 源码：`novaic_cortex/workspace.py`（`Workspace`）。Cortex 内部写路径一律走 `**_sys_***`，不经过 Agent 的 `/rw` ACL。

## 1. 逻辑路径总览


| 区域                        | 用途                                                                          |
| ------------------------- | --------------------------------------------------------------------------- |
| `/ro/active/{scope_id}/`  | **根 scope** 活跃时驻留于此（`phase` 为 `executing` 或 `dormant`）                      |
| `/ro/scopes/{scope_id}/`  | **根 scope 归档后**整树移动到此                                                       |
| `/ro/scopes/_index.jsonl` | **全局**归档 scope 索引（供 **Recall** 使用，见 [recall.md](recall.md)）                 |
| `{任意 scope}/steps/`       | 统一时间线：`_index.jsonl` + `env_*.json` / `ast_*.json` / tool JSON / 子 scope 目录 |


子 scope **嵌套**在父 scope 的 `steps/` 下，目录名形如 `**{seq:04d}_scope_{scope_id}/`**。

---

## 2. 创建 scope：`create_scope`

- `**parent_path is None**`：在 `**/ro/active/{scope_id}/**` 建**根** scope（新会话根或待机根）。
- `**parent_path` 给定**：在父的 `**steps/`** 下建子目录；父的 `**steps/_index.jsonl**` 追加一行 `**type: "scope"**`，指向子目录。

`**meta.json` 初始字段**（节选）：`name`、`skill`、`start_time`、`phase`（`executing` | `dormant`）、可选 `prev_scope_id`、`wake_triggers`。

> 2026-04-23 (PR-55)：`handoff_notes` 字段已从 R9 wake-continuity 链路中移除（见
> [`docs/roadmap/tickets/PR-55-phantom-summary-pipeline-cleanup.md`](../roadmap/tickets/PR-55-phantom-summary-pipeline-cleanup.md)）。
> `api.py` 若仍容忍该字段，当前 runtime / business 已不再传递；历史 meta.json 可能含有遗留值，不影响读出。

- `**phase == "dormant"`**：会写一条 `**env` / `scope_dormant**` 到子 scope 的 `_index.jsonl`，表示待机。

---

## 3. 激活待机 scope：`activate_scope`

- 仅当 `**phase == "dormant"**` 时可转为 `**executing**`（幂等：已是 `executing` 则直接返回）。
- 更新 `**meta.json**`，并在 `**_index.jsonl**` 追加 `**scope_activate**`；可选追加 `**wake_notification**` 文本（`env` 条目）。

---

## 4. 子 scope 结束：`complete_child_scope`

- 子 scope **仍嵌在父 `steps/` 下**（未单独移到 `/ro/scopes`）。
- 写入 `**summary.md`**，`**meta.phase = "archived"**`，`**ended_at**`。
- **根 scope 日后归档**时，`**_walk_scope_tree`** 会把子树一并索引进 `**/ro/scopes/_index.jsonl**`。

---

## 5. 根 scope 归档：`archive_root_scope`

1. **`_auto_close_open_children(active_path)`**：DFS 关闭所有仍 `phase != archived` 的子 scope（写 `summary.md = "[auto-closed on rest: scope left open by agent]"`、`phase = archived`、`ended_at`）。保证归档后整棵树 phase 一致，不会把「还在 open 的 Meta / skill」随 root 一起冻进只读区。
2. 在 `**/ro/active/{scope_id}/**` 写 `**summary.md**`，更新 `**meta.json**`（`phase=archived`、`ended_at`）。
3. `**_walk_scope_tree(active_path)**`：收集该根下**所有** scope（含嵌套子 scope）的索引行（`scope_id`、`path`、`name`、`depth`、`ts`、可选 `**parent`**）。
4. `**move_prefix**`：把 `agents/.../ro/active/{scope_id}/` **整体**移到 `.../ro/scopes/{scope_id}/`。
5. 修正索引中的 `**path`** 前缀后，**追加**到 `**/ro/scopes/_index.jsonl`**（与 Recall 读取的文件一致）。
6. API 层 `/v1/scope/end` 在 `is_root=true` 归档后还会调 `_drop_skill_lock` 回收 `_SKILL_LOCKS` 里对应 `(user_id, agent_id, scope_id)` 的互斥锁条目。

> 2026-04-25 (PR-56 / PR-58)：根 scope 的 `summary` 参数有**两层来源**，按优先级解析（`api.py::_scope_end`）：
> 1. **Tier 1 — LLM 显式写**：根级 `skill_end(report="...")` 走 `_context_skill_end_locked`，把 report 暂存到 `meta.pending_rest_summary`；归档时该字段 winning。这是"agent 主动写 turn recap"的官方通路（参考 `tool_schemas.py::skill_end` description 中的 Pattern B / continuity protocol）。
> 2. **Tier 2 — saga 自动派生**：若 LLM 没在 root 层显式调 `skill_end`（实际线上多数情况），`react_actions._extract_rest_summary` 会从最后一条 `chat_reply.message` 抠 1–3 句、套字节 cap，由 `subagent_rest._build_cortex_scope_end_payload` 作为 `report` 传进来。
> 3. 两者都没有 → 写空字符串（与 PR-55 删 phantom `generate_simple_summary` 之后的语义一致）。
>
> 写入的 `summary.md` 既被 `<PREV_SCOPE_TAIL>` 渲染近邻 turn，也被新的 `<PREV_SCOPE_HISTORY>` 块（PR-57）取作 K 个 root 的 rolling history（见 [§10](#10-跨-root-rolling-summary-history)）。

---

## 6. 原子「结束当前根 + 建新待机根」：`scope_end_and_spawn`

用于一轮对话结束、进入待机：

1. 对当前 `**/ro/active/{scope_id}**` 读 `**_index.jsonl**` 与 `**meta**`，用 `**generate_combined_summary**` 生成最终 `**summary**`。
2. 调用 `**archive_root_scope(scope_id, summary)**`。
3. `**create_scope**` 新建 `**phase=dormant**` 的根 scope（新 `scope_id`，`prev_scope_id` 指向旧根等）。

返回 `**archived_scope_id`、`archive_path`、`new_scope_id`、`new_scope_path**`。

---

## 7. 统一时间线写入（与 ContextEngine 对齐）

与 `**steps/_index.jsonl**` 强相关的方法：


| 方法                                          | 作用                                   |
| ------------------------------------------- | ------------------------------------ |
| `**write_env**`                             | `env_*.json` + 索引行（用户消息、唤醒、标记等）      |
| `**write_assistant**`                       | `ast_*.json` + 索引行 `type: assistant` |
| `**write_inline_env**`                      | 仅索引行、无独立文件（轻量 marker，如 skill 相关）     |
| `**write_step**`                            | tool 类 JSON 文件 + 索引行 `type: tool`    |
| `**read_step_index` / `read_session_meta**` | ContextEngine 读取入口                   |


**子 scope 作为一步**：只在父 scope 的索引里出现 `**type: scope`**；子树内再有各自的 `_index.jsonl`。

---

## 8. 查询辅助

- `**find_active_root_scope**`：从 `**list_active_scopes()**` 取第一个根（待机或执行中）。
- `**resolve_active_scope_path**`（见 workspace 其它方法）：解析「当前最深活跃 scope」供工具路由（与 Agent Runtime 约定一致）。

---

## 9. Skill scope 生命周期（LLM 可见、栈式）

> 源码：**`api.py`** 内 **`/v1/context/skill_begin` / `/v1/context/skill_end`**；工具 schema 在 **`tool_schemas.py`**；Runtime 侧桥接在 `cortex_bridge.py`、`handlers/cortex_handlers.py`、`handlers/tool_handlers.py`。

Skill scope 是 LLM 通过两个工具 **`skill_begin` / `skill_end`** 管理的**嵌套子 scope**；每一层都是父 scope `steps/` 下的一个目录（§1），并遵循以下规则：

### 9.1 显式 ID + 全局唯一

- **调用 `skill_begin(scope_id=..., name=..., task?)` 必须由 LLM 指定 `scope_id`**（在工具参数里叫 `scope_id`，到 Cortex HTTP 叫 `child_scope_id`）。
- 该 id 需在**此会话的整棵 scope 树**（包括已归档子孙）中**从未出现过**；Cortex 调 **`_walk_scope_tree(root_scope_path)`** 收集所有节点的 `scope_id` 做校验，冲突返回 `{ok: false, error: "scope_id '...' already used ..."}`。
- 根 scope 的 `scope_id` 由系统生成（会话创建时）；**只有子 skill scope 由 LLM 命名**。

### 9.2 严格 LIFO 关闭

- `skill_end(scope_id=..., report=...)` 的 `scope_id` 必须等于**当前最内层**活跃 scope（通过 **`resolve_active_scope_path`** 解析）。
- 不匹配则返回 `{ok: false, error: "scope_id mismatch ... current stack top is '...'", stack_top: "..."}`，不修改任何状态。
- 匹配则调 **`complete_child_scope(active_path, report)`**（§4）把该子 scope 设为 `archived` 并写 `summary.md`。
- **返回体包含栈状态**：`skill_begin` / `skill_end` 的 ok 与 error 响应都会带 `stack`（LIFO 帧数组，栈顶最先，元素为 `{depth, scope_id, skill_name}`）和 `stack_depth`，让 LLM 能直接在工具结果里看到最新栈形。

### 9.3 Meta skill 自底托盘

- `subagent_wake` saga 在 `session_init` 之后、`set_subagent_awake` 之前，会自动通过 **`TaskTopics.CORTEX_SKILL_BEGIN`** 开一个 **`scope_id = meta-<root_scope_id>`、`name = meta`** 的 skill scope（**`_build_auto_meta_skill_payload`**）。
- 该步骤**必需**（非 `optional`）：Cortex 返回 `ok: False` 或抛异常都会使 `handle_cortex_skill_begin` raise，wake saga 整体失败而不是静默降级到「栈空 → 立刻 rest」。
- 对应地，`/api/queue/dispatch` 入口**要求 `user_id` 必填**（Cortex skill_begin 没有 user_id 会校验失败）。
- 这样 LLM 醒来时栈**永远非空**（至少 1 层 Meta），使得「栈空 ⇔ 真的没事做了 ⇔ 自动休息」这个判据可靠。
- 若 LLM 主动 `skill_end` Meta，则 **`react_actions`** 下一步的 **`decide_rest`** 会走 rest 路径（见 [agent-runtime-all-topics.md](agent-runtime-all-topics.md) §3）。

### 9.4 并发安全

- `POST /v1/context/skill_begin` 与 `POST /v1/context/skill_end` 在 API 层以 `(user_id, agent_id, root_scope_id)` 为 key 使用 `asyncio.Lock` 串行化（`_SKILL_LOCKS`），避免同一 round 内并发 tool_calls 同时操作栈时 `resolve_active_scope_path` 读到过期 top。
- 锁条目在 root scope 归档时自动回收（见 §5 第 6 点）。

### 9.4 LLM 上下文中的栈快照（瞬态）

- 每轮 **`cortex.prepare_llm_context`** 在消息末尾会追加一条**瞬态** system 消息，形如：
  ```text
  [Active skill stack (LIFO — close innermost first)]
    depth 0: meta (scope_id=meta-abc123)
    depth 1: debugging (scope_id=debug-1)
  → Stack top: scope_id=debug-1 (skill=debugging). To pop this skill call: skill_end(scope_id='debug-1', report='...')
  ```
- 数据来自 **`ContextEngine.status(...).frames`** —— 每帧 `{depth, skill_name, scope_id}`，由 `_extract_stack_info` 遍历 Step Tree 所有 `is_scope and not closed` 节点构造。
- 该提示**不写入 `context.jsonl`**，每轮重新生成（见 [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md) §4）。

### 9.5 与 Step Tree 折叠的关系

- 已 `skill_end` 的子 scope 在下一轮 `prepare_for_llm` 会被 **`_merge_context_and_steps`** 折叠成一条  
  `"[Skill '{scope_name}' completed]\n{summary}"` system 消息（`summary = skill_end.report`）。
- 还处于 `executing` 的 skill 则在 LLM 上下文里按原样保留，对应 `frames` 中那一帧。

---

## 10. 跨 root rolling summary history

> 2026-04-25 (PR-57)：源码 `novaic_cortex/workspace.py::list_archived_root_summaries` + `api.py::POST /v1/scope/list_summaries`；Runtime 注入端 `task_queue/handlers/runtime_handlers.py::_build_prev_scope_summary_messages`。

`<PREV_SCOPE_TAIL>` 只能续到上一 turn 末尾，不够覆盖"前几 turn 在干啥"。Cortex 提供 K 个最近 root summary 的批量读出：

1. `Workspace.list_archived_root_summaries(limit=K, exclude_scope_ids=[...])`：读 `/ro/scopes/_index.jsonl`，过滤 `depth==0` 行 → 按 `scope_id` 去重保留最新 `ts` → 按时间从老到新排序 → 取最后 `limit` 条 → 回填每条的 `summary.md`（空也保留，由调用方决定要不要丢弃）。
2. API 层 `POST /v1/scope/list_summaries` 是同名 RPC；响应 `{summaries: [{scope_id, summary, archived_at, depth}, ...]}`。
3. Runtime `handle_session_init` 在 trigger message 之前注入一条 `<PREV_SCOPE_HISTORY>` system 消息：渲染每条 `archived_at`（ISO 时间）+ `summary` 文本，整块带字节 cap（`WAKE_PREV_SCOPE_SUMMARY_MAX_BYTES`，默认 16 KB）；条数由 `WAKE_PREV_SCOPE_HISTORY_COUNT` 控制（默认 5）。
4. **PR-58 修正**：原版默认 `exclude_scope_ids=[previous_scope_id]`，结果"上一 turn"会被同时存在的 `<PREV_SCOPE_TAIL>` 和 history 之间双扣空，改为 `exclude_scope_ids=[]`，让 history 自然包含最新一条；尾部的近邻细节交给 `<PREV_SCOPE_TAIL>`，两边职责并存不互斥。

观测：`wake_continuity_render_total{layer="state", result=...}`（PR-54）汇总两块 state 层的 render 健康。

---

## 相关文档

- [context-timeline-and-dfs.md](context-timeline-and-dfs.md) — 如何遍历 `_index.jsonl` 生成 LLM 消息  
- [recall.md](recall.md) — 如何用 `/ro/scopes/_index.jsonl` 做记忆注入  
- [agent-runtime-all-topics.md](agent-runtime-all-topics.md) — `react_actions` 的 `check_skill_stack` / `decide_rest` 与 `subagent_wake` 的 `auto_meta_skill`  
- [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md) — `[Active skill stack]` 瞬态注入