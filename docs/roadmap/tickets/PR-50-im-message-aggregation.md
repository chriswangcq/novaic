# PR-50  IM 消息聚合 / 截断：把"几条连发"合成"一条对话" + 历史窗口上限

| 字段 | 值 |
| --- | --- |
| **Phase** | UX-side optimization（不是正确性 bug，是"观感 + 成本"问题） |
| **Milestone** | R9 IM stream layer 完形 |
| **承诺** | R9（IM 语义一致性） |
| **Status** | `[~]` — Wave 1（B: CHAT_HISTORY 字节 cap + TRUNCATED marker）已实现 + 11 单测全绿；Wave 2（A: business outbox 聚合窗口）延后独立 PR |
| **Depends on** | PR-38（IM 渲染）、PR-44（wake IM replay）、PR-46（by-ids 装配） |
| **Blocks** | — |
| **估时** | 0.5–1 d |
| **Owner** | __ |
| **PR 标题** | `feat(runtime): aggregate same-sender IM bursts within window; cap replay window size` |

## 事件摘要

04-22 观察到：

1. 用户**连发多条短消息**（`hi hi` → 3 秒后 → `现在几点了`），当前 runtime 会触发 2 次独立 dispatch、2 个 scope、2 次 session.init。LLM 第一次还没回，第二条又来，于是 LLM 看到"11 条旧 + 2 条新"（如果 PR-46 未上的话），或者"2 条新分两轮处理"（PR-46 上了之后）。任一情况都不符合真实对话语义——**真实对话里这两条应当合并**。
2. `<CHAT_HISTORY>` 回放无上限：PR-44 当前默认回放 K=10 条已读消息；随着 agent 长期对话累积，历史数据增长超过想象（长尾用户 >1000 条），回放 10 条是粗略 cap，但**没按字节 cap**——一条巨长的 attachment 描述就能把窗口撑爆。

### 引用你自己的"IM 聊天工具类似 product" 理解

- IM 聊天产品里，用户"连珠炮"发消息通常是**语义上的一句话**。agent 应当**等一个静默窗口（~60s）再回复**，或者至少把窗口内消息聚合成一次 LLM 输入。
- 现状：dispatch 以消息为粒度，没有聚合窗口。对人眼看是"3 秒连发"，对 agent 是"立即醒两次"。

### 现状代码定位

- DispatchAssembler `assemble_sync(trigger, agent_id, message_ids=[...])`：已支持 multi-id，但上游**没人真的传 multi-id**——DispatchSubscriber `_deliver_one_inner` 每次只处理 outbox 的单条 row。
- `handle_context_read`：PR-46 之后按 message_ids 精确装配；没有聚合逻辑。
- `<CHAT_HISTORY>` replay in `context_handlers.py`：按条数 K 取，没字节 cap。

## 方案

分三个独立的小优化，打包进一个 PR：

### A. IM 聚合窗口：subscriber 端 60s 同 sender 合批

在 `DispatchSubscriber` 端引入**短延迟合批**：

```python
# dispatch_subscriber.py（示意）
IM_AGGREGATION_WINDOW_SEC = int(os.environ.get("IM_AGGREGATION_WINDOW_SEC", 60))
IM_AGGREGATION_MAX_BATCH = int(os.environ.get("IM_AGGREGATION_MAX_BATCH", 10))

def _deliver_one_inner(self, row, payload):
    trigger = TriggerType.from_legacy(row["trigger_type"])

    # 只对"会话型"trigger 聚合，避免把 SYSTEM_WAKE 之类也聚合了
    if trigger not in {TriggerType.USER_MESSAGE, TriggerType.SUBAGENT_SEND}:
        return self._dispatch_single(row, payload)

    # 窥视本 agent 同类型 outbox 里最近 WINDOW 秒内、同 sender 的其他 row
    peers = self.outbox_repo.peek_same_agent_same_sender(
        agent_id=row["agent_id"],
        sender_fingerprint=self._sender_fingerprint(row),
        within_seconds=IM_AGGREGATION_WINDOW_SEC,
        limit=IM_AGGREGATION_MAX_BATCH,
    )
    # 如果只有自己，直接走
    if len(peers) <= 1:
        return self._dispatch_single(row, payload)

    # 多条：一起 claim、一起 dispatch、一次 session.init
    claimed = self.outbox_repo.claim_many([p["outbox_id"] for p in peers])
    message_ids = [p["message_id"] for p in claimed]
    metadata = dict(payload.get("metadata") or {})
    metadata["im_aggregated"] = True
    metadata["im_aggregated_count"] = len(claimed)
    req = self.assembler.assemble_sync(
        trigger,
        row["agent_id"],
        message_ids=message_ids,       # 一次带走多条
        metadata=metadata,
        idempotency_key=f"agg:{message_ids[0]}:{message_ids[-1]}",
    )
    self.assembler.dispatch_sync(req)
    metric_inc("im_aggregated_total", count=len(claimed))
```

**关键设计**：

1. **window 60s**：拍脑袋但基于"正常人连发消息的节奏 5–30s"。值配置化。
2. **max_batch 10**：即便用户贴了 100 条，一次最多合 10，防止单次 session.init 过载。剩下的下一轮 outbox 轮询继续合批。
3. **幂等 key 变了**：从 `msg:{id}` 改为 `agg:{first}:{last}`，保证同一批多次投递时不重复 dispatch。
4. **agent 正在 running scope 时走 buffered**：当前 buffered 分支已经能把多条 message_ids 一次性 `append_scope_input`；本改动主要影响**新开 scope** 的聚合。
5. **向后兼容**：`IM_AGGREGATION_WINDOW_SEC=0` 退回旧行为（不聚合）。

### B. `<CHAT_HISTORY>` 字节 cap + 条数 cap

PR-44 当前只按条数（K=10）。补字节 cap：

```python
# context_handlers.py（PR-44 的扩展）
WAKE_IM_REPLAY_MAX_BYTES = int(os.environ.get("WAKE_IM_REPLAY_MAX_BYTES", 16 * 1024))  # 16 KiB
WAKE_IM_REPLAY_MAX_COUNT = int(os.environ.get("WAKE_IM_REPLAY_MAX_COUNT", 10))

def _render_chat_history(messages: list[dict]) -> str:
    out = []
    used = 0
    # 倒序取最近的，直到字节 cap；最后再按时间 ASC 输出
    for msg in reversed(messages[-WAKE_IM_REPLAY_MAX_COUNT:]):
        rendered = _render_im_content(msg, ...)
        if used + len(rendered.encode("utf-8")) > WAKE_IM_REPLAY_MAX_BYTES:
            out.append(f"<TRUNCATED n_omitted={...}>")
            break
        out.append(rendered)
        used += len(rendered.encode("utf-8"))
    return "\n".join(reversed(out))
```

**为什么双 cap**：条数 cap 保证窗口可预测；字节 cap 保证 token 预算不爆。

### C. Metric + 日志

- `im_aggregated_total{count}`：聚合批的大小分布
- `im_aggregated_missed_total`：agent 已在 running scope（走 buffered）时，本可以聚合但没走合批路径的次数——指导未来是否在 buffered 路径也做聚合
- `wake_im_replay_truncated_total{reason=bytes|count}`

日志：

- `event=im_aggregate agent=X window=60 count=3 ids=[...]`
- `event=chat_history_truncate reason=bytes used=16384`

## 范围

### business
- `novaic-business/business/repos/outbox_repo.py`：加 `peek_same_agent_same_sender` + `claim_many`
- `novaic-business/business/subscribers/dispatch_subscriber.py`：加聚合分支
- `novaic-business/tests/test_outbox_aggregation.py`

### runtime
- `novaic-agent-runtime/task_queue/handlers/context_handlers.py`：`<CHAT_HISTORY>` 字节 cap
- `novaic-agent-runtime/tests/test_wake_im_replay_bytes_cap.py`

### common
- `novaic-common/common/wake/` 如有共享渲染 util，同步字节 cap 逻辑

### env
- `IM_AGGREGATION_WINDOW_SEC`（默认 60）
- `IM_AGGREGATION_MAX_BATCH`（默认 10）
- `WAKE_IM_REPLAY_MAX_BYTES`（默认 16384）
- `WAKE_IM_REPLAY_MAX_COUNT`（默认 10）

## 实施 Checklist

### A. 聚合（**Wave 2 — 延后独立 PR**）
> 本 wave 跨父仓 runtime + submodule `novaic-business` 两端，需要 outbox repo 新增两个 SQL API、subscriber 重写 deliver 逻辑、跨 subscriber 并发幂等测试。单独一张票更清晰，与 Wave 1 解耦上线；Wave 1 的 byte cap 独立就有价值（防 token 预算爆破），不阻塞 Wave 2 周期。

- [ ] `outbox_repo.peek_same_agent_same_sender` 实现
- [ ] `outbox_repo.claim_many` 原子 claim（单 SQL UPDATE ... WHERE id IN(...)）
- [ ] `_deliver_one_inner` 聚合分支
- [ ] 幂等 key 改为 `agg:{first_id}:{last_id}`（单条时仍用 `msg:{id}`）
- [ ] env `IM_AGGREGATION_WINDOW_SEC` / `IM_AGGREGATION_MAX_BATCH`
- [ ] metric `im_aggregated_total{count}`

### B. CHAT_HISTORY cap — 已实现（Wave 1）
- [x] `_budget_trim` 新增 `max_bytes` 参数 + 返回值扩展为 4 元组 `(kept, tokens, bytes, reason)`
  - 实现：`novaic-agent-runtime/task_queue/handlers/context_handlers.py`
  - 按字节（UTF-8）优先于 token 判定，捕获中日韩 / base64 等 token 估算严重失准的负载
- [x] `_replay_max_bytes()` helper + env `WAKE_REPLAY_MAX_BYTES`（默认 `16*1024 = 16384`；`0` 关闭）
- [x] `_build_wake_replay_block` 当 truncation 发生时：
  - 在 replay 块头部插入一条 `<CHAT_HISTORY_TRUNCATED n_omitted=N reason=bytes|tokens|count/>` system 消息
  - `_message_type="WAKE_IM_REPLAY_TRUNCATED"`，`_metadata` 带 reason + n_omitted
  - 退化 case（kept=[]）仍 emit metric + log，保证 ops 看到信号
- [x] metric `wake_im_replay_truncated_total{reason}`
- [x] log `event=chat_history_truncate agent=<x> reason=<bytes|tokens> n_omitted=N bytes_used=... tokens_used=... kept=...`

### C. 单测（**Wave 2 聚合部分延后**）
- [ ] 3 条同 sender 30s 内连发 → 一次 dispatch 带 3 个 message_ids（Wave 2）
- [ ] 3 条同 sender 但跨 > 60s → 分两次 dispatch（Wave 2）
- [ ] 3 条不同 sender → 各自独立 dispatch（Wave 2）
- [ ] 窗口内 15 条 → 前 10 合批、剩 5 条下一轮合批（Wave 2）
- [ ] 聚合幂等（重复 claim_many 不重复 dispatch）（Wave 2）
- [ ] `IM_AGGREGATION_WINDOW_SEC=0` → 完全关闭，回退老行为（Wave 2）
- [x] `_budget_trim` 字节 cap 先于 token cap 触发（CJK 30KB）
- [x] `_budget_trim` token cap 在 max_bytes=0 时仍生效
- [x] `_budget_trim` 两 cap 都 0 返回空
- [x] `_budget_trim` 走最新→最旧顺序（保留 newest turns）
- [x] `_replay_max_bytes` env plumbing（default / override / invalid / zero）
- [x] `_build_wake_replay_block` truncation 时 emit marker + metric + log
- [x] `_build_wake_replay_block` 不 truncation 时不插 marker
- [x] `_build_wake_replay_block` kept=[] 极端 case 下 metric + log 仍记录

### D. 回归 — 全绿
- [x] PR-38 渲染测试（IM 头、sender_kind）
- [x] PR-44 wake replay 测试（已更新 `_budget_trim` 4 元组签名）
- [x] PR-46 by-ids 装配测试
- [x] PR-47 age cap + Entangled 状态机测试
- [x] PR-48 Turn Finalizer 测试
- [x] PR-49 subagent_rest executor 测试
- [x] novaic-agent-runtime 全套 210 / 210（排除 2 个与 PR-50 无关的 throughput perf floor 脆弱测）

## 验收

### 本地
```bash
cd novaic-business && ./run_tests.sh tests/test_outbox_aggregation.py tests/test_dispatch_subscriber.py
cd novaic-agent-runtime && ./run_tests.sh tests/test_wake_im_replay_bytes_cap.py tests/test_wake_im_replay.py
```

### 线上
```bash
# 1. 连发 3 条短消息（5s 间隔）
# 2. 验证只触发 1 次 session.init
grep 'event=session_init' /opt/novaic/data/logs/runtime-*.log | tail -3
# 预期：只看到 1 条，对应 3 个 message_ids

# 3. 验证聚合 metric
curl -s localhost:9090/metrics | grep im_aggregated_total
# 预期：count=3 的 counter 有 +1

# 4. 验证 CHAT_HISTORY 截断
grep 'event=chat_history_truncate' /opt/novaic/data/logs/runtime-*.log | tail -3
```

## 部署 Checklist（必走）

1. 代码合入父仓 main（含 runtime + business submodule bump）
2. `./deploy services` + `./deploy runtime`
3. 线上证据 ≥ 2 段：
   - 连发测试：3 条短消息 → 1 次 session.init（日志 + SQL scope 表只增 1 行）
   - `im_aggregated_total{count="3"}` 计数 ≥ 1
   - `wake_im_replay_truncated_total{reason="bytes"}` 在长对话 agent 上 > 0
4. 负向：bake 1 周观察 agent 响应延迟是否退化（聚合窗 60s 会让"单条消息"最多延迟 60s 才被处理；必要时收窄到 30s）

## 风险 / 讨论

1. **60s 窗口导致单条消息延迟**：
   - 当前实现是"outbox 队列里**已经看到后续消息**才合批"。如果 60s 内**没有**后续消息，不会等，立即单条 dispatch。所以"单条消息延迟 0"，"连发才合批"。
   - `peek_same_agent_same_sender(within_seconds=60)` 的语义是"往后 peek 看看 outbox 里已经积的"，不是"等 60s"。
2. **合批后 LLM 上下文里的 user message 渲染**：
   - 仍是多条独立的 `role=user` 消息，只是一次性喂给 LLM。LLM 自然能看出 "用户连发了 3 句"。
   - 不要合并成"一条包含三段"的消息——破坏 IM 事件流语义（PR-38 承诺）。
3. **DispatchSubscriber 改造对其它 trigger 的影响**：严格限定只对 `USER_MESSAGE / SUBAGENT_SEND` 聚合；其他 `SYSTEM_WAKE / RECOVERED` 依旧单条走——这些本来就是低频事件。
4. **claim_many 的并发安全**：单 SQL `UPDATE ... WHERE id IN (...) AND claimed_at IS NULL` 原子性 OK；多个 subscriber 实例并发时 SQLite 的 rowlock 机制保证 at-most-once。
5. **chat_history TRUNCATED 提示给 LLM 的语义**：LLM 看到 `<TRUNCATED n_omitted=7>` 可能理解成"这里还有 7 条我看不见"。正确行为：**当用户提及早期历史时主动让用户提醒**。prompt 层可补一条约定。本 PR 不管 prompt。
6. **sender_fingerprint 怎么算**：
   - USER_MESSAGE：`user_id`
   - SUBAGENT_SEND：`metadata.source_subagent_id`
   - 其它 trigger：不聚合，fingerprint 不参与

## 承诺登记

- **R9 IM layer**：从"每条消息独立触发"升级到"按对话节奏合批"，匹配 IM 产品语义。
- **成本控制**：聚合后 session.init 次数下降（3 条连发从 3 次 → 1 次），LLM 成本降低；字节 cap 防止长对话 agent 的 replay 膨胀到 token 预算外。

## 备注

- 本 PR 独立上线是安全的，但 **PR-46 先上**：by-ids 装配是聚合路径能正确"一次吃多条"的前提。PR-46 没上时，聚合的 3 条被 `handle_context_read` 的"扫 unread"还是能捞到，但顺序 / 幂等更脆弱。
- IM 聚合未来如果还想做得更细，可以考虑 "sender 打字中" signal（前端发 typing_start / typing_end）来动态调整 window——本 PR 不在范围内。
