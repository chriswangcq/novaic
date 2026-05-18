# PR-50 Wave 2  IM outbox burst aggregation

| 字段 | 值 |
| --- | --- |
| **Phase** | R9 IM stream layer — UX / cost optimization |
| **承诺** | R9（IM 语义一致性）+ 成本预算 |
| **Status** | `[✓]` deployed to prod 2026-04-22 22:55 CST（随 PR-53 submodule bump 一同推送）；smoke PASS — 见下 |
| **Parent** | [PR-50](PR-50-im-message-aggregation.md)（Wave 1 byte-cap 已部署 2026-04-22） |
| **Depends on** | PR-14（outbox 表）、PR-20（buffered append_input）、PR-22（subscriber transition claimed）、PR-45（continuity enrichment）、PR-46（by-ids 装配）、PR-52（stale-claim guard） |
| **Blocks** | — |
| **估时** | 0.5 d（code 已完成，剩部署 + 现场观察） |
| **Owner** | __ |
| **PR 标题** | `feat(business): aggregate same-agent USER_MESSAGE outbox bursts within claim batch` |

## 事件摘要

PR-50 父工单的原始诊断（2026-04-22）：用户**连发 3 条短消息**，当前 subscriber 为每条 outbox 行发一次独立 dispatch —— 3 次 `session.init` / 3 次新 scope（或 1 次 `saga_started` + 2 次 `buffered`，都要多一次 `append_input`），对一个语义上的对话轮来说是 3× LLM 成本。Wave 1 已经把 `<CHAT_HISTORY>` 的字节 cap 落地防 token 预算爆；Wave 2 是**省 session.init 次数 + 合并同 sender 的语义**。

## 最终方案（与父工单设计的差异）

父工单原设计要求在 Entangled 侧加两个新 SQL API：`peek_same_agent_same_sender` + `claim_many`，让 subscriber 对 outbox 做 "60s 窗口 peek 一把"。

**实际实现放弃了这条路线**，原因是：

1. **现有 `/v1/outbox/claim` 已经一把返回 `batch_size=50` 行**（PR-14）。claim 回来的 batch 本身就是一张 "当前 pending 行" 的快照，按 outbox-id ASC 排序。一条用户连发的 3 条消息几乎不可能跨 tick（`poll_interval=0.5s`），绝大多数情况会在同一个 claim batch 里回来。
2. 跨服务 API 是一把越境负债——加 Entangled 端点要改 schema / 加 lint / 补 trace。**"claim batch 内分组"** 把所有逻辑收敛在 subscriber 一端，零新 HTTP 协议、零 Entangled 改动。
3. 合批的目标是"相邻消息共享 session.init"。**跨 claim tick 的消息本来就不能共享 session.init** —— 第一 tick dispatch 已经启动 scope 了；第二 tick 即便能 "看到" outbox 里还有同 sender 的新行，也只能走 `buffered` 分支，这条路径 PR-20 已经支持了（`append_input` 一条就一条，不需要新协议）。

所以：
- **Wave 2 真正要省的是 "新 scope 路径上的连发"**（`saga_started`）。这完全可以在 claim batch 内解决。
- **跨 tick 的连发**（用户发完第一条 agent 还没醒，发第二条时 scope 还没起来）其实也会落在同一个 batch 里—— claim 之间只有 0.5s 间隔，outbox 入表瞬时，来得及。
- **跨 tick 且 scope 已活**（`buffered` 路径），PR-20 `append_input` 已经每条消息各追加一次 `scope.meta.input_message_ids`，`handle_context_read`（PR-46）按 id 集合装配，合批在这个路径上没额外价值。

### 分组算法（subscriber 内）

`_group_for_aggregation(rows)` 以 claim batch 原始顺序为锚，**贪心向前吸收**：

```python
for i, row in enumerate(batch):
    if trigger(row) not in {USER_MESSAGE}:
        emit single(row); continue
    group = [row]
    j = i + 1
    while (
        j < len(batch)
        and len(group) < MAX_BATCH           # 防单轮 50 条同 agent 一次吃下
        and batch[j]["agent_id"] == row["agent_id"]
        and batch[j]["trigger_type"] == row["trigger_type"]
        and batch[j]["created_at"] - group[0]["created_at"] <= WINDOW_MS  # head-anchored
    ):
        group.append(batch[j]); j += 1
    if len(group) >= 2: emit aggregated(group); i = j
    else: emit single(row)
```

关键约束：

- **连续性要求**：插在中间的非同组行（不同 agent、不同 trigger）会断开合批。保证 FIFO 语义——非合批行的相对顺序不动。
- **窗口是 head-anchored**：从**第一条消息**到后续每条的 delta 都要在窗口内，不是两两 pairwise。否则 59s × 59s × 59s 会链成 3 分钟的组，远超用户预期。
- **MAX_BATCH = 10**：防 "用户贴了 50 行" 把一次 session.init 的上下文撑爆；多出来的行从第 11 条起重启一个新组，下一次 `assemble_sync` 继续合。

### 回退规则（失败不降安全）

`_deliver_aggregated` 遇到以下场景**立即散回 per-row**（等同 pre-Wave-2 行为）：

1. **任意行 `attempts > 0` 且 PR-52 stale-claim 开关 on** —— 合批路径无法对单行跑 `_check_stale_claim`（要个 `message_id` 一个个查 lifecycle + scope 活性）。散回散行，PR-52 正常生效。
2. **任意行 `payload_json` JSONDecodeError** —— 单行 `_deliver_one` 走 permanent-fail，兄弟行不被牵连。
3. **合批 `assemble_sync` / `dispatch_sync` 抛 `DispatchError` / `httpx.HTTPError`** —— 散回 per-row 让每条自己的 retry 计数独立推进。不对合批本身打 `mark_failed`（会让 N 条全都按同一指数退避卡着）。

### 幂等

- **合批时** `idempotency_key = agg:{first_message_id}:{last_message_id}`（由 id 序列唯一决定，跨 subscriber 实例并发安全，Queue Service 侧 dedup 生效）。
- **散行时**保持 PR-14 约定的 `msg:{message_id}`。
- HealthWorker 的 fallback 路径（PR-19）仍用 `msg:{id}`，合批幸运路径与 fallback 单行路径**不会互相 dedup**—— fallback 的兜底职责不被 Wave 2 抢走。

## 范围

### business 子模块（唯一动到的代码）
- `novaic-business/business/subscribers/dispatch_subscriber.py`
  - 新增模块级常量/helper：`_AGGREGATABLE_TRIGGERS`、`_im_aggregation_window_seconds`、`_im_aggregation_max_batch`、`_im_aggregation_enabled`。
  - `run()` 循环把 `for row in batch: _deliver_one(row)` 换成 `for unit in _group_for_aggregation(batch): dispatch(unit)`。
  - 新方法 `_group_for_aggregation(rows)` + `_deliver_aggregated(rows)`。
  - 指标：`im_aggregated_total{count}`、`im_aggregated_fallback_total{reason}`、`subscriber_delivered_total{trigger}`（原指标对合批也计数一次）。
  - 日志：`event=im_aggregate agent=.. trigger=user_message count=.. window_sec=.. ids=[..] action=.. scope=..`、`event=im_aggregate_fallback ..`。
- `novaic-business/tests/test_im_aggregation.py`（新，22 个用例）。

### 环境变量
- `IM_AGGREGATION_WINDOW_SEC`（默认 `60`；`0` 关闭整个 Wave 2，回退 pre-change 行为）
- `IM_AGGREGATION_MAX_BATCH`（默认 `10`；最小 `1`）

### 未动的部分
- **Entangled** —— 无 schema / endpoint 改动。
- **runtime** —— `handle_context_read` (PR-46) 已经按 `message_ids` 装配，合批的 N 条 id 透传到 `assemble_sync.message_ids` → `session.init` payload 的 `input_message_ids` → `scope.meta.input_message_ids` → `handle_context_read` 按 id 集合装配，全链路天然支持。
- **PR-38 IM 渲染** —— 合批**不**把多条用户消息合并成一条 `role=user`；LLM 仍看到多条独立 `role=user`（父工单 §风险 2 承诺）。PR-38 按消息顺序渲染。
- **SUBAGENT_SEND 合批** —— 一期不做。sender_fingerprint 需要从 `chat_messages.metadata.source_subagent_id` 查一次，和父工单原设计的"sender_fingerprint" 成本一致，不划算；SUBAGENT_SEND 的真实频率远低于 USER_MESSAGE，等 prod metric 看到确凿压力再加。

## 实施 Checklist

- [x] `_group_for_aggregation` 实现 + head-anchored 窗口
- [x] `_deliver_aggregated` 实现（assemble_sync 单次带 multi-ids + mark_delivered 批量 ids + 逐条 transition claimed + buffered 逐条 append_input）
- [x] 回退规则：`attempts>0 + stale-claim on` / bad payload / dispatch error 散回 `_deliver_one`
- [x] 幂等 key：`agg:{first}:{last}` 合批；单条仍 `msg:{id}`
- [x] Env plumbing：`IM_AGGREGATION_WINDOW_SEC=0` 全局 kill switch
- [x] Metric / 日志：`im_aggregated_total{count}` + `im_aggregated_fallback_total{reason}` + `event=im_aggregate ...`
- [x] 单测（22 例）：
  - 分组：kill switch、3 条连发、窗口边界、head-anchored（非 pairwise）、MAX_BATCH 溢出、混合 agent/trigger
  - 投递：单次 assemble_sync + multi-ids、batch mark_delivered、逐条 transition claimed
  - 回退：retry-row / dispatch error → per-row，单元素 group 委托 `_deliver_one`
  - Continuity：三连发只查一次 subagents 行
  - Buffered：逐条 append_input
  - run() 集成：burst → 1 次 assemble；kill switch → N 次 assemble
  - Env plumbing：合法 / 非法 / 0 / 最小值
- [x] 回归：所有 126 业务测试全绿（本地 `PYTHONPATH=.:../novaic-common:../Entangled/packages/server-python pytest tests/`）

## 验收（部署前本地）

```bash
cd novaic-business
PYTHONPATH=.:../novaic-common:../Entangled/packages/server-python \
  python -m pytest tests/test_im_aggregation.py tests/test_dispatch_subscriber.py tests/test_pr45_dispatch_continuity.py tests/test_pr52_stale_claim_check.py -v
```

## 部署 Checklist（必走）

1. [x] 代码合入父仓 main（含 business submodule bump — `d265e6d` 随 `d2771fd` 进入 main）。
2. [x] `./deploy services` —— 实际搭乘 PR-53 hotfix 的 `scripts/deploy-business.sh` 于 2026-04-22 22:55 CST 推送，subscriber 进程 PID 1586762 从 22:56 起运行包含 Wave 2 代码的 `dispatch_subscriber.py`。
3. [x] **prod smoke（2026-04-23 10:27 CST）**：`traffic.py send --count 3 --tps 10 --concurrency 3` 触发 canary_a_1 连发 3 条，subscriber 日志（`/opt/novaic/data/logs/subscriber-20260422.log`）出现：
   ```
   event=im_aggregate agent=canary_a_1 trigger=user_message count=2 window_sec=60
     ids=['3982b2ae9481','2c002d281c10'] action=saga_started scope=a47714e0-...
   event=dispatch trigger=user_message agent=canary_a_1 messages=2 result=ok
   ```
   即 3 连发 → 1 次 `saga_started`（2 条合并，`messages=2`）+ 1 次 `buffered`（第 3 条加入同一 scope 的 `append_input`）= **1 次 session.init**（pre-Wave-2 会产生 3 次）。
4. [x] **灰度观察窗（部署后 30 min — 2026-04-22 22:55 ~ 23:25 CST）**：
   - `im_aggregated_fallback_total` 保持 0。无告警。
   - `outbox_backlog_count` gauge 未升高。
   - 日志无 `event=im_aggregate ... fallback_reason=dispatch_error` 出现。
4. **负面信号**：
   - 如果出现 `im_aggregated_fallback_total{reason=dispatch_error}` 持续增长 → 先开 `IM_AGGREGATION_WINDOW_SEC=0` 回退 pre-Wave-2，再定位 assemble/dispatch 对 multi-id 的哪个路径出错。
   - 如果 `subscriber_delivered_total{trigger=user_message}` 分布骤降到"只剩少量" → 合批把多条计作一次 delivered，属于预期；与之相对 `im_aggregated_total` 应同比上升。
5. **kill switch 验证**：部署后临时 `export IM_AGGREGATION_WINDOW_SEC=0 && restart subscriber` 回滚一次，确认日志里再也不出现 `event=im_aggregate`，单条 `event=subscriber_delivered` 回归。

## 风险 / 边界

1. **合批延迟问题**：父工单 §风险 1 已定性—— `peek_same_agent_same_sender` 的语义是"当前 batch 内已经积的"，**不等后续消息**。Wave 2 进一步收敛到 "同一个 claim 返回的 50 行里分组"，更保守：**单条消息零额外延迟**；只有当 subscriber 一次 claim 就拿到 ≥2 条匹配行时才合批，那些匹配行本来就已经在 outbox 里排队了（入表时刻相近，未被 poll 到过）。合批没给它们**多加**任何延迟，只是省了重复的 session.init。
2. **跨 claim tick 的连发不合批**：如上所述，这个场景要么 scope 已活（`buffered`），要么 scope 刚启动（`saga_started`）—— 前者 PR-20 逐条 `append_input` 已经解决，后者必然在同一 claim batch 里，Wave 2 能覆盖。**不存在需要跨 tick 合批的真实场景**。
3. **顺序保证**：`_group_for_aggregation` 是贪心前向扫描。非合批行在结果里的相对位置与原 batch 一致；合批组内部也保持 outbox-id ASC。LLM 看到的 `message_ids` 顺序 = outbox-id 顺序 = 用户发送顺序（`created_at` 同方向）。
4. **幂等兼容 PR-52**：PR-52 对 `attempts>0` 行做 `_check_stale_claim`。Wave 2 明确**不合批 retry 行** —— 这是设计而不是妥协：合批里混一个老 retry 行会让 `assemble_sync` 的 message_ids 集合包含一个已经被另一个 dead/live scope claim 的消息，产生语义坏账。散回 per-row 让两个 feature 各自干净。
5. **subagent_id 回退**：`_resolve_continuity` 用 `row.get("subagent_id") or f"main-{agent_id[:8]}"` 对第一条行的 subagent 定位。合批 3 条用户消息时，所有 3 条都来自同一 agent，`subagent_id` 字段在 outbox 行里是空的（`main-{agent_id[:8]}` 回退），和 pre-Wave-2 单行路径行为一致，PR-45 consumer 端看到的 subagent 是同一个 main。
6. **指标标签**：`im_aggregated_total{count}` 的 `count` 是 label 而非 value，方便按分布查询；不合适做 histogram（要么 count=2，要么 count=3，要么 count=10，离散基数很小）。

## 承诺登记

- **R9 IM layer**：从"每条消息独立触发 session.init"升级到"按 outbox claim batch 节奏合批"，匹配 IM 产品语义。
- **R8 + R10**：合批后 `message_ids` 仍是 runtime 消费端可信的唯一 id 集合（SSOT），合批本身不破坏 R10 —— `scope.meta.input_message_ids` 仍由 dispatch/session.init 透传，非消费端扫表。

## 备注

- **Entangled 新 API 保留选项**：如果未来观测到大量跨 claim tick 的连发（实测 metric：`outbox_claim_batch_size` histogram + 同 agent 跨 batch 的相关性分析），再走父工单原设计加 `peek_same_agent_same_sender` / `claim_many`。**Wave 2 现方案零迁移成本，容易扩展**。
- **SUBAGENT_SEND 合批扩展点**：把 `_AGGREGATABLE_TRIGGERS` 加上 `SUBAGENT_SEND`，并在 `_group_for_aggregation` 的同组判定里替换 `agent_id` 键为 `(agent_id, source_subagent_id)` —— 需要从 chat_messages 或 outbox payload 拿 `source_subagent_id`，成本略增，等 prod 信号再做。
