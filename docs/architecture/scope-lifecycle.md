# Scope & Message Lifecycle

> 这是 PR-20 + PR-21 一起落地之后，"一条消息从用户敲下回车 → 落到某个 Cortex scope 里被消化"的权威生命周期定义。
>
> 历史上这条链每一段都各自维护一份零散状态（`chat_messages.status` / `tq_active_sessions` / `tq_outbox` / `scope.meta` 等），出现卡死时几乎没法在单一查询里把"这条消息现在在哪、谁拿走了它"问出来。PR-21 把消息侧的状态机收拢到一列、PR-20 把消息侧 ↔ scope 侧之间的指针补完整，整条链才第一次具备"无人值守可观测"的能力。

---

## 1. `chat_messages.lifecycle` — 单一权威消息状态机 (PR-21)

`chat_messages` 表新增三列，`lifecycle` 是唯一对外可写的状态字段：

| 列                       | 类型 | 说明                                                                 |
|--------------------------|------|----------------------------------------------------------------------|
| `lifecycle`              | TEXT | 消息当前生命周期。`pending`/`claimed`/`consumed`/`orphaned`/`deduped` |
| `claimed_by_scope`       | TEXT | `lifecycle='claimed'` 时记录把它认领走的 scope_id                     |
| `lifecycle_updated_at`   | INT  | epoch ms。每次 `transition()` 写入                                    |

允许的状态迁移（`Entangled/packages/server-python/entangled/sql/message_state.py::ALLOWED_TRANSITIONS`）：

```
pending  → claimed | deduped
claimed  → consumed | orphaned
orphaned → claimed              (HealthWorker recovery 重新认领)
consumed → ⌀ (terminal — 已经被某个 scope 真正吃掉了)
deduped  → ⌀ (terminal — 幂等键判定为重复，永远不会被分发)
```

### 1.1 唯一写入口

**所有**对 `chat_messages.lifecycle` 的写入都必须经过 Entangled 的 HTTP 入口：

```
POST /v1/messages/{message_id}/transition
{
  "to":       "claimed",
  "scope_id": "scope-xxx",       # 仅 to=claimed 时必填
  "reason":   "subscriber claim"  # 可选，仅日志
}
```

底层调用的是 `entangled.sql.message_state.transition()`，它会：

1. 在一个全局事务里读取当前 lifecycle，校验目标状态在 `ALLOWED_TRANSITIONS[current]` 中；
2. 写入新 lifecycle、`claimed_by_scope`（若适用）、`lifecycle_updated_at`；
3. INFO 级别打一条 `event=message_transition` 日志，带 from/to/scope/reason。

非法迁移抛 `InvalidTransition`（HTTP 409）；找不到消息抛 `MessageNotFound`（HTTP 404）。

### 1.2 CI 守门 (`scripts/ci/lint_lifecycle.sh`)

裸 SQL `UPDATE chat_messages SET lifecycle = ...` 在仓库内会被 ripgrep 扫到并让 lint 失败，仅以下文件在白名单内：

- `Entangled/packages/server-python/entangled/sql/message_state.py`（状态机本身 + `backfill_lifecycle`）
- `Entangled/packages/server-python/entangled/app/message_state.py`（HTTP 入口）
- `Entangled/packages/server-python/tests/`、根 `tests/`、`docs/`（测试 / 文档允许出现样例 SQL）
- `scripts/gateway/`、`scripts/ci/lint_lifecycle.sh` 自身

### 1.3 一次性 backfill

`SqlEntityStore.ensure_schema(MESSAGES_DEF)` 在首次 deploy 后会自动调用 `backfill_lifecycle()`，对所有 `lifecycle='pending' AND (processed=1 OR claimed_by IS NOT NULL)` 的旧行做一次性回填到 `consumed`/`claimed`，**幂等**——后续重启不会重复回填。

---

## 2. `scope.meta.input_message_ids` — Scope ↔ Message 反向索引 (PR-20)

每个 Cortex scope 在创建时会把"是哪些消息触发了我"写进自己的元数据：

```jsonc
// novaic-cortex 中的 scope meta.json
{
  "scope_id": "scope-xxx",
  "input_message_ids": ["msg-aaa", "msg-bbb"],
  ...
}
```

写入方式：`POST /v1/scope/append_input` （Cortex），幂等去重合并。

### 2.1 三种触发路径下的写入责任

| Queue Service action | 谁来写 input_message_ids？                                          |
|----------------------|---------------------------------------------------------------------|
| `saga_started`       | Agent Runtime 的 `handle_session_init`（消息 ID 通过 saga context → session_init payload 流入） |
| `buffered`           | `DispatchSubscriber._try_append_scope_input`（Queue 在 buffered 响应里回带 `scope_id`，Subscriber 拿到后追加） |
| `deduped`            | 跳过（幂等键的胜者已经登记过了，重复写入是 no-op，但会污染指标）   |

Subscriber 这一段是 **soft-fail**：写 Cortex 失败只 WARN，不阻断 outbox 主循环——因为 Cortex 的 `append_input` 本身幂等，HealthWorker recovery 后续仍能重放。

### 2.2 这条链解决的问题

PR-20 之前，`buffered` 分发只回 `{"action": "buffered"}`，Subscriber 拿不到 scope_id；要追问"这条消息到底进了哪个 scope"，需要二次 `GET /api/queue/sessions` 去推断，且推断结果在并发场景下不可信。PR-20 之后：

```
DispatchRequest.message_ids
    ↓
Queue Service tq_active_sessions.metadata
    ↓
saga_context (**metadata spread)
    ↓
session_init payload.message_ids
    ↓
bridge.append_scope_input → Cortex
    ↓
scope.meta.input_message_ids ← 唯一的反向索引来源
```

任何环节断了，PR-26 的孤儿扫描会立刻看到"这条消息 lifecycle=claimed 但找不到对应 scope"，可以单点定位。

---

## 3. 与其它 PR 的关系

- **PR-17 (Dispatch Subscriber)**：物理上把 outbox→queue 的 dispatch 从 `chat_messages` 触发器搬到独立 subprocess。PR-20/21 是它落地后的"装仪表"动作。
- **PR-25 (端到端追踪)**：依赖 PR-20 的 `input_message_ids` 反向索引拼链路图。
- **PR-26 (孤儿扫描)**：依赖 PR-21 的 `lifecycle='claimed'` + `claimed_by_scope` 双字段，扫描"claimed 超过 N 分钟仍未 consumed"的行做兜底告警。
- **PR-19 (HealthWorker recovery-only)**：恢复路径会调用 `transition(to='claimed')`，复用相同入口。
