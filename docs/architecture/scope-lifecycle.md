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

- `Entangled/packages/server-python/entangled/sql/message_state.py`（状态机本身）
- `Entangled/packages/server-python/entangled/app/message_state.py`（HTTP 入口）
- `Entangled/packages/server-python/tests/`、根 `tests/`、`docs/`（测试 / 文档允许出现样例 SQL）
- `scripts/gateway/`、`scripts/ci/lint_lifecycle.sh` 自身

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

## 3. PR-22 / PR-23 — 让状态机真正起效

PR-21 只搭好了状态机的骨架（枚举 + transition 入口 + CI 守门）。**真正让流量里的每条消息走完 `pending → claimed → consumed` 这条主干**的动作分两步：

### 3.1 PR-22 — `dispatch_ok → claimed`

**写入者**：`DispatchSubscriber._try_transition_claimed`
（`novaic-business/business/subscribers/dispatch_subscriber.py`）

subscriber 成功把一条 outbox 行 dispatch 给 Queue 后，拿着 Queue 返回的 `result.scope_id` 调：

```
POST /v1/messages/{message_id}/transition
{"to": "claimed", "scope_id": "<scope>", "reason": "subscriber_dispatch:saga_started"}
```

三种 Queue action 的处理：

| action         | transition 行为 |
|----------------|----------------|
| `saga_started` | claim 到新 saga 的 scope_id |
| `buffered`     | claim 到已 active 的 scope_id（PR-20 起 buffered 也回带 scope_id） |
| `deduped`      | 不 transition——幂等键的胜者已经 claim 过 |

**软失败策略**：
- 409 (InvalidTransition) → INFO 日志，继续走。通常是 HealthWorker recovery 或前一次重试已经 claim 了。
- 404 (MessageNotFound) → WARN 日志。这条 message 被外部删掉了。
- 网络 / 5xx → WARN 日志。outbox 已标记 delivered，dispatch 本身是成功的；孤儿扫描（PR-26）会用 `delivered_at IS NOT NULL AND lifecycle='pending'` 的 join 兜底。

### 3.2 PR-23 — `scope_end → consumed`

**写入者**：`handle_cortex_scope_end` → `BusinessClient.bulk_transition_messages`
（`novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`）

scope 成功归档（`/ro/scopes/`）后，把它的 `input_message_ids` 批量 transition 到 `consumed`：

```
POST /internal/messages/bulk-transition                  ← Business 代理入口
{"message_ids": [...], "to": "consumed", "scope_id": "<scope>", "reason": "scope_end"}
```

Business 端 fan-out 到 Entangled 的单条 transition 入口，每条失败独立记录 (`results[i].error`)，不整体失败。

**时序要点（严格遵守）**：

1. **archive 之前**快照 `scope.meta.input_message_ids` —— archive 可能移动 scope 目录。
2. **archive 之后**才 transition —— 如果 archive 自己失败了，让消息停在 `claimed`，recovery（PR-26）才能决定怎么处理。
3. bulk-transition 整体 **soft-fail** —— 归档已经成功，丢一条 consumed trace 好过重跑 saga 让归档再发生一次。

### 3.3 `transition(to == current)` 幂等 no-op（PR-23）

PR-22 和 PR-23 都会被重试（outbox redelivery / saga re-entry）。如果 `transition()` 对"当前状态 == 目标状态"抛 `InvalidTransition`，所有调用点都得包 `try/except InvalidTransition/pass`。

所以 `transition()` 内部把 self-loop 改成 **no-op**：不写 DB、不 bump `lifecycle_updated_at`，返回 `{"noop": true, ...}`。`ALLOWED_TRANSITIONS` 表仍然会拒绝真正非法的迁移（比如 `consumed → claimed`），只是"已经在终态再调一次"不当错误。

### 3.4 PR-52 — subscriber 重试路径的 scope-aliveness 护栏

**写入者 / 读取者**：`DispatchSubscriber._check_stale_claim`
（`novaic-business/business/subscribers/dispatch_subscriber.py`）

PR-51 Part 1 踩到的坑：subscriber 重启触发 outbox 的 retry claim → 一条 `pending` 的 USER_MESSAGE 被 dispatch 给一个**全新**的 Queue session → 拉起新 scope → 老 scope 早已 archived，两头对不上，消息停在 `claimed(new_scope)` 永远没人消费。PR-51 Part 2 的 HealthWorker stuck-claimed 扫描兜底清，**但不能防止产生新的幽灵 scope**。

PR-52 在 subscriber 侧做两道闸，**只针对 retry（`row.attempts > 0`）触发**，happy path 零开销：

1. **Lifecycle 闸** — `GET /v1/entities/messages/{id}`：
   - `pending` → 正常 retry dispatch（最常见场景）
   - `consumed` → 已经由 scope_end 处理完，`mark_delivered` + 不 dispatch
   - `claimed` → 进入 aliveness 闸
   - 其它 / probe 失败 → fail-open 继续 dispatch
2. **Aliveness 闸**（仅 claimed 分支）— Cortex `POST /v1/meta/read`：
   - `meta.phase in {"executing", "compacting"}` → 活，`mark_delivered` + 不 dispatch（原 claim 正在处理，再 dispatch 会重复触发）
   - `phase=archived|failed` 或 `meta=={}` → 死，`mark_delivered` + 打 `STALE_CLAIM_DEAD_SCOPE` 日志 + metric `subscriber_stale_claim_total{result=dead_scope}`。**不自己 transition**——claimed → consumed 归 PR-51 Part 2 scanner。
   - probe 失败 → fail-open

Kill switch：`SUBSCRIBER_STALE_CLAIM_CHECK=0` 恢复 pre-PR-52 行为。

这条护栏不碰状态机、不写 DB，只是在 dispatch 前加读闸，所以与 §3.1 / §3.2 / §3.3 全兼容。真想要消除"幽灵 scope 诞生"，比这条护栏更强的方案需要 Queue Service 在 `dispatch` 时也做 scope-aliveness 检查，成本远高于收益（主路径上每条都要多一个 Cortex hop），记账到 backlog。

---

## 4. 与其它 PR 的关系

- **PR-17 (Dispatch Subscriber)**：物理上把 outbox→queue 的 dispatch 从 `chat_messages` 触发器搬到独立 subprocess。PR-20/21/22/23 是它落地后的"装仪表"动作。
- **PR-22 (本页 §3.1)**：点亮 `claimed` 入口。
- **PR-23 (本页 §3.2)**：点亮 `consumed` 出口。
- **PR-25 (端到端追踪)**：依赖 PR-20 的 `input_message_ids` 反向索引拼链路图。
- **PR-26 (本页 §4)**：已落地。依赖 PR-21 的 `lifecycle='pending'` + outbox JOIN 做"`pending` 超时"扫描告警。
- **PR-27 (本页 §4)**：已落地。PR-26 扫到的 crit 孤儿走 `TriggerType.RECOVERED` 再派发，然后复用 PR-22 的 `claimed` 入口。
- **PR-19 (HealthWorker recovery-only)**：HealthWorker 的唯一身份就是 Queue timeout recovery + PR-26/27 孤儿兜底；主路径 dispatch 全归 subscriber。

---

## 4. PR-26 / PR-27 — `pending` 超时的兜底告警 + 自愈

PR-22/23 是"主路径成功时让状态机正确流动"，PR-26/27 是"主路径失败时有人
能看到 + 有人能自愈"。这条链挂在 `HealthWorkerSync` 上（同一个 worker 进程、
同一个 tick，`check_interval` 默认 30s）。

### 4.1 PR-26 — 孤儿扫描 + 告警

**查询源**：`GET /v1/orphans?min_age_sec=&limit=&include_delivered_pending=`
（`Entangled/packages/server-python/entangled/app/orphans.py`）。做
`chat_messages LEFT JOIN message_outbox`，返回 `{message_id, agent_id,
age_seconds, severity, lifecycle, outbox_attempts, outbox_last_error,
outbox_delivered_at, ...}`。

**代理**：`GET /internal/messages/orphaned`（Business 薄代理），Entangled
不可达时 502（blind scanner 比 noisy 的更糟）。

**严重度**：server-side 计算
- `created_at < now - 300s` → `crit`
- 否则 → `warn`

**告警**：`HealthWorker._scan_and_recover_orphans` 每 tick 拉一次，打日志：

```
crit:  ERROR   ORPHAN message_id=<id> agent=<a> age=<s>s attempts=<n> last_error=<...>
warn:  WARNING orphan_warn message_id=<id> ...
```

**去重**：`(message_id, severity)` 级别，`ORPHAN_EMIT_DEDUP_SEC=600s`。
同严重度不重复打；`warn → crit` 升级会在新严重度再打一次，所以 ops 用
`rg ORPHAN` 能直接看到"什么时候升级的"。

### 4.2 PR-27 — 孤儿再派发

**入口**：`HealthWorker._maybe_recover(message_id, agent_id, attempts)`，
仅 `severity='crit'` 的 row 会进来。

**attempts 门**：`outbox.attempts < MAX_RECOVERED_ATTEMPTS`（默认 3）。到
达 / 超过 → 打 `PERMANENT_ORPHAN` ERROR，`metrics.permanent_orphans++`，**不
调 assembler**。ops 必须人工介入，因为这表示主路径已经连着试了 3 次都失败。

**再派发**：走一个 **独立的** `DispatchAssembler`（`service_name="runtime-recovery"`），
调 `assemble_and_dispatch_sync(TriggerType.RECOVERED, agent_id, message_ids=[id],
metadata={"recovered_from": "orphan", ...})`。Queue Service metrics 以
`caller` label 区分 `business-subscriber`（主路径）和 `runtime-recovery`
（孤儿兜底）——**不要**让 caller 收到"recovery / 6000 dispatch = 0.1%"的时候
以为主路径有问题。

**claim**：成功后复用 PR-22 路径 —— `POST /internal/messages/bulk-transition`
（batch size 1），`to="claimed" scope_id=result.scope_id reason="recovered"`。
PR-23 的 noop 语义让这里和 subscriber 的并发 claim 无冲突。

**错误分类**：

| `DispatchError.kind`      | 动作                                        |
|---------------------------|---------------------------------------------|
| `no_owner` / `bad_argument` | 打 `PERMANENT_ORPHAN`，不重试                |
| `queue_5xx` / `network`   | 只计数，下个 tick 再试（仍受 attempts 门约束）|
| 未知异常                  | 同上                                        |

### 4.3 这条链解决的"10 分钟没人发现"问题

PR-26 前，一条 dispatched 但没进 saga 的 message 会永远停在 `pending`，
没有任何 metric / log 会提醒。PR-26 后：
- 30s 打 WARN，300s 打 ERROR `ORPHAN`
- 300s 后 PR-27 自动尝试 re-dispatch（最多 3 次）
- 超过 3 次自动打 `PERMANENT_ORPHAN`，这时日志里一定有 3 条带
  `recovered_dispatched_failed` 的记录 + `outbox.last_error` 的具体原因。

