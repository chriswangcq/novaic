# Entangled WebSocket 同步协议 v1

> 阶段 1 交付物。与运行时实现对齐：`Entangled/packages/server-python`、`Entangled/packages/client-rust`、`novaic-app` AppBridge。  
> **向后兼容**：新字段可被旧客户端忽略；旧服务端缺字段时客户端使用 [entangled-pk-conventions.md](./entangled-pk-conventions.md) 中的回退规则。

---

## 1. 传输载体

- 桌面：**同一条** AppBridge WebSocket（如 `/api/app/ws`）上 `type: "sync"` 的 JSON 对象。
- 帧级字段使用 **camelCase**（如 `idField`、`baseVersion`）。

---

## 2. Sync 帧通用字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `"sync"` | 固定 |
| `entity` | string | 实体名，如 `messages` |
| `params` | object \| null | 作用域参数（如 `{"agent_id":"..."}`），空订阅为 `null` |
| `mode` | string | `snapshot` \| `head_n` \| `delta` \| `up_to_date` |
| `version` | number | 服务端当前该 `(entity, params)` 状态版本 |
| **`idField`** | string | **必选（v1 推荐）**：JSON 行主键字段名，如 `id`、`model_id`。subscribe 首帧与 **delta 帧均应携带**（见 §6）。 |

### 2.1 按 mode 的附加字段

| mode | 附加字段 |
|------|-----------|
| `snapshot` | `data`: 行数组 |
| `head_n` | `data`: 行数组，`hasMore`: boolean |
| `delta` | `baseVersion`: number，`ops`: 操作数组 |
| `up_to_date` | 无额外负载 |

### 2.2 可选字段（占位 — 阶段 A.1）

| 字段 | 类型 | 说明 |
|------|------|------|
| `resyncReason` | string | 服务端主动提示「整段重同步」原因时携带（如 `op_log_gap`、`invalidate`）。**v1 实现可不发送**；客户端应忽略未知值。 |

---

## 3. 操作对象 `SyncOp`（delta 内 `ops[]`）

JSON 形态（camelCase 别名由服务端序列化决定，客户端 `SyncOp` 已对齐）：

| 字段 | 说明 |
|------|------|
| `version` | 该 op 对应版本 |
| `op` | `insert` \| `update` \| `delete` \| `invalidate` |
| `id` | **实体主键的字符串形式**（与 `idField` 所指列语义一致，非一定 JSON 键名 `id`） |
| `data` | 可选，insert/update 的合并载荷 |
| `ts` | 时间戳 |
| `requestId` | 可选，与乐观写关联 |

---

## 4. 客户端处理顺序（Rust `process_sync`）

1. 解析帧；`idField` 缺失时使用 `default_id_field_for_entity(entity)`。
2. `snapshot` / `head_n`：按 `idField` + `item_id_string` 落 SQLite。
3. `delta`：`apply_delta`（`op.id` 已为字符串）。
4. **`up_to_date`**：将本地 `entity_meta.version` **对齐为帧内 `version`**（避免仅内存一致而持久化版本落后）。不触发强制 UI 失效时可不发 `entities_changed`（当前实现返回 `None`）。

---

## 5. subscribe 首帧

由 `ws_handler._subscribe_one` 发送，含完整 `idField` 与 `resolve_sync` 结果。

---

## 6. 推送 delta（notifier）

- **变更推送**：`notify_entity_change` 下发的 delta 帧 **必须包含** 与首帧相同的 `idField`（取自 `EntityDef`，缺省 `id`）。
- **级联 invalidate**：对 `rel.target` 实体使用 **目标实体** 的 `idField`。

---

## 7. Schema 推送（可选消费）

`to_schema_dict()` 含 **`idField`** 时，客户端可在订阅前获知主键字段（与 [entangled-pk-conventions.md](./entangled-pk-conventions.md) 一致）。

---

## 8. Params 规范化

跨语言 `(entity, params)` 分区须一致，见 [entangled-params-canonical.md](./entangled-params-canonical.md)。

---

## 9. Stream / op-log 缺口（阶段 1.7 — **v1 选定语义 B**）

当客户端持有的 `baseVersion` 与服务端 op-log 窗口**无法衔接**（例如离线过久、服务端轮换日志）时，Gateway 对 **stream** 实体走 `resolve_sync` 的 **head_n 重同步**（见 Python `[Entangled] stream op-log gap` 日志）；**list** 实体可走全量 `snapshot`。

**v1 客户端（Rust `apply_snapshot`）**：对给定 `(entity, params)` 执行 **`DELETE` 再写入本帧 `data`**，即 **整分区 head 数据被替换**；此前通过 `load_more` / `prepend_older` 落在本地的更老行**不会保留**（与语义 **B** 一致）。

| 语义 | 行为 | v1 |
|------|------|-----|
| **A** | 仅替换 head 窗口，保留更老 prepend 页 | **未实现**（后续若要做需改 `apply_snapshot` / 元数据策略） |
| **B** | 整 key 重置 head（丢弃本地 prepend 与旧 head 行） | **是** |

可选字段命名见 **§2.2 `resyncReason`**；当前以 `mode` + 日志为准即可。

---

## 10. 修订历史

| 日期 | 说明 |
|------|------|
| 2026-04-01 | v1：delta/schema 补 `idField` 约定；`up_to_date` 版本对齐 |
| 2026-04-01 | §9：stream / op-log 缺口语义备忘（1.7） |
| 2026-04-01 | §9：明确 v1 = 语义 B（`apply_snapshot` 全量替换 head 分区） |
| 2026-04-01 | §2.2：`resyncReason` 可选字段占位（A.1） |
