# PR-26  `recovery_worker` orphan emitter + metrics + `/orphaned` 视图

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| 字段 | 值 |
| --- | --- |
| **Phase** | 4（pending 告警） |
| **Milestone** | M3 |
| **承诺** | R5 |
| **Status** | `[x]` (2026-04-15) |
| **Depends on** | PR-19, PR-21 |
| **Blocks** | PR-27 |
| **估时** | 1 d |
| **Owner** | __ |
| **PR 标题** | `feat(runtime+business+entangled): orphan emitter (/v1/orphans JOIN + /internal/messages/orphaned proxy + HealthWorker scan)` |

## 实施总结（2026-04-15）

落地后的形态（与 RFC 的主要差异只在数据归位，不在行为）：

- **Entangled** — 新增 `GET /v1/orphans?min_age_sec=&limit=&include_delivered_pending=`
  （`entangled/app/orphans.py`）。做 `chat_messages LEFT JOIN message_outbox`，
  server-side 计算 `age_seconds` / `severity`，返回 `{orphans[], count,
  warn_count, crit_count, now_ms}`。LEFT JOIN 保证"有 chat_messages 但
  没 outbox 行"这种**就是可疑的**状态不被掩盖（见 endpoint docstring）。
- **Business** — 新增 `GET /internal/messages/orphaned`（thin proxy，
  `business/internal/message.py`），复用现有的 bulk-transition HTTP
  client，Entangled 不可达时 502（不是 empty list —— blind scanner 比
  noisy 的更糟）。ops + runtime 通过这一个 URL 拿同样的数据。
- **HealthWorker** — `task_queue/workers/health_worker.py` 的 `_perform_check`
  里同时跑 recover-all + orphan scan，一个 tick 一次 round-trip 到 Business。
  - dedup：`_orphan_emitted: {msg_id: (ts, severity)}`，`ORPHAN_EMIT_DEDUP_SEC`
    （默认 600s）内同严重度不重复打 log；warn→crit 升级会再打一次。
  - metrics：`orphans_seen / orphans_warned / orphans_crit` 走
    `HealthWorkerMetrics.to_dict()`，没有 metrics 模块之前这就是 ops 能拿到的。
- **阈值 env**：`PENDING_WARN_SEC=30` / `PENDING_CRIT_SEC=300` /
  `ORPHAN_EMIT_DEDUP_SEC=600`（`MAX_RECOVERED_ATTEMPTS` 归 PR-27 用）。

## 目标

把"消息 pending > 阈值"做成一等事件：metric + 可查视图 + alert 级日志。hihi 事件里"10 分钟无人察觉"这类失明不能再发生。

## 范围

- `novaic-agent-runtime/task_queue/workers/recovery_worker_sync.py`（PR-19 重命名的 worker）
- `novaic-business/business/internal/messages.py`（新增 `/orphaned` 视图端点）
- Metrics 端点

## 前置 Checklist

- [ ] PR-19 recovery_worker 已就位
- [ ] PR-21 `lifecycle` 字段可用
- [ ] 监控系统（日志告警或 prometheus）能消费新 metric

## 实施 Checklist

### 1. recovery_worker 加 orphan 扫描

```python
# recovery_worker_sync.py
PENDING_WARN_SEC  = int(os.environ.get("PENDING_WARN_SEC",  "30"))
PENDING_CRIT_SEC  = int(os.environ.get("PENDING_CRIT_SEC",  "300"))

async def _scan_pending_messages(self):
    now = int(time.time() * 1000)
    warn_before = now - PENDING_WARN_SEC * 1000
    crit_before = now - PENDING_CRIT_SEC * 1000
    rows = self.db.execute("""
        SELECT id, agent_id, created_at
          FROM chat_messages
         WHERE lifecycle = 'pending'
           AND created_at < ?
    """, (warn_before,)).fetchall()
    warn_count = 0
    crit_count = 0
    for r in rows:
        age_sec = (now - r["created_at"]) / 1000
        severity = "crit" if r["created_at"] < crit_before else "warn"
        if severity == "crit":
            crit_count += 1
            logger.error("ORPHAN message_id=%s agent=%s age=%.1fs", r["id"], r["agent_id"], age_sec)
        else:
            warn_count += 1
            logger.warning("orphan_warn message_id=%s agent=%s age=%.1fs", r["id"], r["agent_id"], age_sec)
        metrics.incr("messages_orphaned_total",
                     labels={"severity": severity, "trigger_type": infer_trigger(r)})
        metrics.observe("messages_pending_seconds", age_sec)
    metrics.gauge("messages_pending_count", len(rows))
    metrics.gauge("messages_orphaned_count_crit", crit_count)
    return len(rows)
```

### 2. Business 新增 `/internal/messages/orphaned`

```
GET /internal/messages/orphaned?min_age_sec=30&limit=50
→ 200 [
  {
    "message_id": "...",
    "agent_id": "...",
    "created_at": ...,
    "age_seconds": 312.4,
    "severity": "crit",
    "outbox_attempts": 5,
    "outbox_last_error": "no_owner: ..."
  }
]
```

- [ ] 按 `lifecycle='pending' AND age > min_age_sec` 聚合
- [ ] 附带 outbox 投递情况（JOIN）

### 3. Alert 输出

- [ ] `logger.error("ORPHAN ...")` 已经是 ERROR 级（log-based alert 可 grep `ORPHAN`）
- [ ] 预留正式 alert（pagerduty/飞书）接入点作为 TODO 注释

### 4. emitter 节奏

- [ ] recovery_worker 每个 tick（例 15s）跑一次 orphan scan
- [ ] 去重：同一 message 不重复 log（维护上次 emit 的 set 或 "last emitted at" 字段）→ 否则同一 orphan 每 15s 刷一条 ERROR

## 测试 Checklist

- [ ] 单测：插入 `lifecycle=pending created_at=now-60s` → emitter 1 次 WARN
- [ ] 单测：`created_at=now-600s` → emitter 1 次 CRIT
- [ ] 集成：kill subscriber + 发消息 + 等 5 分钟 → ORPHAN log 产生
- [ ] `/orphaned` 端点返回对应消息

## 可观测性 Checklist

> **落地偏差注记（TD-5, 2026-04-21）**：本节规划期命名为 `messages_orphaned_total`，
> 落地时为了跟 subscriber/assembler 那批 metric 保持短前缀一致，采纳
> `orphans_total` 作为最终名；label 也从 `{severity, trigger_type}` 收窄到
> `{severity}`（warn/crit/permanent 三档已经足够分流告警，trigger_type
> 在 `outbox_enqueued_total` / `dispatch_total` 已有覆盖）。

- [x] metric `orphans_total{severity=warn|crit|permanent}` counter（HealthWorker scan + TD-5 hook 进 PR-32 registry）
- [x] gauge `HealthWorkerMetrics.orphans_crit` / `.orphans_warned` / `.permanent_orphans` 内存计数（便于 `/health` debug 自省；Prometheus 侧以 `orphans_total` 为准）
- [x] log：ERROR 级带 `ORPHAN` / `PERMANENT_ORPHAN` 前缀，WARN 级 `orphan_warn`（便于 grep）
- [ ] histogram `messages_pending_seconds` — 规划期列出，落地时判断 `outbox_lag_seconds` gauge 已足够覆盖"整体感觉慢"这条查路径，histogram 推迟到真有按 percentile 看分布的需求时再加

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P4-1/2/3/4 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] `docs/runbooks/troubleshooting.md` 加 "消息 orphan 的 SOP"：
  1. `curl /internal/messages/orphaned`
  2. 对 crit 级 → 查 trace (`/internal/messages/<id>/trace`)
  3. 根据 outbox_last_error 决策

## 验收命令

```bash
# 制造 orphan：关 subscriber，发消息
DISPATCH_SUBSCRIBER_ENABLED=0 # 改 env
# 等 35 秒
rg ORPHAN recovery.log
curl -s .../internal/messages/orphaned?min_age_sec=30 | jq .
```

## 回滚

`git revert` —— 回到 "只有人工发现" 的盲区状态。强烈建议保留本 PR。

## 备注

- 去重非常重要；否则告警会变噪音。
- 严重度阈值建议 env 化，生产可微调。
