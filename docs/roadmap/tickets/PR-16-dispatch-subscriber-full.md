# PR-16  `dispatch_subscriber` poll 循环 + 去重 + retry

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| 字段 | 值 |
| --- | --- |
| **Phase** | 2 |
| **Milestone** | M2 |
| **承诺** | R1 + R6 |
| **Status** | `[x]` |
| **Depends on** | PR-15 |
| **Blocks** | PR-17 |
| **估时** | 1.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(business): dispatch_subscriber full implementation (poll/claim/dispatch/retry)` |

## 目标

让 subscriber 成为"消息写入 → wake"的主路径。保证：
- **at-least-once 投递**（依赖 Queue Service idempotency ledger 做 exactly-once 效果）
- **多实例安全**（locked_by + locked_until 的悲观锁）
- **失败重试 backoff**
- **不吞任何异常**

## 范围

- `novaic-business/business/subscribers/dispatch_subscriber.py`（PR-15 骨架，此处填充）
- 清理脚本：`scripts/outbox-compact.sh`（删 7 天前 delivered）

## 前置 Checklist

- [x] PR-14 / PR-15 合并
- [x] `message_outbox` 表存在并有积累（可手动灌几条测试行）

## 实施 Checklist

### `_tick` 核心逻辑

```python
async def _tick(self) -> int:
    now_ms = int(time.time() * 1000)
    claim_until = now_ms + CLAIM_TTL_MS  # e.g. 30_000

    # 1. Claim a batch (CAS):
    #    - delivered_at IS NULL
    #    - (locked_until IS NULL OR locked_until <= now_ms)   -- free or expired
    claimed = self.db.execute("""
        UPDATE message_outbox
           SET locked_by = ?, locked_until = ?
         WHERE id IN (
             SELECT id FROM message_outbox
              WHERE delivered_at IS NULL
                AND (locked_until IS NULL OR locked_until <= ?)
              ORDER BY id
              LIMIT ?
         )
         RETURNING id, message_id, agent_id, trigger_type, payload_json, attempts
    """, (self.worker_id, claim_until, now_ms, self.batch_size)).fetchall()

    if not claimed:
        return 0

    for row in claimed:
        await self._deliver_one(row)

    return len(claimed)
```

### `_deliver_one` 逻辑

```python
async def _deliver_one(self, row):
    payload = json.loads(row["payload_json"])
    try:
        req = await self.assembler.assemble(
            TriggerType.from_legacy(row["trigger_type"]),
            row["agent_id"],
            message_ids=[row["message_id"]],
            metadata=payload.get("metadata") or {},
        )
        result = await self.assembler.dispatch(req)
        # success → mark delivered, free lock
        self.db.execute("""
            UPDATE message_outbox
               SET delivered_at = ?, locked_by = NULL, locked_until = NULL, last_error = NULL
             WHERE id = ?
        """, (int(time.time()*1000), row["id"]))
        metrics.incr("subscriber_delivered_total", labels={"trigger": row["trigger_type"]})
    except DispatchError as e:
        # classify: permanent vs transient
        permanent = e.kind in ("no_owner", "bad_argument")
        attempts = row["attempts"] + 1
        if permanent or attempts >= MAX_ATTEMPTS:
            # give up; leave delivered_at=NULL but attempts high → PR-26 will flag as orphan
            self.db.execute("""
                UPDATE message_outbox
                   SET attempts = ?, last_error = ?, locked_by = NULL, locked_until = NULL
                 WHERE id = ?
            """, (attempts, f"{e.kind}: {e.msg}", row["id"]))
            logger.error("subscriber permanent fail id=%s kind=%s attempts=%d",
                         row["id"], e.kind, attempts)
            metrics.incr("subscriber_failed_total", labels={"kind": e.kind})
        else:
            # transient → free lock with backoff (exponential)
            backoff = min(300_000, 1000 * (2 ** attempts))  # cap 5min
            next_until = int(time.time()*1000) + backoff
            self.db.execute("""
                UPDATE message_outbox
                   SET attempts = ?, last_error = ?, locked_by = NULL, locked_until = ?
                 WHERE id = ?
            """, (attempts, f"{e.kind}: {e.msg}", next_until, row["id"]))
            logger.warning("subscriber transient fail id=%s kind=%s attempts=%d next_in=%ds",
                           row["id"], e.kind, attempts, backoff//1000)
            metrics.incr("subscriber_retry_total", labels={"kind": e.kind})
```

### 实装 checklist

- [x] `CLAIM_TTL_MS` / `MAX_ATTEMPTS` / `BACKOFF_CAP` 作为 class const 或 env 读取
- [x] Claim 用 `UPDATE ... WHERE id IN (SELECT ... ORDER BY id LIMIT)` + `RETURNING`（sqlite 3.35+ 原生支持）
- [x] Dispatch 成功后**必须**立刻 free lock（避免下次 tick 重复投递）
- [x] Dispatch 失败：
  - [x] `no_owner` / `bad_argument` → permanent
  - [x] `queue_400` → permanent（合约不匹配应报警而不是重试）
  - [x] `queue_5xx` / `network` → transient + backoff
- [x] 单个 tick 内多条消息按顺序处理（避免并发混淆 scope 归并）
- [x] Graceful shutdown：signal 到来时当前 tick 结束才退
- [x] Claim 的 lock 若进程 crash → `locked_until` 过期后自动被下个 worker 接管

### 运维脚本

- [x] `scripts/outbox-compact.sh`：
  ```bash
  sqlite3 ~/.novaic/data/entangled.db \
    "DELETE FROM message_outbox WHERE delivered_at IS NOT NULL AND delivered_at < strftime('%s','now','-7 days')*1000;"
  ```

## 测试 Checklist

- [x] 单测（用内存 sqlite）：
  - [x] 1 条 outbox → 1 次 dispatch → delivered_at 写入
  - [x] dispatch `queue_5xx` → attempts+1 + backoff；下次 tick 延后
  - [x] dispatch `no_owner` → attempts+1，不再 retry（locked_until 不延长以便 orphan emitter 发现）
  - [x] 2 个 subscriber 实例 + 100 条 outbox → 各自 claim 不重复；总投递次数 = 100
  - [x] subscriber crash 模拟（不 free lock）→ 30s 后另一实例接管
- [ ] 集成：`hihi` 场景端到端 → 观察 outbox delivered_at 更新、Queue Service 收到 1 次 dispatch
- [ ] 压测：1 秒内 100 条消息 → 全部在 2 秒内 delivered

## 可观测性 Checklist

- [x] metric `subscriber_delivered_total{trigger}` counter — 落地于 PR-32（`_deliver_one_inner` 成功分支）
- [x] metric `subscriber_failed_total{kind}` counter — 落地于 PR-32（permanent 分支：DispatchError / httpx.HTTPError / malformed payload 三处对称）
- [x] metric `subscriber_retry_total{kind}` counter — 落地于 PR-32（transient 分支两处对称）
- [x] metric `outbox_lag_seconds` gauge — 落地于 PR-32（`_claim_batch` 每 tick 从 `ClaimResponse.oldest_pending_age_ms` `metric_set`，`-1` 哨兵映射为 `0.0`）
- [x] metric `outbox_claim_batch_size` histogram — 落地于 PR-32（`_claim_batch` 每 tick `metric_observe(len(rows))`）
- [x] 结构化 log：`subscriber_tick claimed=N delivered=M failed=K`

## 文档 Checklist

- [-] [message-wake-refactor.md](../message-wake-refactor.md) P2-3（第二半）→ `[x]`
- [x] 本工单 Status → `[x]`
- [x] runbook 补一节 "outbox 堆积 / subscriber 停摆排查"

## 验收命令

```bash
# 启动 Business + subscriber
DISPATCH_SUBSCRIBER_ENABLED=1 ./scripts/start.sh

# 发一条消息
# 观察 outbox
watch -n1 "sqlite3 ~/.novaic/data/entangled.db \
  'SELECT id,trigger_type,attempts,delivered_at,last_error FROM message_outbox ORDER BY id DESC LIMIT 5;'"

# 预期：秒级内出现一行 → 1-2 秒内 delivered_at 被填

# 观察 metrics
curl http://localhost:8200/metrics | rg 'subscriber_|outbox_'
```

## 回滚

`git revert` —— subscriber 停（PR-17 的 flag 保护）。回滚时要同时关 env `DISPATCH_SUBSCRIBER_ENABLED=0`。

## 备注

- **实现重点在 claim 的原子性**。若不确定 sqlite 是否支持 `UPDATE ... RETURNING`，退化为 `BEGIN IMMEDIATE + SELECT + UPDATE + COMMIT`。
- `no_owner` 不重试 是故意的：PR-26 的 emitter 会把它当 orphan 报警，运维决定是否手动补 owner / 删消息。
- Queue Service 的 idempotency ledger（已有）是 exactly-once 的第二道保险：即便 subscriber 重复投递，ledger 会吃掉重复。
