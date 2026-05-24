# LogicalFS 与对象键

> 当前源码：`novaic_cortex/workspace.py`、`novaic_cortex/workspace_authority.py`、`novaic_cortex/registry.py`、`novaic-logicalfs/logicalfs/authority.py`、`novaic-logicalfs/logicalfs/blob_store.py`。

## 1. 当前边界

- **Cortex** 拥有 agent-root、wake、skill、scope、step、payload、context 等语义。
- **LogicalFS** 拥有实时 `/ro` 和 `/rw` 文件语义、路径校验、目录/list/move/read/write 等文件操作。
- **Blob Service** 是 LogicalFS 下方的便宜 byte/object 持久化层，也服务 artifact、display、download 等普通字节流。
- **sandboxd** 只执行进程；它消费 LogicalFS 提供的可执行文件视图，不拥有 workspace/subagent 文件语义。

实现类：

| 类/模块 | 用途 |
| --- | --- |
| `StoreBackedLogicalFileAuthority` | live `/ro` / `/rw` 文件边界 |
| `BlobObjectStore` | LogicalFS 下方的 Blob object adapter |
| `build_workspace_file_authority(...)` | Cortex 侧用 agent 语义创建 LogicalFS authority |
| `Workspace` | Cortex scope/context 语义，依赖 LogicalFS authority 做文件操作 |
| `MemoryStore` / `LocalFileStore` | 测试用 object-store adapter |

## 2. 注册表：`WorkspaceRegistry`

- 每个 `user_id` 缓存一个 LogicalFS object adapter。
- 每个 `(user_id, agent_id)` 缓存一个 `Workspace`。
- Registry 构造链路：

```text
user_id
  -> BlobObjectStore(base_url, tenant_id=user_id)
agent_id
  -> build_workspace_file_authority(object_store, agent_id)
  -> Workspace(authority, agent_id)
```

## 3. 逻辑路径 -> 持久化对象键

LogicalFS authority 负责把逻辑路径映射到 object key：

```text
/ro/active/... -> agents/{agent_id}/ro/active/...
/ro/scopes/... -> agents/{agent_id}/ro/scopes/...
/rw/subagents/{subagent_id}/scratch/... -> agents/{agent_id}/rw/subagents/{subagent_id}/scratch/...
```

Blob Service 决定物理后端是本地磁盘、OSS 还是 S3。这个映射是持久化细节，不是 live `/ro` / `/rw` 权威边界。

`/rw/...` 仍然可以作为 LogicalFS 的一般文件路径映射到底层 object key，
但 Cortex/shell 的默认 scratch 契约是 subagent-aware 的
`/rw/subagents/{subagent_id}/scratch/...`，不是历史 root `/rw/scratch/...`。

## 4. 与 `list_recursive`、归档的关系

- `archive_root_scope` 使用 LogicalFS authority 的 prefix move，把 `/ro/active/{scope_id}/` 移到 `/ro/scopes/{scope_id}/`。
- Sandbox 物化时通过 LogicalFS view 读取 `/ro` 与 `/rw`，执行后只把允许的 `/rw` 变化写回。

### 4.1 `move_prefix` 契约

底层 object adapter 提供 `move_prefix`，语义上等价于对当前 prefix 下的对象做逐 key move。Cortex 的正确性依赖：

1. 归档前先把 scope `phase` 置为 `archived`，所有后续写入拒绝。
2. 归档流程在同一个 scope lock 内完成，避免移动期间写入源 prefix。
3. 失败重试只会继续移动剩余对象；scope end API 自身保持幂等。

## 相关

- [scope-lifecycle.md](scope-lifecycle.md) — 归档时键如何移动
- [sandbox-shell.md](sandbox-shell.md) — 物化与回写
