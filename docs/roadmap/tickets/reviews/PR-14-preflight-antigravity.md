# PR-14 Preflight Review — Entangled `message_outbox` + co-transaction insert

## §1 核心架构发现：写入路径不在 Entangled 里

Ticket 假设 "消息写入发生在 Entangled 侧"（`entangled/sql/entity_store.py::append`），因此要在 Entangled 的 `append()` 方法里做 co-transaction outbox insert。

但实际数据流是：

```
Business._store_add_message()
  → BusinessEntityStore.append()
    → EntangledServiceClient.append()   ← HTTP POST /v1/entities/messages/append
      → Entangled CRUD handler (crud.py:314)
        → SqlEntityStore.append()       ← 这里才真正 INSERT INTO chat_messages
```

**关键问题：Business 与 Entangled 是两个独立进程**，它们之间走 HTTP。Business 侧完全没有 Entangled 的 `db` 句柄。所以 "co-transaction" 只可能发生在以下两个位置之一：

| 方案 | 位置 | 同事务保证 | 复杂度 |
| --- | --- | --- | --- |
| **A：Entangled 侧** | `SqlEntityStore.append()` 内部，在 `with self.db.transaction()` 块里追加一条 `INSERT INTO message_outbox` | ✅ 原子（同一 SQLite 连接、同一事务） | 低——改 1 个方法 |
| **B：Business 侧** | 在 `_store_add_message()` 之后单独 HTTP 调 Entangled 的新 `/outbox/enqueue` 端点 | ❌ 非原子（两个 HTTP 请求，中间可能崩） | 高——需补偿 |

**结论：必须走方案 A。** 在 Entangled 的 `SqlEntityStore.append()` 中插入 outbox 行。

## §2 `message_outbox` 表的归属

既然 co-transaction 只能在 Entangled 侧做，`message_outbox` 表必须建在 **Entangled 的数据库**（`~/.novaic/data/entangled.db`）中，而不是 Business 自己的 DB。

Schema 创建有两种路径：
1. **schema_push 动态注册**（Business 启动时 POST `/v1/schema/register`）—— 但 `message_outbox` 不是一个常规 entity，不需要 CRUD API、不需要 WS sync。走 schema_push 会污染 entity 注册表。
2. **Entangled 本地启动时 `ensure_schema`**—— 在 Entangled 的 app 初始化阶段用 `db.execute(CREATE TABLE IF NOT EXISTS message_outbox ...)` 建表。这是更合适的做法——outbox 是基础设施表，不是业务 entity。

**推荐方案 2**：在 Entangled `server-python` 启动时、或者在 `SqlEntityStore.__init__` / `ensure_all_schemas` 之后追加一个 `_ensure_outbox_schema()`。

## §3 所有消息写入入口穷举

通过 `rg '_store_add_message'` 穷举了所有消息写入入口（仅 Business 侧，Cortex / Runtime 不写消息）：

| 文件 | 行号 | 消息类型 | 是否触发 wake | 应写 outbox |
| --- | --- | --- | --- | --- |
| `message_actions.py:100` | `send_action` | `USER_MESSAGE` | ✅ 是（当前由 `_dispatch_trigger` 立即触发） | ✅ |
| `internal/message.py:129` | `interrupt_agent` | `INTERRUPT` | ❌ 否（中断动作） | ❌ |
| `internal/message.py:257` | `create_message` | 动态 `data["type"]` | ⚠️ 取决于 type | 仅当 type ∈ {USER_MESSAGE, SUBAGENT_SEND, SPAWN_SUBAGENT} |
| `internal/message.py:336` | `chat_event` | 动态 `event_type` | ⚠️ 取决于 type | 同上 |
| `agent_actions.py:81` | `interrupt_action` | `INTERRUPT` | ❌ 否 | ❌ |

**关键洞察**：outbox 过滤逻辑不应在 Business 侧做（否则非原子）。应该在 Entangled 侧 `append()` 方法内判断：如果 `type` 字段值在 `{"USER_MESSAGE", "SUBAGENT_SEND", "SPAWN_SUBAGENT"}` 中，才追加 outbox 行。

但这引出一个问题：**Entangled 是通用存储引擎，不应该硬编码 NovAIC 的业务类型列表**。

**解决方案**：在 `SqlEntityDef` 的 schema 定义中增加一个可选属性 `outbox_trigger_types: Optional[Set[str]]`。如果此属性存在，`append()` 在写入时检查 `data["type"]` 是否在该集合中，如果在就同事务追加 outbox 行。这保持了 Entangled 的通用性，业务过滤逻辑通过 schema 配置注入。

**或者更简单**：由 Business 在调用 `store.append()` 时传入一个 `outbox_trigger_type: Optional[str]` 参数。非 None 时 Entangled 自动追加 outbox 行。这完全不侵入 schema 定义。

## §4 现有投递语义分析

| 属性 | 当前状态 |
| --- | --- |
| **投递模式** | **Push-based / fire-and-forget**。`message_actions.py:108` 在 `_store_add_message` 后立即 `await _dispatch_trigger()`，不管 dispatch 结果。 |
| **保证** | **At-most-once**。如果 `_dispatch_trigger` 崩溃或被 400（如 PR-12 发现的 user_id 空置），消息永远不会被处理。HealthWorker 兜底是事后补救，不是承诺。 |
| **幂等** | 依赖 Queue 的 `idempotency_key` 做去重（PR-10 追加）。但 `_dispatch_trigger` 当前不传 `idempotency_key`（PR-11 实现中只传了 `message_ids`，没设 key）。 |
| **Outbox 模式** | **不存在**。没有任何 outbox 表、WAL 消费、或 changefeed 机制。 |
| **Exactly-once** | 不存在。at-most-once（上游）× 依赖 Queue 去重（下游）= 最多一次。 |

**PR-14 引入 outbox 后的目标语义**：
- 写消息 + 写 outbox = 同一 SQLite 事务 → **at-least-once enqueue 保证**
- PR-16 的 subscriber poll + dispatch + mark delivered → **at-least-once delivery**
- Queue 端 `idempotency_key` 做最终去重 → **exactly-once effect**

## §5 Entangled `append()` 的修改点

当前 `SqlEntityStore.append()` 的事务块（`entity_store.py:513-517`）：

```python
with self.db.transaction(defn.lock_type, resource_id=lock_id):
    cur = self.db.execute(sql, tuple(row[c] for c in cols))
    if is_auto_int and cur.lastrowid:
        row[defn.id_field] = cur.lastrowid
        res_id = str(cur.lastrowid)
```

**修改方案**：在该 `with` 块内追加 outbox insert：

```python
with self.db.transaction(defn.lock_type, resource_id=lock_id):
    cur = self.db.execute(sql, tuple(row[c] for c in cols))
    if is_auto_int and cur.lastrowid:
        row[defn.id_field] = cur.lastrowid
        res_id = str(cur.lastrowid)
    # Co-transaction outbox insert
    if hasattr(defn, 'outbox_trigger_types') and defn.outbox_trigger_types:
        msg_type = row.get("type", "")
        if msg_type in defn.outbox_trigger_types:
            import time, json
            self.db.execute("""
                INSERT INTO message_outbox (message_id, agent_id, trigger_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO NOTHING
            """, (
                str(row.get(defn.id_field, res_id)),
                row.get("agent_id", ""),
                defn.outbox_trigger_types.get(msg_type, msg_type),  # map → TriggerType.value
                json.dumps({"message_ids": [str(row.get(defn.id_field, res_id))]}),
                int(time.time() * 1000),
            ))
```

## §6 file:line 修改清单

| 文件 | 行号 | 动作 |
| --- | --- | --- |
| `Entangled/.../entity_store.py` | 513-517 | 在 `with self.db.transaction` 块内追加 outbox INSERT（§5） |
| `Entangled/.../entity_store.py` | 新 | 新增 `_ensure_outbox_schema()` 方法 |
| `Entangled/.../app/state.py` 或启动入口 | | 调用 `_ensure_outbox_schema()` |
| `novaic-business/business/schema_push.py` | 404-429 `MESSAGES_DEF` | 如果采用 `outbox_trigger_types` 方案，在 `SqlEntityDef` 构造中传入 trigger mapping |
| `Entangled/.../sql/entity_def.py` | | `SqlEntityDef` 增加 `outbox_trigger_types: Optional[Dict[str, str]]` 属性 |

## §7 本 PR 不做的事

- ❌ 不实现消费（subscriber 是 PR-15/PR-16）
- ❌ 不删除 `_dispatch_trigger`（那是 PR-18）
- ❌ outbox 行会积累（`delivered_at` 恒 NULL），这是预期行为
- ❌ metrics（PR-14 scope 只含写入侧）

## §8 SQLite `RETURNING` 兼容性

本机 SQLite 版本 3.50.4，`RETURNING` 从 3.35 开始支持 → OK（PR-16 的 claim 逻辑会用到）。

## §9 测试计划

1. **单测**（Entangled 侧，用内存 SQLite）：
   - 写 `USER_MESSAGE` → `chat_messages` + `message_outbox` 各一行
   - 写 `ASSISTANT_MESSAGE` → `chat_messages` 一行，outbox 无变化
   - 并发写 100 条 → outbox 100 行（`UNIQUE ON message_id` 保护）
2. **集成测试**（本地端到端）：
   - 发 `hihi` → `SELECT * FROM message_outbox WHERE delivered_at IS NULL` 有 1 行

## §10 风险与决策点

1. **Entangled 耦合**：在通用存储引擎里加 outbox 逻辑可能被认为"侵入性过高"。但由于 co-transaction 是硬约束（§1），没有更好的位置。通过 `outbox_trigger_types` 属性做可选注入可以将侵入降到最低。
2. **重复写 outbox vs 直接 dispatch**：PR-14 合并后，`_dispatch_trigger` 仍然存在。这意味着同一条消息既走了 outbox（积累），又走了直接 dispatch（PR-11 的 fire-and-forget）。两条路径共存是 Phase 2 的过渡态，PR-17（canary flag 切换）和 PR-18（删除旧路径）会收束它们。
