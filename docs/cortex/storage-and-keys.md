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

---

## 相关

- [scope-lifecycle.md](scope-lifecycle.md) — 归档时键如何移动  
- [sandbox-shell.md](sandbox-shell.md) — 物化与回写  
