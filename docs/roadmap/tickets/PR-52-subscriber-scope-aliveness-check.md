# PR-52 — subscriber scope-aliveness check before retry dispatch

| Field | Value |
|---|---|
| **Ticket**  | PR-52 |
| **Status**  | `[~]` impl + tests landed 2026-04-23, not yet deployed |
| **Opened**  | 2026-04-23 |
| **Owner**   | wc |
| **Blocks**  | (none — leak-prevention follow-up to PR-51) |
| **Blocked by** | PR-51 Part 2 (deployed, so the failure mode this PR prevents is currently observed + auto-cleaned, not critical) |
| **Invariant** | R-INV: *"runtime消费端只信 dispatch 透传的 id 集合"* (PR-46) — this PR extends the symmetry to the write-side: the subscriber must not silently re-materialise a scope for a message whose previous claim is already in flight or whose owning scope is dead. |

## 问题陈述

PR-51 Part 1 部署时发现 22 条 canary `USER_MESSAGE` 行的 `lifecycle_updated_at` 被刷新到 `2026-04-21 11:49 UTC`，远晚于它们 `created_at = 2026-04-18`。经调查：subscriber 重启 → outbox 行被 re-claim → `assembler.dispatch_sync` 创建了**新的 Cortex scope** → `_try_transition_claimed` 把 `chat_messages.lifecycle` 从 `pending → claimed(new_scope_id)` —— 但这条消息在 04-18 当天就已经被原始 scope 处理过，原始 scope 早已 archived。

结果：新创建的 scope 没有用户任何继续操作的上下文，要么自己死掉（留下 stuck-claimed），要么发一条无意义的 reply，浪费模型预算、污染用户会话。

PR-51 Part 2 在 scanner 侧兜底清理，但那是"事后打扫"；根因在 subscriber 的**重试路径从不检查 message 的当前 lifecycle**。

## 根因时序（从 Part 1 evidence 重构）

```text
T0  2026-04-18  user 发 USER_MESSAGE m1 → chat_messages.lifecycle=pending
T0  outbox 行 o1 (message_id=m1) 插入
T1  subscriber 首次 claim o1, dispatch → 新 scope S1 saga_started
T1  _try_transition_claimed: pending → claimed(S1), outbox.delivered_at=T1
T2  scope S1 执行中遇到 PR-46-era assembly bug → scope_end 未被调用,
    scope S1 成 archived 状态但 chat_messages 仍 claimed(S1)
    （这就是 PR-51 Part 1 清理的那些残留）
────────── 3 天过去 ──────────
T3  2026-04-21 11:49  运维部署触发 subscriber 重启
T3  新 subscriber 启动, 但 outbox o1 的 locked_until 早过期
T3  outbox claim 返回 o1 (delivered_at 其实非 NULL? 下面有分析)
T3  subscriber 再次 assembler.dispatch_sync → idempotency=msg:m1
    Queue Service 发现没有活跃 session（S1 已死），启动 NEW scope S2
T3  _try_transition_claimed 从 claimed(S1) → claimed(S2)：
    由于是 self-loop (claimed → claimed) 且 cur_state == to, PR-23 短路
    返回 noop, 但 **Entangled 是否真的没更新 lifecycle_updated_at?**
    答：代码路径确实不 UPDATE。所以这套"subscriber 重启刷新时间戳"
       的假说有问题。
```

**Re-examined 假说**：最合理的解释是 T1 的路径其实走成了 `dispatch 返回 saga_started 但 subscriber 先挂了，_try_transition_claimed 没跑`，所以 T1 后 chat_messages.lifecycle 仍然是 `pending`，outbox.delivered_at = NULL（如果 _mark_delivered 也没跑）或 outbox 进入 retry 状态。

然后 T3 重启时 outbox.retry 被再次消费 → dispatch 创建新 scope S2 → `_try_transition_claimed` 真正跑 `pending → claimed(S2)` → `lifecycle_updated_at = T3`。这与 Part 1 观察到的时间戳吻合。

即：**漏洞不是 "subscriber 重启刷新 claimed 行的时间戳"，而是 "subscriber 重试把一个死在旧 scope 的消息重新送进一个新 scope"**。

## 目标行为（PR-52）

subscriber 在 dispatch 前，针对**已重试的 outbox 行**（`attempts > 0`）做两道闸：

1. **Lifecycle 闸**：read `chat_messages.{lifecycle, claimed_by_scope}`。
   - `pending` → 正常重试 dispatch（真的是首次成功派发失败的场景）
   - `consumed` → 目标已经处理完，直接 `mark_delivered`，不派发
   - `claimed(by S')` → 进入 aliveness 闸
   - `orphaned` → 交给 orphan recovery path（PR-27），不在这里处理
2. **Aliveness 闸**（仅 claimed 分支）：probe Cortex `/v1/meta/read` for scope S'。
   - `meta == {}`（scope 不存在 / 已清理）→ 死
   - `meta.phase != "executing"`（archived / failed）→ 死
   - 否则 → 活
   - 活 → `mark_delivered`，不派发。原 claim 仍在处理，再派发会造成重复触发。
   - 死 → `mark_delivered` + emit `STALE_CLAIM_DEAD_SCOPE` + metric `subscriber_stale_claim_total{scope_state=dead}`。**不自己做 transition**（那是 PR-51 Part 2 scanner 的职责，且单 subscriber 并发 claim 换 consumed 需要考虑 reason-allowlist 扩展，此 PR 不触碰状态机）。

第一次尝试（`attempts == 0`）**不走任何闸** — fast path 零开销。

Cortex 不可达 → fail-open（假设 alive），继续正常派发。保留 subscriber liveness。

## Kill switch

`SUBSCRIBER_STALE_CLAIM_CHECK=0` 恢复 pre-PR-52 行为。默认开。

## 为什么不走更重的方案

**"强一致地拒绝 claim 死 scope 的消息"** 需要 Entangled 端状态机扩展、Cortex 端的 atomic scope lookup、跨三个服务的事务，成本远高于收益。PR-51 Part 2 已经在 24h 窗口内兜底，PR-52 做得"足够好"即可：
- 避免在 stuck-claimed 被 scanner 清掉之前产生新的无效 reply
- 避免浪费 LLM token 在一个已经无意义的会话轮次上
- 让 `subscriber_stale_claim_total` 指标成为 canary，告诉 ops "这种情况发生了"

## 实现 checklist

- [x] `novaic-business/business/subscribers/dispatch_subscriber.py`：
  - [x] 新增 `_probe_message_lifecycle(message_id)` → `{lifecycle, claimed_by_scope}` 或 `None`（soft-fail）
  - [x] 新增 `_probe_scope_alive(scope_id, user_id, agent_id)` → `True|False|None`（fail-open）
  - [x] 新增 `_check_stale_claim(row)` → `True` = abort dispatch
  - [x] 新增 `_extract_user_id(row)`：payload 优先，缺失时 fall back 到 `assembler._resolver.resolve_sync`
  - [x] `_deliver_one_inner` 在 `assembler.assemble_sync` 前调用 `_check_stale_claim`（仅 `row["attempts"] > 0`）
  - [x] 新 env `SUBSCRIBER_STALE_CLAIM_CHECK`（default on）
  - [x] 新 metric `subscriber_stale_claim_total{result=already_consumed|in_flight_live|dead_scope|probe_failed|scope_probe_failed}`
- [x] Cortex client 初始化：subscriber 已有 `cortex_client`（PR-20 起），复用，无需新增依赖
- [x] 单测 `novaic-business/tests/test_pr52_stale_claim_check.py`（**22 用例**，覆盖 fast-path / retry lifecycle 分支 / fail-open / kill switch / 两个 probe helper / user_id 回退）
- [x] 文档：`docs/architecture/scope-lifecycle.md` §3.4 新增"subscriber 重试路径的 scope-aliveness 护栏"
- [ ] 部署 + prod smoke（验证 `subscriber_stale_claim_total` 初始为 0，若出现 `result=dead_scope` 说明还在漏；`result=in_flight_live` 和 `result=already_consumed` 可观测到即 OK）

## 测试结果

```
novaic-business tests: 104 passed (22 PR-52 new + 82 pre-existing)
```

22 个新测试全绿：

* `test_first_attempt_skips_stale_claim_check` — fast-path 断言
* `test_retry_on_{pending,consumed}_*` — lifecycle 分支
* `test_retry_on_claimed_{live,dead}_scope_*` — scope-alive 分支
* `test_{entangled,cortex}_probe_failure_fails_open` — 失败策略
* `test_kill_switch_disables_check` — env 断路
* `test_unknown_lifecycle_proceeds_with_dispatch` — 未来新 state 向前兼容
* `test_probe_message_lifecycle_*`（4） — HTTP wrapper 单测
* `test_probe_scope_alive_*`（6） — Cortex probe 单测
* `test_extract_user_id_*`（3） — user_id resolver fallback

## 状态机兼容性

零改动。PR-52 **只读**消息状态 + scope phase，不写。写路径仍是 existing `_try_transition_claimed`（pending→claimed）和 PR-51 Part 2 HealthWorker（claimed→consumed）。

## 与其它 PR 的关系

- 受 PR-45、PR-46、PR-48 保护：这些 PR 减少了新 stuck-claimed 的产生速率
- 受 PR-51 Part 2 保护：scanner 负责兜底清理
- 本 PR 负责：避免在清理窗口内生成新的、错乱的 dispatch 副作用
