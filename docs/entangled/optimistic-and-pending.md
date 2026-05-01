# 历史：乐观并发与 Pending Ops

> 这页是历史说明，避免排障时把旧 Path B / 早期 Path C 机制误认为当前活路径。

## 当前结论

当前 `novaic-app` 的 Entangled 写入路径是 **pessimistic-first**：

1. React 调用 `dispatch()` / `entangledMethod()`。
2. Rust 通过 `entangled_method` 发送服务端 action / entity mutation。
3. 服务端确认写入后，Entangled sync 帧把结果推回本地 SQLite read-model。

客户端 `entangled_cache.db` 当前只维护：

```text
entity_meta
entity_items
idx_entity_items_seq
```

`pending_ops` 不再是活跃表。Rust cache 初始化时会执行：

```sql
DROP TABLE IF EXISTS pending_ops;
```

所以遇到 App 缓存问题时，不要再假设有客户端离线写队列或 pending-op 重放机制。

## 历史机制

早期设计曾考虑或实现过 `_opt_*` 临时行与 `pending_ops` 表，用于弱网下的 optimistic UI。那一路径已经退出活代码：当前 `novaic-app/src/data/entangled/dispatch.ts` 明确是 pessimistic-first，乐观 UI 若需要应在更上层用 TanStack Query `onMutate/onError/onSettled` 这类展示层机制实现，而不是依赖 Rust cache 写队列。

## 当前排障命令

```bash
sqlite3 "$HOME/Library/Application Support/com.novaic.app/entangled_cache.db" ".tables"
sqlite3 "$HOME/Library/Application Support/com.novaic.app/entangled_cache.db" \
  "SELECT entity, params_hash, version, subscribed, has_more FROM entity_meta ORDER BY entity"
```

执行日志相关约定：

- `messages` / `execution-logs` 是 Entangled stream read-model；
- `log-payloads` 通过 action lazy fetch，不默认订阅；
- 工具长结果走 Cortex step；
- 原始 LLM 调用走 LLM Factory，Entangled 中只需要 join key。
