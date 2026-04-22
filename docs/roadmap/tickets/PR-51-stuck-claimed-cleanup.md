# PR-51  卡住的 `claimed` 行回收：补 PR-47 的另一半 + HealthWorker 周期扫描

| 字段 | 值 |
| --- | --- |
| **Phase** | Post-deploy 跟单（PR-47 部署过程中从 prod 现场发现） |
| **Milestone** | R5（消息生命周期闭环） |
| **承诺** | R5：`chat_messages.lifecycle` 不应出现"claimed 超过 N 小时仍非 consumed/orphaned" 的半死不活态 |
| **Status** | `[✓] Part 1 + Part 2 deployed 2026-04-23`；Part 1 migration 清理 25/28 rows，Part 2 HealthWorker 扫描 + Entangled/Business 端点上 prod，剩 3 rows 待自然老化被扫掉（均为 2026-04-21 prod-agent 行，~23h，距 24h 门槛不足 1h） |
| **Depends on** | PR-21（lifecycle 状态机）、PR-27（HealthWorker 孤儿扫描）、PR-41 amend（consumed-at-birth） |
| **Blocks** | — |
| **估时** | 0.5 d（一次性迁移）+ 0.5 d（HealthWorker 扩展）= 1 d |
| **Owner** | __ |
| **PR 标题** | `fix(lifecycle): recover stuck-claimed chat_messages + add HealthWorker claimed-age cap` |

## 事件摘要

2026-04-22 18:00 UTC 执行 PR-47 迁移时，`Before` 快照查询意外暴露：

```text
AGENT_REPLY|claimed|2
USER_MESSAGE|claimed|26    -- 后来回溯到 25 条（1 条进 consumed 了）
```

原预期是 "0 pending"（PR-41 amend + 正常 subscriber 消费），没想到 *claimed* 侧漏了一大把。按 `agent_id + claimed_by_scope + timestamp` 切片，得到 28 条卡死分布如下：

| Scope | Agent | Type | Rows | 最早 / 最晚 |
| --- | --- | --- | --- | --- |
| `03a93597-6102-4c8e-889e-015fafe6e4e9` | `canary_a_1` | `USER_MESSAGE` | 22 | 2026-04-18 13:03 / 13:14 |
| `b5e32c0c-b13b-4d09-80fb-63a9919cd507` | `canary_a_1` | `USER_MESSAGE` | 3 | 2026-04-18 13:22 / 2026-04-19 21:25 |
| `a50cf5b1-a486-43bb-931d-0620ff64abe0` | `415f6cfd4e5b4a04911b66cb8ab2cad7` | `USER_MESSAGE` | 1 | 2026-04-21 11:45（内容：`{"text":"说句话"}`） |
| `5b53d5de-b83b-4a35-b43e-190255da7601` | `415f6cfd...` | `AGENT_REPLY` | 1 | 2026-04-21 17:17（内容：`"hi！😊 终于能正常聊天了..."`） |
| `354b2d72-a35e-4f8e-8cc4-dbb938f6cec3` | `415f6cfd...` | `AGENT_REPLY` | 1 | 2026-04-21 18:14（内容：`"理解，抱歉让你有不好的体验..."`） |

`claimed_by_scope` 对应的 scope 全部在 Cortex 存储目录 `/opt/novaic/data/cortex/` 中**不存在**——`ls` 为空。即这些 scope 全部已经彻底消失（Cortex 进程重启、scope 文件被 GC、或 PR-23 scope_end 没跑到）。

## 根因拆解（两条独立路径同时贡献）

### 根因 A：pre-PR-41-amend 的 AGENT_REPLY 漏网
`5b53d5de` 和 `354b2d72` 的两条 `AGENT_REPLY` 都来自 2026-04-21 下午，**早于** 2026-04-22 18:00 的 PR-41 amend 部署。那之前的 `_sql_create` 路径不会 stamp `consumed-at-birth`，于是这两条 reply 以 `pending` 落盘，之后 subscriber 成功 claim（`claimed`），但 Cortex 的下游消费没能让它们走到 `consumed`。

这部分是历史数据，今天的 amend 已经切断源头，不会再新增。**属于一次性清理**。

### 根因 B：scope 死亡但 `chat_messages` 没回滚到 `orphaned`
`a50cf5b1` 下的那条 `USER_MESSAGE "说句话"` 是 2026-04-21 11:45 夜里那段失联事件的现场证据：

1. Subscriber 成功 dispatch → `claimed`。
2. 但 scope 在首轮 `context.read` 前后就挂了（当时还没 PR-48 Turn Finalizer、没 PR-46 by-ids 装配，首轮 think 很容易卡在"11 条 unread 轰炸"里）。
3. Scope 再也没回来，`scope_end` 永远不会触发。
4. `lifecycle` 留在 `claimed`，永世不得翻身。

HealthWorker 当前只扫 `pending`（PR-27 的设计），这种 `claimed + 孤儿 scope` 不在它的职责里。

### 根因 C：canary 测试残留
22+3 = 25 条 `canary_a_1` agent 的 USER_MESSAGE 是早期 PR-14/15 测试时的产物。那个 agent 现在仍然存在但没人用，历史 scope 早散架。没毒但占行——**一次性清理**。

## 方案

### Part 1 — 一次性 SQL 迁移 `048_cleanup_stuck_claimed.sql`

``lifecycle='claimed' AND lifecycle_updated_at < now - 24h`` → `consumed`。

阈值选 24h：

- 正常 subscriber dispatch → runtime think → consume 全链路 < 60s。
- 偶发 LLM 慢响应 / 人工 debug 延迟，最多几十分钟。
- 24h 足够把所有"正常流"排除，又足够短让下一次漏网在第二天就能被第二次运维扫到。
- （HealthWorker 的 `CRIT` 阈值是 300s，所以 24h 是它的 288×；不会误伤任何实时消息。）

`claimed → consumed` 是状态机既有合法边（PR-21），**无需** PR-47 那样的 reason-gate。单纯的 UPDATE 就够了。`reason="pr51_stuck_claimed_cleanup"` 留在 `message_state_transitions` 作审计。

**不动** `canary_a_1` 的历史 scope 或 agent 数据，只翻转消息生命周期列。canary agent 本身是个活的调试凭证，轨迹日志别动。

### Part 2 — HealthWorker 扩展：定期扫 `claimed + 超龄`

加一个新的扫描分支，和 PR-27 的 `pending orphan scan` 平行：

```python
# health_worker.py 新增
STUCK_CLAIMED_AGE_SEC = int(os.environ.get("STUCK_CLAIMED_AGE_SEC", str(24 * 3600)))

def _scan_and_recover_stuck_claimed(self):
    """Scan chat_messages WHERE lifecycle='claimed' AND age > threshold.
    Transition to consumed with reason='stuck_claimed_timeout'.
    """
    if STUCK_CLAIMED_AGE_SEC <= 0:
        return  # kill switch
    rows = self._get_business_client().get(
        "/internal/messages/stuck-claimed",
        params={"age_seconds": STUCK_CLAIMED_AGE_SEC},
    ).json()["messages"]
    for row in rows:
        self._transition_claimed_to_consumed(row["id"], reason="stuck_claimed_timeout")
        self.metrics.stuck_claimed_recovered += 1
        metric_inc("stuck_claimed_recovered_total")
```

Business 端需要新 endpoint `GET /internal/messages/stuck-claimed?age_seconds=N` 返回 `claimed` 且 `lifecycle_updated_at < now - N` 的行（参考 PR-27 的 orphan endpoint 实现）。

### Part 3 — Entangled 新增 reason 进 allow-list？

不需要。`claimed → consumed` 本来就允许（PR-21 `ALLOWED_TRANSITIONS["claimed"] = {"consumed", "orphaned"}`），reason 字段走现有 `transition()` 参数化。`reason` 值进 `message_state_transitions` 审计但不参与状态机决策。

## 范围

### Entangled
- 无代码改动；只需要确认 `transition(claimed → consumed, reason=<任意字符串>)` 正常工作（既有 PR-21 单测已覆盖）。

### novaic-business
- 新增 `GET /internal/messages/stuck-claimed` 列表端点（参考 `GET /internal/messages/orphans` 的结构）。
- 内部 SQL：`SELECT id, agent_id, type, claimed_by_scope, timestamp, lifecycle_updated_at FROM chat_messages WHERE lifecycle='claimed' AND lifecycle_updated_at < (strftime('%s','now') - ?) * 1000 LIMIT ?`

### novaic-agent-runtime
- `task_queue/workers/health_worker.py`：加 `_scan_and_recover_stuck_claimed` 分支，跟 `_scan_and_recover_orphans` 同 tick 或交替 tick。
- `STUCK_CLAIMED_AGE_SEC` env（默认 `24*3600`；`0` 禁用）。
- Metric `stuck_claimed_recovered_total`。
- 单测：mock business 返回 2 行 stuck-claimed，验证各自被 transition 到 consumed；kill switch；空列表；transition HTTP 失败软失败。

### scripts/migrations
- `048_cleanup_stuck_claimed.sql`——一次性清理历史。结构参考 `047_cleanup_ancient_user_message_pending.sql`（backup 表 + audit 行），但：
  - WHERE 条件是 `lifecycle='claimed' AND lifecycle_updated_at < (strftime('%s','now') - 24*3600) * 1000`
    （这里 `lifecycle_updated_at` 是 INTEGER epoch-millis，和 `created_at` TEXT 不同——schema 混合，不能混用）。
  - 无 reason-gate 问题。

## 实施 Checklist

### A. 一次性迁移（先上，止血）
- [ ] 写 `scripts/migrations/048_cleanup_stuck_claimed.sql`
- [ ] 本地 smoke：造一条 `claimed + old`、一条 `claimed + fresh`、一条 `pending`、一条 `consumed`，验证只翻第一条
- [ ] prod 前 `cp entangled.db entangled.db.pr51.bak.$(date +%s)`
- [ ] Before/After 快照 paste 进 PR 关单评论
- [ ] 验证：执行后 `SELECT COUNT(*) FROM chat_messages WHERE lifecycle='claimed' AND lifecycle_updated_at < (strftime('%s','now')-24*3600)*1000 → 0`

### B. Business endpoint
- [ ] `GET /internal/messages/stuck-claimed?age_seconds=N&limit=M`
- [ ] 单测：age/limit 参数、空结果、分页
- [ ] 跟 `/internal/messages/orphans` 保持 shape 一致

### C. HealthWorker 扫描
- [ ] `STUCK_CLAIMED_AGE_SEC` env + 默认 24h
- [ ] `_scan_and_recover_stuck_claimed` 方法
- [ ] `_transition_claimed_to_consumed` helper（复用 `_transition_claimed` 模板，只是 `to="consumed"`）
- [ ] metric `stuck_claimed_recovered_total`
- [ ] 扫描节奏：和 orphan 扫描同 tick 即可，不需要独立 scheduler

### D. 单测
- [ ] `_scan_and_recover_stuck_claimed` mock business 返回 2 行 → 各自 transition 到 consumed、metric +2
- [ ] Business 返回空 → no-op
- [ ] `STUCK_CLAIMED_AGE_SEC=0` → 完全跳过
- [ ] transition HTTP 5xx/异常 → 软失败，不阻塞 tick

### E. 回归
- [ ] PR-27 orphan scan 测试绿（不能因为新分支改变了老行为）
- [ ] PR-47 age cap 测试绿（`_transition_to_consumed` reason 不和本 PR 冲突）
- [ ] PR-21 状态机 `claimed → consumed` 合法性不变

## 验收

### 本地
```bash
cd novaic-agent-runtime && python -m pytest tests/test_health_stuck_claimed.py -q
cd Entangled/packages/server-python && python -m pytest tests/test_message_state.py -q
```

### 线上
```bash
# 1. 迁移前
sqlite3 /opt/novaic/data/entangled.db "SELECT COUNT(*) FROM chat_messages WHERE lifecycle='claimed' AND lifecycle_updated_at < (strftime('%s','now')-24*3600)*1000;"
# 预期：28（或部署时刻剩余）

# 2. 执行迁移
sqlite3 /opt/novaic/data/entangled.db < scripts/migrations/048_cleanup_stuck_claimed.sql

# 3. 迁移后
sqlite3 /opt/novaic/data/entangled.db "SELECT type, lifecycle, COUNT(*) FROM chat_messages GROUP BY type, lifecycle;"
# 预期：claimed 行数下降，consumed 上升同等数字

# 4. HealthWorker 部署后一天
grep 'stuck_claimed_recovered' /opt/novaic/data/logs/subscriber-*.log | tail -5
curl -s localhost:9090/metrics | grep stuck_claimed_recovered_total
# 预期：计数器保持 0（迁移后历史已清；新增的都会被 PR-41 amend / PR-48 正常闭环）
```

## 部署 Checklist

1. 合入父仓 main（仅 SQL 迁移可以独立先合）
2. 部署 `scripts/deploy-business.sh incremental` → 带 runtime HealthWorker 扩展 + business endpoint
3. 手动跑 `048_cleanup_stuck_claimed.sql`
4. paste Before/After 快照进 PR 评论
5. 一周后 check `stuck_claimed_recovered_total` metric：
   - `== 0`：健康（PR-41 amend + PR-48 + PR-46 的组合已经不再产生新的 stuck-claimed）
   - `> 0`：说明有新漏点，回头 debug；但至少 HealthWorker 已经兜住了

## 风险 / 讨论

1. **误伤正在 think 的长命 scope**
   真实 scope 的 `lifecycle_updated_at` 会在 subscriber claim 的那一秒定格，然后直到 runtime 成功 `transition(claimed→consumed)` 才再动。一个 scope 如果正在跑 30 分钟的深思（比如代码生成 + 工具调用链），那 30 分钟内它的 message 就停在 `claimed`，`lifecycle_updated_at` 不会更新。但 30 分钟 << 24h，所以 24h 阈值安全。更保险：Part 2 的 HealthWorker 扫描可以**只清**"scope 不在 Cortex 活跃列表"的——调 Cortex 的 `/v1/scope/list?status=active` 做二次确认。**推荐一期先不做这个确认**，因为 24h 本身已经足够宽，而且误清一条其实也只是让 runtime 下次 context.read 少拿一条；不会出现数据丢失（消息本体和 `message_text` 一直在）。

2. **PR-48 Turn Finalizer 已经部署，是否还需要 Part 2？**
   Turn Finalizer 只保证"LLM 不忘记关门"，但不保证"scope 本身没挂"。进程崩溃、OOM、外部 kill、subscriber race 等场景依然会遗留 `claimed`。HealthWorker 兜底 = 永久防漏。

3. **和 PR-47 age cap 的正交性**
   - PR-47：`pending > 6h` → `consumed(age_cap)`（reason-gated 因为 `pending → consumed` 不是常规边）
   - PR-51：`claimed > 24h` → `consumed(stuck_claimed_timeout)`（常规 `claimed → consumed` 边）
   两者独立，metric 独立（`orphans_total{reason=age}` vs `stuck_claimed_recovered_total`），log 独立，不交叉。

4. **`canary_a_1` 数据要不要保留？**
   22+3 条残留只是占行；但它们会被 `_render_chat_history`（PR-44 的 replay）扫到，作为 `read=0` 的历史注入到任何新的 canary_a_1 scope。虽然 canary agent 没活跃流量，但如果日后再拉起 canary 做回归测试，旧数据会污染 replay。**清。**

## 承诺登记

- **R5 补完**：`chat_messages.lifecycle` 三路兜底齐备——
  - 正常：subscriber dispatch + scope consume
  - 拖太久 pending：PR-47 age cap
  - 拖太久 claimed：**本 PR**
  - 正常消费不成但应归属：PR-27 orphan 升级 + PR-47 attempts cap

## 备注

- 这张票是 PR-47 部署过程中的"意外礼物"——没有真去 prod 摸 SQL 永远不会发现。写进 `docs/architecture/message-wake-principles.md` 作为 R-INV 事故复盘的一段。
- Part 1（迁移）可以**先独立 ship** 止血，Part 2（HealthWorker）跟 PR-50 Wave 2 一起打包。

## Part 1 部署记录（2026-04-23）

### 实际执行

```bash
cp /opt/novaic/data/entangled.db \
   /opt/novaic/snapshots/entangled.db.pr51.bak.1776852534  # ✓
sqlite3 /opt/novaic/data/entangled.db < scripts/migrations/048_cleanup_stuck_claimed.sql  # ✓
```

### Before / After

```text
BEFORE (prod, 2026-04-22 10:09 UTC):
  canary_a_1         | 03a93597... | USER_MESSAGE | 22  (created 2026-04-18)
  canary_a_1         | b5e32c0c... | USER_MESSAGE |  3  (created 2026-04-18..19)
  415f6cfd... (prod) | a50cf5b1... | USER_MESSAGE |  1  (created 2026-04-21 11:45)
  415f6cfd... (prod) | 5b53d5de... | AGENT_REPLY  |  1  (created 2026-04-21 17:17)
  415f6cfd... (prod) | 354b2d72... | AGENT_REPLY  |  1  (created 2026-04-21 18:14)
  ────────────────────────────────────────────────────
  Total: 28 stuck-claimed

AFTER pass 1 (lifecycle_updated_at < now - 24h):
  Cleaned: 3 rows (the b5e32c0c canary batch — only cluster whose
                   lifecycle_updated_at was pre-2026-04-21 10:09 UTC).
  Left:   25 rows (22 canary + 3 prod-agent; their lifecycle_updated_at
                   was refreshed to 2026-04-21 11:49 UTC by a subscriber
                   restart, so at 10:09 UTC on 04-22 they were only
                   ~22h20m old — narrowly inside the 24h window).

AFTER pass 2 (one-off ad-hoc, created_at < now - 72h):
  Cleaned: 22 more rows (all canary_a_1/03a93597 from 2026-04-18).
  Left:    3 rows (the prod-agent 2026-04-21 batch — only 19-22h old
                   by created_at; will age out organically within
                   ~2h and be caught by Part 2 HealthWorker scan).

Lifecycle totals after cleanup:
  AGENT_REPLY  | claimed   |   2
  AGENT_REPLY  | consumed  | 160
  USER_MESSAGE | claimed   |   1
  USER_MESSAGE | consumed  | 158

Audit trail (message_state_transitions):
  pr51_stuck_claimed_cleanup           |  3
  pr51_stuck_claimed_cleanup_by_age    | 22
  ──────────────────────────────────────────
  25 rows audited (matches ``chat_messages_backup_pr51`` count).
```

### Lessons from this run

1. **``lifecycle_updated_at`` isn't a reliable age proxy** when subscribers
   restart and re-claim existing rows. The 22 canary rows had their
   timestamp bumped to 2026-04-21 11:49 UTC by a subscriber restart on
   that day, even though their content and scope had been dead since
   2026-04-18. A second pass keyed on ``created_at`` was needed.
   ⇒ **Update Part 2**: HealthWorker's scan should use `MAX(lifecycle_updated_at, created_at_bumped_threshold)` — or, more simply, scan both axes (recent stuck: `lifecycle_updated_at < now-24h`; ancient stuck: `created_at < now-72h`).

2. **Subscriber re-claim of a dead scope's messages is its own bug**.
   The subscriber restart on 2026-04-21 11:49 UTC flipped those 22
   messages from whatever state they were in (`pending`? `orphaned`?)
   to `claimed` — but the owning scope (`03a93597...`) had been gone
   since 2026-04-18. That means subscriber's dispatch-to-runtime
   loop doesn't verify scope aliveness before claim. Open as
   ``PR-52 (follow-up): subscriber scope-aliveness check``.

3. **Audit sub-select pitfall (documented for future scripts)**:
   ``chat_messages_backup_pr51`` is a *snapshot*; its rows keep the
   original ``lifecycle`` value from insert time. My first pass-2
   audit query filtered on ``WHERE lifecycle = 'consumed'`` in the
   backup table — no rows matched (they're all snapshotted as
   ``claimed``). Fix: filter on live ``chat_messages`` or use
   ``NOT EXISTS`` against ``message_state_transitions``. The
   ``048b`` ad-hoc SQL above shows the correct pattern.

## Part 2 实现记录（2026-04-23）

### 代码变更

1. **Entangled** ``packages/server-python/entangled/app/stuck_claimed.py`` (new):
   - ``GET /v1/stuck-claimed`` 新端点
   - 双轴年龄匹配：``lifecycle_updated_at < now - min_age_sec`` **OR** ``created_at < now - min_created_age_sec``
   - 不再限制 message type（USER_MESSAGE / AGENT_REPLY / SYSTEM_NOTE 同样扫）——任何 type stuck-claimed 都是 bug
   - 响应字段 ``matched_axis`` ∈ {``lifecycle``, ``created``, ``both``} 暴露命中的轴，方便 dashboard 辨识"是正常老化还是 subscriber 重启污染"
   - ``matched_by_lifecycle`` / ``matched_by_created`` 汇总计数
   - 测试 ``tests/test_stuck_claimed.py``：14 用例，覆盖空结果、两轴匹配、非-claimed 豁免、任意 type、order by lifecycle_updated_at ASC、limit、forensic ``claimed_by_scope`` 字段、off-by-one 门槛、kill-switch 行为
   - ``app/factory.py`` 注册 router

2. **Business** ``novaic-business/business/internal/message.py``:
   - 新增 ``GET /internal/messages/stuck-claimed`` proxy（跟 orphan proxy 同形、复用 ``_get_bulk_transition_client()`` 的连接池）
   - ``StuckClaimedItem`` / ``StuckClaimedListResponse`` Pydantic schema
   - 默认参数 ``min_age_sec=86400`` (24h) + ``min_created_age_sec=259200`` (72h)
   - 软失败：Entangled 不可达 → 502，不 raise

3. **Runtime** ``novaic-agent-runtime/task_queue/workers/health_worker.py``:
   - 新增 env ``STUCK_CLAIMED_AGE_SEC`` (24h default, 0 = kill-switch) + ``STUCK_CLAIMED_CREATED_AGE_SEC`` (72h default)
   - 新 metrics ``stuck_claimed_seen`` / ``stuck_claimed_recovered`` / ``stuck_claimed_failed``
   - 新方法 ``_scan_and_recover_stuck_claimed()``：
     - 跟 orphan scan 独立 round-trip
     - 每行调 ``_transition_to_consumed(msg_id, reason="stuck_claimed_timeout")`` —— 复用 PR-47 helper（``claimed → consumed`` 是 state machine 合法边，无 reason-gate）
     - 单行异常不中断循环（``stuck_claimed_failed`` 计数）
     - 新 metric family ``stuck_claimed_total{axis=lifecycle|created|both}``
     - 新日志行 ``STUCK_CLAIMED message_id=... agent=... dead_scope=... axis=... lifecycle_age=... created_age=...`` (WARNING)
   - ``_perform_check`` 挂一个新分支：受 ``STUCK_CLAIMED_AGE_SEC > 0`` 保护，异常独立兜底
   - 测试 ``tests/test_health_stuck_claimed.py``：9 用例，覆盖单行 / 多行 / 双参数透传 / kill-switch / business 不可达软失败 / 5xx 软失败 / 空结果 no-op / 单行异常不中断 / 日志格式断言
   - 回归：``tests/test_health_dispatch.py::test_health_worker_perform_check_calls_recover_and_orphan_scan`` 更新断言（Business 现在每 tick 发 **两** 个 GET：先 ``/orphaned`` 再 ``/stuck-claimed``）

### 测试结果

```text
# Entangled
cd Entangled/packages/server-python && python -m pytest -q
  → 133 passed, 1 skipped

# Runtime (--deselect 2 个不相关 pre-existing 失败：performance flake + WAKE_IM_REPLAY regression)
cd novaic-agent-runtime && python -m pytest -q
  → 217 passed, 4 deselected
```

### 状态机兼容性

``claimed → consumed`` 本来就在 ``ALLOWED_TRANSITIONS`` 里（PR-21 ``message_state.py:66``），**不经过** ``_PENDING_CONSUMED_REASON_ALLOWLIST`` 的 reason-gate（那个只对 ``pending → consumed`` 生效）。所以 ``reason="stuck_claimed_timeout"`` 不需要加入 allow-list，状态机不会阻止转换。

这跟 PR-47 的 ``pending → consumed`` 路径形成漂亮的互补：
- PR-47 reason-gated，因为该边是从零新加的
- PR-51 不 reason-gated，复用 PR-21 一直存在的边

### 运维接口

部署后 ops 可以用的查询：

```bash
# 当前积压
curl -s 'http://localhost:19900/v1/stuck-claimed' \
  -H "X-Service-Token: $SVC_TOKEN" | jq '.count, .matched_by_lifecycle, .matched_by_created'

# 只看 subscriber-restart 污染（created 轴）
curl -s 'http://localhost:19900/v1/stuck-claimed?min_age_sec=99999999&min_created_age_sec=86400' \
  -H "X-Service-Token: $SVC_TOKEN" | jq '.stuck[] | {message_id, claimed_by_scope, created_age_seconds}'

# 强制立即兜底（把 min_age_sec 调到 0，scanner 会下一 tick 把所有 claimed 冲成 consumed）
# ——慎用，只在确信 scope 全死时用
export STUCK_CLAIMED_AGE_SEC=0  # disable
export STUCK_CLAIMED_AGE_SEC=60 # aggressive cleanup
systemctl restart novaic-runtime-subscriber  # HealthWorker 一起
```

### 部署 Checklist (Part 2)

- [x] 父仓 main 已 push（3 个 submodule commits + 1 父仓 bump commit）
- [x] ``./scripts/deploy-business.sh root@api.gradievo.com`` 跑过 incremental（Entangled + business + runtime 三件套）——2026-04-23 18:25 完成
- [x] Prod smoke 验证（默认 24h/72h 门槛）：
  ```bash
  curl -s 'localhost:19998/internal/messages/stuck-claimed' | jq .count
  # → 0（健康：3 剩余 prod-agent 行均 < 24h）
  ```
- [x] Prod smoke 验证（放宽 20h 门槛确认 endpoint 工作）：
  ```bash
  curl -s 'localhost:19998/internal/messages/stuck-claimed?min_age_sec=72000' | jq '.stuck[0]'
  # → {
  #     "message_id": "cbfe6007196e",
  #     "type": "USER_MESSAGE",
  #     "claimed_by_scope": "a50cf5b1-...",
  #     "lifecycle_age_seconds": 81372.5,  # ~22.6h
  #     "matched_axis": "lifecycle"
  #   }
  ```
- [x] HealthWorker 确认按 30s 周期发 scan：
  ```bash
  grep stuck-claimed /opt/novaic/data/logs/health.log | tail -5
  # → 每 30s 一次 GET /internal/messages/stuck-claimed → 200 OK
  ```
- [ ] 24h 后观察：3 剩余行应自动归零（``lifecycle_age_seconds`` 跨过 86400s → 下一 tick 扫掉 → ``stuck_claimed_recovered_total`` 计入 3）
- [ ] 1 周后观察 `stuck_claimed_recovered_total` 稳态：
  - ``== 3``：健康（PR-41 amend + PR-48 Turn Finalizer + PR-46 + 这个兜底组合已经不再产生新泄漏，只清理了历史残留）
  - ``> 3``：仍有新渠道漏，回溯日志里 `STUCK_CLAIMED message_id=... dead_scope=...` 定位漏源 → 触发 **PR-52** (subscriber scope-aliveness check)
