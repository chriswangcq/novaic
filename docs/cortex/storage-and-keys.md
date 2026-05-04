# 存储抽象与对象键

> 源码：`novaic_cortex/store.py`（`CortexStore`）、`blob_store.py`、`registry.py`、`workspace.py` 中的 `_key`。

## 1. 设计原则

- `CortexStore`：纯 KV / 对象抽象（`put` / `get` / `list_recursive` / `move_prefix` 等），不知道 scope、agent 等业务概念。
- `Workspace`：把逻辑路径（`/ro/...`、`/rw/...`）编码成 store key；所有 scope 步骤写入走 `_sys_*`。
- `BlobCortexStore`：生产主路径。Cortex 通过 Blob Service object API 读写对象；Cortex 不持有 OSS/S3 AK/SK、bucket 或 endpoint。

实现类：

| 类 | 用途 |
|----|------|
| `BlobCortexStore` | 生产：HTTP 调 Blob Service object API |
| `MemoryStore` | 单测（非线程安全说明见 `store.py` 注释） |
| `LocalFileStore` | 本地目录测试 |

---

## 2. 注册表：`WorkspaceRegistry`

- 每个 `user_id` 一个 `BlobCortexStore(tenant_id=user_id)`。
- 每个 `(user_id, agent_id)` 缓存一个 `Workspace(store, agent_id)`。
- Blob Service 决定物理后端是 OSS/S3 还是本地磁盘；Cortex 只知道 Blob Service URL。

---

## 3. 逻辑路径 → 存储键

`Workspace._key` 只负责 `agents/{agent_id}/ro/...` 与 `agents/{agent_id}/rw/...`。

在生产中，对象会以：

```text
tenant_id = {user_id}
namespace = cortex-store
key       = agents/{agent_id}/ro/...
key       = agents/{agent_id}/rw/...
```

写入 Blob Service。Blob Service 再把 `(tenant_id, namespace, key)` 映射到其配置的物理 byte/object 后端。

---

## 4. 与 `list_recursive`、归档的关系

- `archive_root_scope` 使用 `move_prefix` 把 `.../ro/active/{scope_id}/` 整体移到 `.../ro/scopes/{scope_id}/`。
- Sandbox 物化时用 `list_recursive` 扫 `.../ro/` 与 `.../rw/` 前缀，跳过空 `.keep` 占位。

### 4.1 `move_prefix` 契约

Blob Service object API 提供 `move_prefix`，语义上等价于对当前 prefix 下的对象做逐 key move。Cortex 的正确性依赖：

1. 归档前先把 scope `phase` 置为 `archived`，所有后续写入拒绝。
2. 归档流程在同一个 scope lock 内完成，避免移动期间写入源 prefix。
3. 失败重试只会继续移动剩余对象；scope end API 自身保持幂等。

---

## 相关

- [scope-lifecycle.md](scope-lifecycle.md) — 归档时键如何移动
- [sandbox-shell.md](sandbox-shell.md) — 物化与回写
