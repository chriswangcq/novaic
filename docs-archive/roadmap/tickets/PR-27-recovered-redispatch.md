# PR-27  orphan re-dispatch (`trigger_type=recovered`)

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| 字段 | 值 |
| --- | --- |
| **Phase** | 4 |
| **Milestone** | M3 |
| **承诺** | R1 + R5 |
| **Status** | `[x]` (2026-04-15) |
| **Depends on** | PR-26 |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(runtime): HealthWorker re-dispatches crit orphans with TriggerType.RECOVERED and claims them` |

## 实施总结（2026-04-15）

与 PR-26 同一个 tick 内完成（`HealthWorkerSync._perform_check` →
`_scan_and_recover_orphans` → 对 `severity='crit'` 的 row 调用 `_maybe_recover`）。

**执行规则**：

- `outbox.attempts < MAX_RECOVERED_ATTEMPTS`（默认 3，env `MAX_RECOVERED_ATTEMPTS`）
  才进 assembler；到达上限直接打 `PERMANENT_ORPHAN` ERROR + 计数。
- 用 **新的 assembler 实例**，`service_name="runtime-recovery"`，所以
  Queue Service metrics 能区分主路径（`dispatch_total{caller=business-subscriber}`）
  和 recovery（`dispatch_total{caller=runtime-recovery, trigger_type=recovered}`）。
- Dispatch 成功后走 PR-22 / PR-23 同一个链路：`POST /internal/messages/bulk-transition`
  （batch size 1）把 message 切到 `claimed(by_scope=result.scope_id, reason="recovered")`。
  PR-23 的 `transition(current == to)` 是 noop，所以如果 subscriber 同时也
  claim 了不会 409。

**分类**（metrics 名是 `HealthWorkerMetrics.to_dict()` 里的字段）：

| 情况                                    | `recovered_dispatched_*` | `permanent_orphans` | 后续 |
|----------------------------------------|---------------------------|---------------------|------|
| 成功                                    | `_ok` +1                  | 0                   | 转 claimed |
| `DispatchError(kind=no_owner/bad_argument)` | `_failed` +1          | +1                  | 打 `PERMANENT_ORPHAN` |
| `DispatchError(kind=queue_5xx/network)` | `_failed` +1             | 0                   | 下个 tick 再试 |
| 未知异常                                | `_failed` +1              | 0                   | 下个 tick 再试 |
| attempts ≥ MAX                         | 不计                      | +1                  | 打 `PERMANENT_ORPHAN`，不调 assembler |

## 目标

给 orphan 消息一条明确、限流、独立 metric 的恢复通道。**不**与主路径（subscriber）metric 混淆。

## 范围

- `novaic-agent-runtime/task_queue/workers/recovery_worker_sync.py`

## 前置 Checklist

- [ ] PR-26 emitter 在跑
- [ ] `TriggerType.RECOVERED`（PR-09）已存在

## 实施 Checklist

### 策略

- [ ] 对 `severity=crit` 且 `outbox.attempts < MAX_RECOVERED_ATTEMPTS` (默认 3) 的 orphan → 通过 **Assembler** 以 `TriggerType.RECOVERED` re-dispatch
- [ ] 成功后 message lifecycle 仍由 subscriber 流程管（subscriber 会看到 Queue Service 返回的 session_id；但这里我们绕开 subscriber，需另行手动 transition → claimed）。简化实现：recovery_worker 直接走 Assembler，并在成功后自己调 `message_state.transition(...)` → claimed
- [ ] 超过 MAX_RECOVERED_ATTEMPTS → log ERROR `PERMANENT_ORPHAN`，不再 retry

### 代码

```python
async def _recover_orphans(self):
    orphans = self.db.execute("""
        SELECT cm.id as message_id, cm.agent_id, o.attempts, o.last_error
          FROM chat_messages cm
          LEFT JOIN message_outbox o ON o.message_id = cm.id
         WHERE cm.lifecycle = 'pending'
           AND cm.created_at < ?
           AND (o.attempts IS NULL OR o.attempts < ?)
    """, (now_ms - PENDING_CRIT_SEC*1000, MAX_RECOVERED_ATTEMPTS)).fetchall()
    for r in orphans:
        try:
            res = await self.assembler.assemble_and_dispatch(
                TriggerType.RECOVERED,
                r["agent_id"],
                message_ids=[r["message_id"]],
                metadata={"recovered_from": "orphan"},
            )
            # 主动 transition
            transition(self.db, r["message_id"],
                       to="claimed", scope_id=res.scope_id, reason="recovered")
            metrics.incr("recovered_dispatch_total", labels={"result": "ok"})
        except DispatchError as e:
            metrics.incr("recovered_dispatch_total", labels={"result": e.kind})
            if e.kind in ("no_owner","bad_argument"):
                logger.error("PERMANENT_ORPHAN message=%s kind=%s", r["message_id"], e.kind)
```

- [ ] `MAX_RECOVERED_ATTEMPTS` env 化
- [ ] recovery_worker tick 节奏例 30s（PR-26 的 15s 是 scan；recover 可以稀一些）

### Metrics 分离

- [ ] `dispatch_total{caller=business-subscriber}` 继续代表主路径
- [ ] `dispatch_total{caller=runtime-recovery, trigger_type=recovered}` 独立
- [ ] `recovered_dispatch_total{result}` 明确区分

## 测试 Checklist

- [ ] 集成：关 subscriber + 发消息 + 等 > PENDING_CRIT_SEC → recovery 接管
  - message lifecycle → claimed
  - outbox.attempts++（outbox 是 subscriber 的，recovery 不动它；但 recovery 成功后，subscriber 重启后会看到 `delivered_at IS NULL + lifecycle=claimed`，需要 subscriber 智能跳过）→ PR-16 应把这类消息视为"已被别处 claim"
- [ ] 超过 MAX_RECOVERED_ATTEMPTS → ERROR `PERMANENT_ORPHAN` + 不再尝试

### 与 subscriber 的互斥

- [ ] subscriber (PR-16) 里：`_deliver_one` 成功后 `transition` 若发现消息已是 `claimed`（被 recovery 抢先）→ log WARN + 更新 outbox 为 delivered
- [ ] 两者幂等，靠 Queue Service ledger 吃重复

## 可观测性 Checklist

- [ ] `recovered_dispatch_total{result}` counter
- [ ] log: `RECOVERED message=... agent=... attempts=N`
- [ ] log: `PERMANENT_ORPHAN message=... kind=...`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P4-5 → `[x]`
- [ ] OBS-3 → `[x]`（至此 3 个 metric 都齐）
- [ ] 本工单 Status → `[x]`
- [ ] runbook 加 "PERMANENT_ORPHAN 处置"

## 验收命令

```bash
# 观察 metric
curl -s localhost:8200/metrics | rg 'recovered_dispatch_total'

# 制造 orphan + 等 > PENDING_CRIT_SEC
# 看 recovery.log
rg RECOVERED recovery.log
```

## 回滚

`git revert` —— 退回到 "orphan 只报警不自动恢复" 状态；配 PR-26 依然安全。

## 备注

- 主路径应当覆盖 > 99% 场景；recovery 是极端保险。
- 若 `recovered_dispatch_total / dispatch_total > 1%`，表明主路径有问题，需要调查。
