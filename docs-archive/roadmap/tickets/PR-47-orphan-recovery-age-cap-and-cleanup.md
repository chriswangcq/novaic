# PR-47  老毒 USER_MESSAGE 清理 + HealthWorker recovery 年龄上限

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（PR-41 止血后的次生污染） |
| **Milestone** | R5（orphan 有界可恢复） |
| **承诺** | R5 + R1（单一事实 of 分发） |
| **Status** | `[✓]` — runtime + Entangled 状态机 + 单测 9+5 全绿；**已部署 prod（2026-04-22 17:57 UTC）**。迁移 SQL 线上 run 为 no-op：PR-41 amend 已提前清空 `pending` 池（see 部署证据）；迁移保留作为防御性资产 |
| **Depends on** | PR-27（recovery dispatch）、PR-46（by-ids 装配，否则清理前线上还会继续污染） |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `fix(health): recovery must not retry user messages older than N days; migrate pre-fix pending pool` |

## 事件摘要

PR-41 解决了 `AGENT_REPLY` 残留 pending 的自苏醒；但 04-17 ~ 04-21 期间用户发的 **11 条 USER_MESSAGE** 仍然以 `lifecycle=pending` 滞留：

```sql
-- 线上现状（04-22 排查）
SELECT id, type, created_at, lifecycle, read FROM chat_messages
WHERE agent_id = '<agent>' AND type='USER_MESSAGE' AND lifecycle='pending';
-- 预期：11 条，从 03a4be52b217 (04-17) 到 7227fd7fa8ab (04-21 14:57)
```

HealthWorker 当前 orphan 判定：

```python
# health_worker.py
ORPHAN_WARN_AGE_SEC = 60            # 超过 60s 的 pending 就算 orphan
MAX_RECOVERED_ATTEMPTS = 3          # 最多 recovery 3 次
```

11 条消息 age 从 21h 到 4 days 都远超 60s，全部被持续 recovery。PR-27 的 `_maybe_recover` 每次都成功下发一个新 scope（因为 orphan dispatch 本身就会走 assemble_and_dispatch_sync，只要能下发成功就不累加 `outbox.attempts`），于是**这 11 条消息每次 HealthWorker tick 都喂一次新 scope**。

叠加 PR-46 未上线时 `handle_context_read` 的"扫 unread"行为，这 11 条会在每个新 scope 的 context 里出现。结果就是用户看到的"我发'hi hi'，agent 回我一大堆对 4 天前积压的 catch-up"。

### 两个独立问题

1. **数据问题（历史遗留）**：11 条 04-17 ~ 04-21 的 USER_MESSAGE 卡在 `pending`，需要一次性迁移清理。
2. **机制问题（未来还会再犯）**：HealthWorker 没有"绝对年龄上限"，只要消息一直 pending，就一直 recovery。哪怕 `MAX_RECOVERED_ATTEMPTS=3` 加大了重试门槛，实际上 recovery 成功 ≠ 消息被消化（见根因 A 里的 handle_context_read 不按 id 取），消息会一直 "recovery 成功 / 其实没消化 / 下次再 recovery" 循环。

## 方案

### A. 一次性迁移脚本：把远古 pending USER_MESSAGE 落到 consumed 终态

```sql
-- scripts/migrations/047_cleanup_ancient_user_message_pending.sql
-- 备份
CREATE TABLE chat_messages_backup_pr47 AS
  SELECT * FROM chat_messages
  WHERE type='USER_MESSAGE' AND lifecycle='pending'
    AND created_at < strftime('%s','now','-48 hours');

-- 迁移
UPDATE chat_messages
SET lifecycle = 'consumed',
    consumed_reason = 'pr47_ancient_pending_cleanup',
    consumed_at = strftime('%s','now')
WHERE type='USER_MESSAGE' AND lifecycle='pending'
  AND created_at < strftime('%s','now','-48 hours');
```

- **为什么 48h**：远超单次 agent 崩溃恢复窗口（秒级），同时也远超正常 user reply 间隔（分钟-小时级）；`>48h` 的 `pending` 消息 100% 是"系统之前坏了没消化"，没有任何理由再 dispatch。
- **为什么不 purge**：消息文本要保留做历史展示（chat UI 上还要显示）。只改状态机字段。
- **备份表**：出事随时 restore（SQLite 下 `CREATE TABLE AS SELECT` 是 O(N) 拷贝）。

### B. HealthWorker: recovery 绝对年龄上限

```python
# health_worker.py
MAX_RECOVERY_AGE_SEC = int(os.environ.get("MAX_RECOVERY_AGE_SEC", 6 * 3600))   # 6h

def _maybe_recover(self, message_id, agent_id, attempts):
    if attempts >= MAX_RECOVERED_ATTEMPTS:
        ...  # 既有：打 PERMANENT_ORPHAN
        return
    # NEW:
    age = now_ts - row["created_at"]
    if age > MAX_RECOVERY_AGE_SEC:
        logger.error(
            "PERMANENT_ORPHAN_AGE message=%s agent=%s age=%d max=%d",
            message_id, agent_id, age, MAX_RECOVERY_AGE_SEC,
        )
        self.metrics.permanent_orphans += 1
        metric_inc("orphans_total", severity="permanent", reason="age")
        # 同时把它标 consumed(reason=age_cap)，避免下轮 tick 再捞到
        self._transition_to_consumed(message_id, reason="age_cap")
        return
    ...  # 既有 dispatch 逻辑
```

- **为什么 6h**：比 PR-41 的 `ORPHAN_WARN_AGE_SEC=60s` 大两个数量级，给正常恢复充足空间；同时明显短于 48h 的迁移门槛，形成"0-6h 重试 / 6h-48h 缓冲 / >48h 迁移清理"三段梯度。
- **为什么顺手转 consumed**：否则消息永远处于"orphan 但不 retry"的灰色状态，下一轮 tick 还会扫到、每次都 log 一行 PERMANENT_ORPHAN_AGE，噪音。显式转终态 = 状态机收敛。
- **配置暴露**：`MAX_RECOVERY_AGE_SEC` 通过环境变量，默认 6h；值 0 退回旧行为。

### C. 新 metric：`orphans_total{severity,reason}`

- 现有 `metric_inc("orphans_total", severity="permanent")` 补第二维 `reason = attempts | age | no_owner | bad_argument`。
- Prometheus 上能直接看出"最近 10 分钟多少 orphan 是因年龄超限被终结"。
- 如果部署之后发现 `reason=age` 占比 >0，说明有持续产生的"怎么都 dispatch 不成功"消息（恶意 agent？配置错误？），需要进一步排查——而不是被 recovery 隐藏掉。

### D. 迁移前后的观测 SQL

```sql
-- 迁移前 baseline
SELECT type, lifecycle, COUNT(*) FROM chat_messages
WHERE created_at < strftime('%s','now','-48 hours')
GROUP BY type, lifecycle;

-- 迁移后预期
-- type=USER_MESSAGE lifecycle=pending 这一行 COUNT(*) = 0
```

## 范围

### runtime
- `novaic-agent-runtime/task_queue/workers/health_worker.py::_maybe_recover`：加 age cap 分支
- `novaic-agent-runtime/task_queue/workers/health_worker.py`：加 `_transition_to_consumed(reason)` helper（调 Business `/internal/entities/messages/{id}` PATCH lifecycle）
- 新增 `MAX_RECOVERY_AGE_SEC` env

### business
- `novaic-business/business/internal/message.py::bulk-transition` 或 `messages/{id}/transition`：接收 `reason="age_cap"` 透传到 lifecycle 状态机（PR-21 的 state_transition 函数）
- 如已支持 `reason` 透传，无代码改动

### entangled
- `packages/server-python/entangled/sql/message_state.py::state_transition`：支持 `reason="pr47_ancient_pending_cleanup" / "age_cap"` 两个原因码（白名单补项，其他字段零改）

### 迁移
- `scripts/migrations/047_cleanup_ancient_user_message_pending.sql`
- 执行前/后 paste SQL 统计到 PR 描述

### 测试
- `novaic-agent-runtime/tests/test_health_age_cap.py`：age < cap 走 recovery / age > cap 走 consumed+PERMANENT / 边界一秒左右稳定选择 consumed

## 实施 Checklist

### A. HealthWorker 改动 — 已实现
- [x] `MAX_RECOVERY_AGE_SEC` 环境变量（默认 `6*3600 = 21600`s；`0` 回退 pre-PR-47）
- [x] `_maybe_recover` age 分支：age > cap 时优先级高于 attempts cap，转 consumed + log `PERMANENT_ORPHAN_AGE` + metric
- [x] `_transition_to_consumed(message_id, reason)` helper（bulk-transition POST；软失败不抛）
- [x] metric `orphans_total` 增加 `reason` 维度：`age` / `attempts` / `permanent_failure` / `no_owner` / `bad_argument`
- [x] 从 `_scan_and_recover_orphans` 到 `_maybe_recover` 的签名升级 — 透传 `age_sec`

### B. 迁移 — 已准备
- [x] `scripts/migrations/047_cleanup_ancient_user_message_pending.sql` 写好
- [x] 脚本内嵌前/后观测 SQL、备份表 `chat_messages_backup_pr47`、reason=`pr47_ancient_pending_cleanup`
- [x] 幂等：重跑不产生二次变更（`WHERE lifecycle='pending'` 过滤）
- [x] 修正 `created_at` 比较：prod 是 ISO-8601 TEXT（`datetime('now')` 默认），不是 epoch-millis；用 text-to-text 比较（SQL 里两次修复 commit）
- [x] 修正 `message_state_transitions` 列名：prod schema 是 `(message_id, from_state, to_state, reason, actor, scope_id, metadata_json, created_at)`，与首版不同
- [x] prod backup：`/opt/novaic/snapshots/entangled.db.pr47.bak.$(date +%s)`（deploy-business.sh incremental 模式不自动备份，手动 `cp`）
- [x] prod run（2026-04-22 18:00 UTC）：迁移成功但 no-op。Before / After (>48h 窗口) 各自 `(USER_MESSAGE, claimed)=25 / (USER_MESSAGE, consumed)=121 / (USER_MESSAGE, pending)=0`；backup 表 0 行；audit 表 0 行。**原因**：PR-41 amend（`_stamp_consumed_if_non_trigger` 覆盖 `_sql_create`）已提前治本，使得"新增 pending AGENT_REPLY/TOOL_OUTPUT"的源头被掐断，加上 subscriber 正常消费把历史 pending 也清零了。该迁移的实际价值已降级为"防御性保留"（未来若状态机又出现同类漏水，可一键执行）。

### 意外发现（不在 PR-47 范围 — 记作跟单）
- 25 条 `USER_MESSAGE` 停在 `lifecycle='claimed'`，`claimed_by_scope='03a93597-6102-4c8e-889e-015fafe6e4e9'`，created_at 集中在 2026-04-18 13:03..13:14；scope 长期未回收。这是 *stuck-claimed* 而非 *stuck-pending*，属于独立问题（HealthWorker 的 `_scan_unhandled_messages` 只管 `pending`；`claimed` 靠 scope_end 和孤儿升级）。**建议另开工单 PR-51（stuck-claimed 回收）**。

### C. Business/Entangled reason 白名单 — 已实现
- [x] `ALLOWED_TRANSITIONS` 扩展：`pending → {"claimed", "deduped", "consumed"}`（`consumed` 新增）
- [x] `_PENDING_CONSUMED_REASON_ALLOWLIST = {"age_cap", "pr47_ancient_pending_cleanup"}`
- [x] `transition()` 在 `pending→consumed` 分支强制校验 reason，非白名单 → `InvalidTransition`
- [x] 状态机 docstring / 图更新（`pending → consumed` admin-only edge）
- [x] `message_state_transitions` 表自动写入 reason（沿用 PR-31 已有链路）

### D. 单测
- [x] runtime：age < cap → recovery dispatch 被调用（`test_age_below_cap_still_dispatches`）
- [x] runtime：age > cap → 不 dispatch、bulk-transition(age_cap)、metric+1（`test_age_above_cap_transitions_consumed_and_skips_dispatch`）
- [x] runtime：age > cap AND attempts > max → age 优先（`test_age_cap_priority_over_attempts_cap`）
- [x] runtime：age == cap 严格 `>` 边界不触发（`test_age_exactly_at_cap_does_not_trigger`）
- [x] runtime：`MAX_RECOVERY_AGE_SEC=0` 完全禁用分支（`test_max_recovery_age_zero_disables_branch`）
- [x] runtime：bulk-transition 500 / 网络异常 → 不 raise（`test_bulk_transition_http_error_is_soft_fail` / `test_bulk_transition_exception_is_soft_fail`）
- [x] runtime：attempts-cap 路径仍 emit `orphans_total{reason="attempts"}`（`test_attempts_cap_still_triggers_permanent_orphan`）
- [x] runtime：`_transition_to_consumed` reason 透传不被篡改（`test_transition_to_consumed_passes_reason_verbatim`）
- [x] Entangled：`ALLOWED_TRANSITIONS` 快照（`test_allowed_transitions_matches_rfc` 更新）
- [x] Entangled：`pending → consumed` 无 reason → InvalidTransition（`test_pending_consumed_requires_admin_reason`）
- [x] Entangled：非白名单 reason → InvalidTransition（`test_pending_consumed_rejects_unrelated_reason`）
- [x] Entangled：`age_cap` / `pr47_ancient_pending_cleanup` 两个白名单 reason 都能通过（`test_pending_consumed_accepts_admin_reasons` 参数化）
- [x] Entangled：历史非法转移（`consumed`→`claimed` 等）仍被拒绝（`test_invalid_transitions_rejected` 更新）

### E. 回归
- [x] novaic-agent-runtime 全套 199 个全绿（含 PR-41 / PR-45 / PR-46 / PR-48 / PR-49 历史单测）
- [x] Entangled server-python 全套 117 个全绿（含 PR-21 / PR-23 / PR-31 状态机历史单测）

## 验收

### 本地
```bash
cd novaic-agent-runtime && ./run_tests.sh tests/test_health_age_cap.py tests/test_health_dispatch.py tests/test_health_orphan_scan.py
sqlite3 /tmp/entangled.db.bak < scripts/migrations/047_cleanup_ancient_user_message_pending.sql
```

### 线上
```bash
# 1. 迁移前统计
ssh prod sqlite3 /opt/novaic/data/entangled.db \
  "SELECT type, lifecycle, COUNT(*) FROM chat_messages \
   WHERE created_at < strftime('%s','now','-48 hours') GROUP BY type, lifecycle;"
# paste 到 PR 关单评论（before）

# 2. 备份 + 迁移
ssh prod 'cp /opt/novaic/data/entangled.db /opt/novaic/data/entangled.db.pr47.bak.$(date +%s)'
ssh prod sqlite3 /opt/novaic/data/entangled.db < scripts/migrations/047_cleanup_ancient_user_message_pending.sql

# 3. 迁移后统计 + HealthWorker tick 一轮的日志
ssh prod sqlite3 ... "同上查询"   # paste after
grep -E 'event=(orphan_scan|recovered_dispatch|PERMANENT_ORPHAN)' /opt/novaic/data/logs/runtime-*.log | tail -20
# 预期：不再出现 04-17 ~ 04-21 的 message_id；PERMANENT_ORPHAN_AGE 仅在"故意测试的 >6h 消息"上出现
```

## 部署 Checklist（必走）

1. 代码合入父仓 main（含 runtime + business + Entangled submodule bump）
2. `./deploy services` + `./deploy runtime`
3. 迁移脚本 prod 跑过，备份文件名记录在 PR 关单评论
4. 线上证据 ≥ 2 段：
   - 迁移前后 SQL 对比（USER_MESSAGE pending 数量从 11 → 0）
   - HealthWorker tick 后 `grep event=recovered_dispatch` 不再命中清理掉的 11 个 message_id
5. metric 采样 `orphans_total{reason="age"}` 近 1h 不增长（现网没有真实过期消息时应为 0）

## 风险 / 讨论

1. **6 小时阈值是否合理**：
   - 太短 → 正常 agent 长时间离线（用户在国外睡觉没看消息）后醒来，正常消息被当老毒扔掉。6h 覆盖大部分时区睡眠，用户早上看手机时的消息都能 recovery 成功。
   - 太长 → 老毒继续喂 agent。6h 配合 48h 迁移门槛刚好形成双重兜底。
   - 配置化 `MAX_RECOVERY_AGE_SEC` 让 ops 可调。
2. **"转 consumed(age_cap)" 之后消息是否还显示在 UI**：显示。`read` / `consumed` 都不影响 chat history 渲染（前端只按 timestamp 展示）。
3. **HealthWorker 同时 recover + transition 会不会 race**：`_transition_to_consumed` 之后 `return`，本 tick 不再 dispatch；下 tick 该 message 已 consumed，`query_orphans` 的 `lifecycle='pending'` 过滤会跳过。无 race。
4. **为什么不是 recovery tool 本身幂等**：recovery 的幂等性（idempotency_key）只管单个 dispatch 不被 Queue 重复执行；防止不了"下次 HealthWorker tick 再 recovery 一次"这种跨 tick 重试。年龄上限是跨 tick 的硬约束。
5. **PR-46 没上线时能不能先单独上 PR-47**：能，但价值打折。PR-46 负责"新消息进不进 scope"，PR-47 负责"老消息别再打扰"。两个 PR 独立安全。但建议顺序：PR-46 先（修主动脉），PR-47 后（清历史渣）。

## 承诺登记

- **R5**：orphan 真正"有界"——最坏 6h 或 3 attempts 就进入永久终态，不再无声循环。
- **R1**：dispatch 单一事实的另一面是"不合法的输入永远不会被当合法的 dispatch 重试"；年龄超限就是"已经不合法"。
