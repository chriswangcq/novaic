# 存储抽象与对象键

> 源码：`novaic_cortex/store.py`（**`CortexStore`**）、`s3_store.py`、`registry.py`、`workspace.py` 中的 **`_key`**。

## 1. 设计原则

- **`CortexStore`**：纯 **KV / 对象** 抽象（`put` / `get` / `list_recursive` / `move_prefix` 等），**不知道** scope、agent 等业务概念。
- **`Workspace`**：把 **逻辑路径**（`/ro/...`、`/rw/...`）编成 **store key**；所有 scope 步骤写入走 **`_sys_*`**。

实现类：

| 类 | 用途 |
|----|------|
| **`S3Store`** | 生产：boto3 + 异步线程池 |
| **`MemoryStore`** | 单测（非线程安全说明见 `store.py` 注释） |
| **`LocalFileStore`** | 本地目录 |

---

## 2. 注册表：`WorkspaceRegistry`

- 每个 **`user_id`** 一个 **`S3Store`**，前缀 **`users/{user_id}/`**。
- 每个 **`(user_id, agent_id)`** 缓存一个 **`Workspace(store, agent_id)`**。

---

## 3. 逻辑路径 → 存储键（`Workspace._key`）

`Workspace._key` 只负责 **`agents/{agent_id}/ro/...`** 与 **`agents/{agent_id}/rw/...`**（见 `workspace.py`）。

生产 **`S3Store`** 由 **`WorkspaceRegistry._get_store`** 按用户再加前缀 **`users/{user_id}/`**，因此完整对象键形如：

- **`users/{user_id}/agents/{agent_id}/ro/...`**
- **`users/{user_id}/agents/{agent_id}/rw/...`**

---

## 4. 与 `list_recursive`、归档的关系

- **`archive_root_scope`** 使用 **`move_prefix`** 把  
  `.../ro/active/{scope_id}/` **整体**移到 `.../ro/scopes/{scope_id}/`。
- **Sandbox** 物化时用 **`list_recursive`** 扫 `.../ro/` 与 `.../rw/` 前缀，跳过空 **`.keep`** 占位。

### 4.1 `move_prefix` 原子性契约（P3-9 / INV-7）

S3 没有原生 rename；**`move_prefix`** 是 **逐键 `copy + delete` 循环**。**非原子**，但系统正确性依赖以下三条**同时成立**：

1. **逐键原子（S3 保证）**：每一对 `copy_object` / `delete_object` 要么（a）src 仍在，要么（b）dst 已出现，要么（c）短暂重叠——**不会凭空丢失**；失败重试总能定位到对象。
2. **归档期禁写 src**：**`archive_root_scope`** / **`complete_child_scope`** **先**把 **`meta.phase = "archived"`**，**再** **`move_prefix`**。所有写入（`skill_begin` / `skill_end` / `context_append` / `write_step`）都会检查 `phase == "archived"` **并拒绝**。配合 **`_SCOPE_LOCKS`**（见 **[concurrency-and-locks.md](concurrency-and-locks.md)**）把 phase flip + 移动串到同一把锁里，`list_recursive` 拿到的快照即权威。
3. **幂等重试**：若在第 *i / N* 步崩溃，saga 重放时再列 src 只会看到剩余 *N-i* 个键（已移动的键在 src 已无），继续往下即可。**`/v1/scope/end`** 本身在 P2-4 被实现成幂等（见 **[internal-api-schemas.md](internal-api-schemas.md)**），因此 `wake_finalize → cortex_scope_end` saga 步骤可安全重跑。

**任何改动 `move_prefix` 的硬约束**（源码 docstring 同步）：

- 运行期间 **禁止**对 src 产生写入。
- **禁止**删除调用方 `phase = "archived"` 的先写后移顺序。
- **禁止**改成"先删后拷"——破坏第 1 条。
- 生产桶建议开启 **对象版本控制 / 对象锁**，mid-move 崩溃可审计回滚。

---

## 相关

- [scope-lifecycle.md](scope-lifecycle.md) — 归档时键如何移动  
- [sandbox-shell.md](sandbox-shell.md) — 物化与回写  
