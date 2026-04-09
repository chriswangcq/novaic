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

`**meta.json` 初始字段**（节选）：`name`、`skill`、`start_time`、`phase`（`executing` | `dormant`）、可选 `prev_scope_id`、`wake_triggers`、`handoff_notes`。

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

1. 在 `**/ro/active/{scope_id}/**` 写 `**summary.md**`，更新 `**meta.json**`（`phase=archived`、`ended_at`）。
2. `**_walk_scope_tree(active_path)**`：收集该根下**所有** scope（含嵌套子 scope）的索引行（`scope_id`、`path`、`name`、`depth`、`ts`、可选 `**parent`**）。
3. `**move_prefix**`：把 `agents/.../ro/active/{scope_id}/` **整体**移到 `.../ro/scopes/{scope_id}/`。
4. 修正索引中的 `**path`** 前缀后，**追加**到 `**/ro/scopes/_index.jsonl`**（与 Recall 读取的文件一致）。

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

## 相关文档

- [context-timeline-and-dfs.md](context-timeline-and-dfs.md) — 如何遍历 `_index.jsonl` 生成 LLM 消息  
- [recall.md](recall.md) — 如何用 `/ro/scopes/_index.jsonl` 做记忆注入