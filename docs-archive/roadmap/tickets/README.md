# Message → Wake 执行工单

> 本目录把 [message-wake-refactor.md](../message-wake-refactor.md) 的阶段清单进一步下沉到 **PR 粒度的执行工单**。每个文件 = 一个 PR，按顺序执行可直达 M1/M2/M3/M4 里程碑。
>
> SSOT 层级：
>
> 1. [architecture/message-wake-principles.md](../../architecture/message-wake-principles.md) — **为什么**（R1–R8 承诺）
> 2. [roadmap/message-wake-refactor.md](../message-wake-refactor.md) — **做什么**（阶段 / 条目）
> 3. **本目录** — **怎么做 / 如何验收**（PR 工单 + checklist）

---

## 如何使用

**领工单**：

1. 在 `index` 表找到下一个 `[ ]` 状态、依赖已满足的工单。
2. 打开对应 `PR-NN-*.md` 文件。
3. 按 `前置 → 实施 → 测试 → 可观测 → 文档 → 验收 → 回滚` 顺序逐项勾掉。
4. 写 PR 时，PR 描述直接引用该工单路径（如 `docs/roadmap/tickets/PR-10-dispatch-assembler.md`）。
5. 合并后在本 README 的 index 表把状态改为 `[x]` 并提交。

**Definition of Ready (DoR)**：

- 依赖列的所有 PR 已合并
- 影响范围（Scope）和本地自测命令确认可跑
- 有单测计划

**Definition of Done (DoD)**：

- 实施 checklist 全 `[x]`
- `ReadLints` 干净
- 验收命令通过（粘到 PR 描述里）
- 对应承诺 (R-x) 在 `message-wake-principles.md §五对照表` 里找得到证据
- **部署 Checklist 全 `[x]`（未部署的票不能关）**——每张票在"验收命令"之后必须有一段 "部署 Checklist"，包含：
  1. 代码已合入父仓库 main（含子模块 bump）
  2. 已执行 `./deploy <target>`（gateway / runtime / services / cortex / …，视票的 Scope 选择）
  3. **线上证据 ≥ 2 段**：日志 grep + `/metrics` 计数 + 必要时 SQL 状态 check；直接 paste 进 PR 关单评论
  4. 如有一次性迁移（数据修复脚本），需已在 prod 跑过并留有备份文件名
  ——参考 [PR-41](PR-41-agent-reply-not-orphan-eligible.md#部署-checklist必走不部署不算完成) / [PR-42](PR-42-wake-continuity-inject-handoff.md#部署-checklist必走不部署不算完成) / [PR-44](PR-44-wake-im-stream-replay.md#部署-checklist必走不部署不算完成) 的格式。
  ——血教训：2026-04-21 连做三张票（PR-41/42/44）代码完、测试过、ticket 关单，但**没 push 没部署**，第二天用户又看到 AGENT_REPLY 自苏醒。所以"代码写完"不等于"bug 修复"，只有"线上指标验证生效"才算。

---

## 工单索引

> PR-01..PR-85 and review files are historical archaeology unless a later
> current ticket explicitly reopens them. Old terms such as `message_outbox`,
> `SPAWN_SUBAGENT`, and removed subagent tools are not active architecture or
> backlog items. Historical ticket/review files that mention these terms must
> carry a `Historical ticket archive:` banner.

### 当前执行工单

| ID | Status | 标题 | 依赖 | 承诺 | 预估 | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| PR-234 | `[x]` | [Agent Loop Control-Plane Consistency](PR-234-agent-loop-control-plane-consistency.md) | PR-233 | 显式控制面 / 可恢复 Agent loop | 1 d | Codex |
| PR-234A | `[x]` | [Cortex Authoritative Stack Source](PR-234A-cortex-authoritative-stack-source.md) | PR-234 | 单一 stack SSOT | 0.25 d | Codex |
| PR-234B | `[x]` | [Transient Stack Snapshot Assembly Contract](PR-234B-transient-stack-snapshot-contract.md) | PR-234A | prompt snapshot 不污染 durable context | 0.25 d | Codex |
| PR-234C | `[x]` | [Runtime Tool Logical Failure Semantics](PR-234C-runtime-tool-logical-failure-semantics.md) | PR-234A | `ok:false` 是失败 | 0.25 d | Codex |
| PR-234D | `[x]` | [Repeated Mismatch Breaker And Force-Finalize Semantics](PR-234D-repeated-mismatch-breaker.md) | PR-234C | 治本防循环 | 0.25 d | Codex |
| PR-235 | `[x]` | [Reliable Evolution FSM-01 Baseline & Shadow Ledger](PR-235-reliable-evolution-fsm-shadow-ledger.md) | PR-234D | shadow 事件账 / 状态账 / outbox 表，不切旧主路 | 0.5 d | Codex |
| PR-236 | `[x]` | [Reliable Evolution FSM-02 Pure Decision Shadow](PR-236-reliable-evolution-fsm-pure-decision-shadow.md) | PR-235 | pure FSM decision 对账，不切旧主路 | 0.5 d | Codex |
| PR-237 | `[x]` | [Reliable Evolution FSM-03A Durable Outbox Observe](PR-237-reliable-evolution-outbox-observe.md) | PR-236 | outbox effect 记账，不切 publish | 0.5 d | Codex |
| PR-238 | `[x]` | [Reliable Evolution FSM-04 Generation Checked Attach](PR-238-reliable-evolution-generation-checked-attach.md) | PR-237 | attach 显式 expected scope/generation CAS | 0.5 d | Codex |
| PR-239 | `[x]` | [Reliable Evolution FSM-05A Append-only Inbox Observe](PR-239-reliable-evolution-append-only-inbox-observe.md) | PR-238 | append-only `input_received` 事件账，不切 pending | 0.5 d | Codex |
| PR-240 | `[x]` | [Reliable Evolution FSM-05B Input Consumption Observe](PR-240-reliable-evolution-input-consumption-observe.md) | PR-239 | observe-only input consumed 账，不切 pending | 0.5 d | Codex |
| PR-241 | `[x]` | [Reliable Evolution FSM-05C Pending Inbox Projection Observe](PR-241-reliable-evolution-pending-inbox-projection.md) | PR-240 | unconsumed inbox pending projection 对账，不切 pending | 0.5 d | Codex |
| PR-242 | `[x]` | [Reliable Evolution FSM-05D Strict Input Ledger Boundary](PR-242-reliable-evolution-strict-input-ledger.md) | PR-241 | `input_received` 写入 fail-fast，切流前置条件 | 0.5 d | Codex |
| PR-243 | `[x]` | [Reliable Evolution FSM-05E Inbox Restart Cutover](PR-243-reliable-evolution-inbox-restart-cutover.md) | PR-242 | `session_ended()` restart source 切到 inbox projection | 0.5 d | Codex |
| PR-243A | `[x]` | [Reliable Evolution SQLite Transaction Boundary](PR-243A-reliable-evolution-sqlite-transaction-boundary.md) | PR-243 | 修复全量验证暴露的 shadow ledger 绕 transaction 写和 SQLite thread connection 初始化锁洞 | 0.25 d | Codex |
| PR-244 | `[x]` | [Reliable Evolution FSM-05F Remove Pending Trigger Store](PR-244-reliable-evolution-remove-pending-triggers.md) | PR-243 | 删除 `tq_pending_triggers` 活存储，pending 只来自 append-only inbox | 0.5 d | Codex |
| PR-245 | `[x]` | [Reliable Evolution FSM-06A Suspected-Dead Recovery Event](PR-245-reliable-evolution-suspected-dead-recovery.md) | PR-244 | wake_finalize 失败先写 suspected-dead event，下一次 dispatch 由 session coordinator recovery | 0.5 d | Codex |
| PR-246 | `[x]` | [Reliable Evolution FSM-06B Remove Recovery Marker Path](PR-246-reliable-evolution-remove-recovery-markers.md) | PR-245 | 删除 `tq_session_recoveries` marker 表/consumer，recovery 只从 suspected-dead event 决策 | 0.5 d | Codex |
| PR-247 | `[x]` | [Reliable Evolution FSM-06C Recovery Archive Outbox Cutover](PR-247-reliable-evolution-recovery-outbox-cutover.md) | PR-246 | recovery archive `cortex.scope_end` 走 durable session outbox，删除 direct publish 旁路 | 0.5 d | Codex |
| PR-248 | `[x]` | [Reliable Evolution FSM-06D Attach Input Outbox Cutover](PR-248-reliable-evolution-attach-outbox-cutover.md) | PR-247 | active `session.attach_input` 走 durable session outbox，删除 direct publish 旁路 | 0.5 d | Codex |
| PR-249 | `[x]` | [Reliable Evolution FSM-03B Observed Wake Outbox Cleanup](PR-249-reliable-evolution-observed-wake-outbox-cleanup.md) | PR-248 | observe-only `create_wake_saga` 不再污染 retryable pending outbox backlog | 0.25 d | Codex |
| PR-250 | `[x]` | [Reliable Evolution FSM-03C Observed Wake Effect Rename](PR-250-reliable-evolution-observed-wake-effect-rename.md) | PR-249 | observe-only wake 诊断行改名，避免误读为真实 `create_wake_saga` worker 合约 | 0.25 d | Codex |
| PR-251 | `[x]` | [Reliable Evolution FSM-03D Wake Creation Outbox Cutover](PR-251-reliable-evolution-wake-creation-outbox-cutover.md) | PR-250 | start/restart wake saga creation 走 durable session outbox | 0.5 d | Codex |
| PR-252 | `[x]` | [Reliable Evolution FSM-07A Session State SSOT Cutover](PR-252-reliable-evolution-session-state-ssot.md) | PR-251 | `tq_session_state` 接管 session SSOT，`tq_active_sessions` 降级为 cache/view | 0.5 d | Codex |
| PR-253 | `[x]` | [Reliable Evolution FSM-02B Dispatch Pure FSM Cutover](PR-253-reliable-evolution-dispatch-pure-fsm-cutover.md) | PR-252 | `dispatch()` live 分支迁到 pure FSM decision + interpreter | 0.5 d | Codex |
| PR-254 | `[x]` | [Reliable Evolution FSM-07B Finalize Ownership](PR-254-reliable-evolution-finalize-ownership.md) | PR-253 | finalize 变显式事件，带 reason/generation/remaining_stack，由 FSM 清 active | 0.5 d | Codex |
| PR-255 | `[x]` | [Reliable Evolution FSM-08 Legacy Compat Cleanup](PR-255-reliable-evolution-legacy-compat-cleanup.md) | PR-254 | 清理旧分支/旧命名/旧文档，添加 residue guard | 0.5 d | Codex |
| PR-256 | `[x]` | [Reliable Evolution FSM-09 Architecture Ledger Calibration](PR-256-reliable-evolution-architecture-ledger-calibration.md) | PR-255 | 更新架构账本，移除已过期的 shadow/observe-only/current-state 误导描述 | 0.25 d | Codex |
| PR-257 | `[x]` | [Reliable Evolution FSM-10 Remove Active Sessions Table](PR-257-reliable-evolution-remove-active-sessions-table.md) | PR-256 | 物理移除 `tq_active_sessions` 活表/写入/测试依赖，`tq_session_state` 成为唯一在线状态表 | 0.5 d | Codex |


| ID     | Status | 标题                                                                                                                          | 依赖                                       | 承诺          | 预估                                    | Owner       |
| ------ | ------ | --------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ----------- | ------------------------------------- | ----------- |
| PR-01  | `[x]`  | [common.wake 包骨架](PR-01-wake-package-skeleton.md)                                                                           | —                                        | R2          | 0.5 h                                 | __          |
| PR-02  | `[x]`  | [common.agents.ownership 包骨架](PR-02-ownership-package-skeleton.md)                                                          | —                                        | R3          | 0.5 h                                 | __          |
| PR-03  | `[x]`  | [CI lint：禁止直接 POST /api/queue/dispatch](PR-03-ci-ban-direct-dispatch.md)                                                    | —                                        | R2          | 1 h                                   | __          |
| PR-04  | `[x]`  | [CI lint：禁止裸 httpx.Client()](PR-04-ci-ban-bare-httpx-client.md)                                                             | —                                        | R7          | 1 h                                   | __          |
| PR-05  | `[x]`  | [internal_client(service_name=...) 必填](PR-05-internal-client-service-name.md)                                               | —                                        | R7          | 0.5 d                                 | __          |
| PR-06  | `[x]`  | [服务端消费 X-Internal-Service](PR-06-services-consume-caller-header.md)                                                         | PR-05                                    | R7          | 0.5 d                                 | __          |
| PR-07  | `[x]`  | [Business `GET /internal/agents/{id}/owner](PR-07-business-agent-owner-endpoint.md)`                                        | —                                        | R3          | 0.5 d                                 | __          |
| PR-08  | `[x]`  | [AgentOwnershipResolver (TTL 缓存)](PR-08-agent-ownership-resolver.md)                                                        | PR-01, PR-02, PR-05, PR-07               | R3          | 0.5 d                                 | __          |
| PR-09  | `[x]`  | [TriggerType 权威枚举 + schema 迁移](PR-09-trigger-type-enum.md)                                                                  | PR-01                                    | R2          | 0.5 d                                 | __          |
| PR-10  | `[x]`  | [DispatchAssembler 本体 + 合约测试](PR-10-dispatch-assembler.md)                                                                  | PR-05, PR-08, PR-09                      | R2+R3       | 1 d                                   | __          |
| PR-11  | `[x]`  | [Business `_dispatch_trigger` 迁到 Assembler](PR-11-business-trigger-to-assembler.md)                                         | PR-10                                    | R2          | 0.5 d                                 | __          |
| PR-12  | `[x]`  | [HealthWorker `_scan_unhandled_messages` 迁到 Assembler](PR-12-healthworker-scan-to-assembler.md)                             | PR-10                                    | R2+R3+R7    | 0.5 d                                 | __          |
| PR-13  | `[x]`  | [SchedulerWorker 迁到 Assembler](PR-13-scheduler-worker-to-assembler.md)                                                      | PR-10                                    | R2          | 0.5 d                                 | __          |
| **M1** | —      | **合约对齐 ✅**                                                                                                                  | PR-05..PR-13                             | —           | —                                     | —           |
| PR-14  | `[x]`  | [Entangled `message_outbox` schema](PR-14-entangled-message-outbox.md)                                                      | —                                        | R6          | 1 d                                   | __          |
| PR-15  | `[x]`  | [dispatch_subscriber 骨架（flag=off）](PR-15-dispatch-subscriber-skeleton.md)                                                   | PR-10, PR-14                             | R6          | 0.5 d                                 | __          |
| PR-16  | `[x]`  | [dispatch_subscriber poll + dedupe + retry](PR-16-dispatch-subscriber-full.md)                                              | PR-15                                    | R1+R6       | 1.5 d                                 | __          |
| PR-17  | `[x]`  | [灰度开启 dispatch_subscriber (canary)](PR-17-canary-enable-subscriber.md)                                                      | PR-16                                    | R1          | 0.5 d (bake gate revoked 2026-04-19)  | __          |
| PR-18  | `[x]`  | [删除 Business `_dispatch_trigger](PR-18-remove-dispatch-trigger.md)`                                                         | PR-17                                    | R1+R6       | 0.5 d                                 | __          |
| PR-19  | `[x]`  | [HealthWorker → recovery-only](PR-19-healthworker-recovery-only.md)                                                         | PR-17                                    | R1+R5       | 0.5 d                                 | __          |
| **M2** | —      | **主路径切换 ✅**                                                                                                                 | PR-14..PR-19                             | —           | —                                     | —           |
| PR-20  | `[x]`  | [Scope `meta.input_message_ids](PR-20-scope-input-message-ids.md)`                                                          | PR-10                                    | R4          | 1 d                                   | 2026-04-15  |
| PR-21  | `[x]`  | `[chat_messages.lifecycle` 枚举 + state_transition()](PR-21-message-lifecycle-enum.md)                                        | PR-14                                    | R4+R8       | 1 d                                   | 2026-04-15  |
| PR-22  | `[x]`  | [subscriber 成功 dispatch → transition claimed](PR-22-subscriber-transition-claimed.md)                                       | PR-16, PR-21                             | R4          | 0.5 d                                 | 2026-04-15  |
| PR-23  | `[x]`  | [scope_end → transition inputs to consumed](PR-23-scope-end-consumed.md)                                                    | PR-20, PR-21                             | R4          | 0.5 d                                 | 2026-04-15  |
| PR-24  | `[x]`  | [LogContext contextvar + service-wide bind](PR-24-logcontext-scope-id-binding.md)                                           | PR-20                                    | R4          | 1.5 d                                 | 2026-04-15  |
| PR-25  | `[x]`  | [Business `/internal/messages/{id}/trace](PR-25-message-trace-endpoint.md)`                                                 | PR-21                                    | R4          | 0.5 d                                 | 2026-04-15  |
| PR-26  | `[x]`  | [recovery_worker orphan emitter + metrics](PR-26-orphan-emitter-metrics.md)                                                 | PR-19, PR-21                             | R5          | 1 d                                   | 2026-04-15  |
| PR-27  | `[x]`  | [orphan re-dispatch (trigger_type=recovered)](PR-27-recovered-redispatch.md)                                                | PR-26                                    | R1+R5       | 0.5 d                                 | 2026-04-15  |
| **M3** | —      | **可观测**                                                                                                                     | PR-20..PR-27                             | —           | —                                     | —           |
| PR-28  | `[x]`  | [Subagent 状态机](PR-28-subagent-state-machine.md)                                                                             | M2                                       | R8          | 1.5 d                                 | 2026-04-15  |
| PR-29  | `[x]`  | [Scope 状态机（Cortex）](PR-29-scope-state-machine.md)                                                                           | M2                                       | R8          | 1.5 d                                 | 2026-04-15  |
| PR-30  | `[x]`  | [删除 `chat_messages` 旧字段（窄化：保留 `read`）](PR-30-drop-legacy-message-fields.md)                                                 | PR-21, PR-22, PR-23（稳定 1 release）        | R4+R8       | 0.5 d                                 | 2026-04-15  |
| PR-31  | `[x]`  | `[*_state_transitions` 日志表（+ PR-31b subagent 状态机 server-side 化 + PR-31c 删除死 Counter）](PR-31-state-transition-log-tables.md) | PR-28, PR-29                             | R8          | 1 d                                   | 2026-04-15  |
| PR-32  | `[x]`  | [Metrics 兜底落地（零依赖 registry + 13 条 golden signal）](PR-32-metrics-prometheus-integration.md)                                  | PR-06, PR-07, PR-08, PR-10, PR-14, PR-16 | OBS-3       | 1 d                                   | 2026-04-21  |
| **M4** | —      | **状态机化**                                                                                                                    | PR-28..PR-31                             | —           | —                                     | —           |
| PR-33  | `[x]`  | [env shrink + services.json runtime_switches](PR-33-env-shrink.md)                                                          | PR-17                                    | R-FAIL-LOUD | 1 d（2026-04-20 六阶段一轮落地）               | __          |
| PR-34  | `[x]`  | [Worker 同步化（34a-34e 五步分 PR）](PR-34-worker-sync.md)                                                                          | PR-33（并行 mergeable）                      | 系统简单        | 5 × 0.5 d（2026-04-19/20 bake gate 撤销） | __          |
| PR-35  | `[x]`  | [chat_reply 静默 400 双层防御（hotfix）](PR-35-silent-fail-runtime-fill-defaults.md)                                                | —                                        | 无静默失败       | 0.5 d（2026-04-19 prod 上线）             | wangchaoqun |
| PR-36  | `[x]`  | [用户消息顺序修复（messages 默认 ASC）](PR-36-messages-default-order-asc.md)                                                            | —                                        | 无静默失败 / 简单 | 0.25 d（2026-04-22 完成）                 | wangchaoqun |
| PR-37  | `[x]`  | [No-tool warning 显式信号通道](PR-37-no-tool-warning-explicit-signal.md)                                                          | —                                        | 显式 > 隐式    | 0.25 d（2026-04-22 完成）                 | wangchaoqun |
| PR-38  | `[x]`  | [IM 消息渲染（sender / timestamp / msg_id header）](PR-38-im-message-rendering.md)                                                | PR-36                                    | 事件 > 片段    | 0.5 d（2026-04-22 完成）                  | wangchaoqun |
| PR-39  | `[x]`  | [Context assembly 真·DFS（scope_id 匹配 + 嵌套 fold）](PR-39-context-assembly-dfs-recursion.md)                                    | —                                        | 一致性        | 0.5 d（2026-04-22 完成）                  | wangchaoqun |
| PR-40  | `[x]`  | [Entangled id 兜底删除 + chat_reply 显式填 id（fail-fast，chat_reply UNIQUE 根治）](PR-40-entangled-id-fallback-scope-key-collision.md)                       | —                                        | 无静默失败 / fail-fast  | 0.5 d（2026-04-21 完成）             | wangchaoqun |
| PR-41  | `[x]`  | [AGENT_REPLY 等非 wake-trigger 消息不再进入 orphan 候选（止血：5 分钟自动苏醒误循环）](PR-41-agent-reply-not-orphan-eligible.md) | PR-21, PR-26                        | R4 + R8 + 止血           | 0.5 d                        | __          |
| PR-42  | `[x]`  | [Wake 时注入 handoff_notes + historical_summary 到新 scope（R9 文字层）](PR-42-wake-continuity-inject-handoff.md) | PR-13, PR-20                        | R9（新增）                | 1 d                          | __          |
| PR-43  | `[✓]`  | [Scope 续链 previous_scope_id + cortex assembly 读上一次 scope 尾部 K 步（R9 状态层）](PR-43-scope-chain-previous-id.md) **— implemented, then retired from main path by PR-69** | PR-20, PR-29, PR-39, PR-42          | R9 + R4                 | 2–3 d                        | archived          |
| PR-44  | `[x]`  | [Wake 首轮 IM 流回放（最近 K 条 chat_messages 前置注入）](PR-44-wake-im-stream-replay.md) | PR-38, PR-42                        | R9 + R4                 | 0.5–1 d（2026-04-21 完成）                      | wangchaoqun          |
| PR-45  | `[✓]`  | [Wake continuity 文字层 producer→consumer 接线（subagent_rest saga 持久化 historical_summary + DispatchSubscriber/HealthWorker 注入 continuity + 幂等清除 + kill switch）— **Wave 1A–E deployed 2026-04-22；Wave 1F review 完成 2026-04-24；PR-45.1 观测性补丁 `event=continuity_resolve` 3 条 info log + 4 测 2026-04-24 合入等部署**，[review 笔记](reviews/PR-45-review.md)](PR-45-wake-continuity-text-producer-wiring.md) | PR-28, PR-42                        | R9 + R10                | 1–2 d（Wave 1A–E 已落 2026-04-22）              | wangchaoqun          |
| PR-46  | `[✓]` | [context.read 按 `payload.message_ids` 精确装配（废除"扫 agent pending" 反模式，根因 A）](PR-46-context-read-by-message-ids.md) **— deployed 2026-04-22** | PR-20, PR-21, PR-38                 | R2 + R4 + R9             | 0.5–1 d                     | __          |
| PR-47  | `[✓]` | [老毒 USER_MESSAGE 清理 + HealthWorker recovery age cap（根因 B）](PR-47-orphan-recovery-age-cap-and-cleanup.md) **— deployed 2026-04-22; migration ran no-op (pool already empty)** | PR-27, PR-46                        | R5 + R1                  | 0.5 d                        | __          |
| PR-48  | `[✓]` | [Turn Finalizer：LLM 回复后强制收敛 scope（chat_reply → auto rest / skill_end 兜底，根因 D）](PR-48-turn-finalizer-force-rest.md) **— deployed 2026-04-22** | PR-28, PR-29, PR-45                 | R8 + R9                  | 1 d                          | __          |
| PR-49  | `[✓]` | [`subagent_rest` tool executor（PR-45 Wave 1.5，根因 C：让 LLM 自述 handoff_notes 真落地）](PR-49-subagent-rest-executor.md) **— deployed 2026-04-22** | PR-45, PR-28                        | R9 + R8                  | 0.5 d                        | __          |
| PR-50  | `[✓]`  | [IM 消息聚合 60s 合批 + `<CHAT_HISTORY>` 字节 cap（根因 F）— **Wave 1 + Wave 2 deployed**](PR-50-im-message-aggregation.md) | PR-38, PR-44, PR-46                 | R9                      | 0.5–1 d                     | closed          |
| PR-50 Wave 2 | `[✓]` | [IM outbox burst 聚合（claim batch 内分组，subscriber only，无 Entangled 改动）— deployed to prod 2026-04-22 22:55 CST](PR-50-wave-2-im-aggregation.md) | PR-50, PR-14, PR-20, PR-22, PR-45, PR-46, PR-52 | R9                      | 0.5 d                       | closed          |
| PR-51  | `[✓]`  | [卡住的 `claimed` 行回收 + HealthWorker 周期扫描 — **Part 1 migration 清 25/28 rows；Part 2 HealthWorker scan + endpoints deployed to prod 2026-04-23**](PR-51-stuck-claimed-cleanup.md) | PR-21, PR-27, PR-41 amend           | R5                      | 1 d                         | __          |
| PR-52  | `[✓]`  | [subscriber 重试路径 scope-aliveness 护栏 — **deployed to prod 2026-04-23 18:48 CST**；阻止死 scope 被 re-materialized，配合 PR-51 Part 2 scanner 防新洞+清老洞](PR-52-subscriber-scope-aliveness-check.md) | PR-22, PR-51 Part 2                 | R5                      | 0.5 d                       | __          |
| P6-12  | `[✓]`  | [`chat_messages.read` 降级为 UI-only 字段 — 契约 + CI 强制（`scripts/ci/lint_chat_messages_read.sh`）+ survivor 审计 + 4 个僵尸 Business 路由贴弃用标记；2026-04-24 落地](P6-12-chat-messages-read-ui-only.md) | PR-46, P6-11                        | R10                      | 0.5 d                       | __          |
| PR-55  | `[✓]`  | [Retire phantom `subagent_rest` / `historical_summary` / `handoff_notes` pipeline](PR-55-phantom-summary-pipeline-cleanup.md) **— closed by later agent-root / wake-finalize cleanup and guardrails** | PR-42, PR-45, PR-49, PR-53 (supersedes all) | R9 + R-ZOMBIE            | 1–1.5 d                     | closed          |
| PR-56  | `[✓]`  | [LLM system prompt must not reference tools absent from the call schema](PR-56-llm-prompt-phantom-tools.md) **— deployed 2026-04-25** | — | LLM contract | 0.5 d | __ |
| PR-57  | `[✓]`  | [LLM memory wording must match the active R9 scope-continuity contract](PR-57-llm-memory-contract-drift.md) **— deployed 2026-04-25** | PR-55 | R9 + LLM contract | 0.5 d | __ |
| PR-58  | `[✓]`  | [Root scope summaries must be future-self summaries, not pasted user-facing replies](PR-58-root-scope-summary-quality.md) **— deployed 2026-04-25** | — | R9 | 0.5–1 d | __ |
| PR-59  | `[✓]`  | [`<PREV_SCOPE_HISTORY>` and `<PREV_SCOPE_TAIL>` should not duplicate the same short prior turn](PR-59-prev-scope-history-tail-duplication.md) **— deployed 2026-04-25** | PR-58 | R9 + context budget | 0.5 d | __ |
| PR-60  | `[✓]`  | [User IM content must render as clean user text, not a Python dict string](PR-60-im-user-content-clean-body.md) **— deployed 2026-04-25** | PR-38 | IM rendering | 0.5 d | __ |
| PR-61  | `[✓]`  | [`subagent_report` must not be exposed to agents that cannot validly call it](PR-61-contextual-tool-visibility-subagent-report.md) **— deployed 2026-04-25** | — | Tool contract | 0.5 d | __ |
| PR-62  | `[✓]`  | [LLM request builder should not send null optional generation parameters](PR-62-llm-request-null-parameter-pruning.md) **— deployed 2026-04-25** | — | Provider compatibility | 0.25 d | __ |
| PR-63  | `[✓]`  | [LLM-visible `shell` capability needs an explicit safety boundary](PR-63-shell-tool-safety-boundary.md) **— deployed 2026-04-25** | — | Safety + ops | 0.5 d | __ |
| PR-64  | `[✓]`  | [Purge legacy 小牛 scope/runtime data before agent-root rollout](PR-64-purge-legacy-xiaoniu-scope-data.md) **— operational cleanup completed 2026-04-25** | — | R9 reset | 0.25 d | __ |
| PR-65  | `[✓]`  | [Introduce long-lived agent root scope lifecycle](PR-65-agent-root-scope-lifecycle.md) **— runtime foundation deployed + smoke-verified 2026-04-25** | PR-64 | R9 + Cortex | 1 d | __ |
| PR-66  | `[✓]`  | [Make system-created child scopes render through the DFS step tree](PR-66-step-tree-first-system-scope-rendering.md) **— Cortex deployed + smoke-verified 2026-04-25** | PR-65 | Cortex DFS | 1 d | __ |
| PR-67  | `[✓]`  | [Rewire wake lifecycle so each wake is a child scope under agent root](PR-67-wake-as-agent-root-child-scope.md) **— Runtime+Cortex deployed + smoke-verified 2026-04-25** | PR-65, PR-66 | R9 + Runtime | 1–2 d | __ |
| PR-68  | `[✓]`  | [Restore `summary.md` semantics to scope-end report only](PR-68-summary-md-scope-end-report-only.md) **— Runtime+Cortex deployed + smoke-verified 2026-04-25** | PR-67 | Memory correctness | 0.5 d | __ |
| PR-69  | `[✓]`  | [Retire `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` from the main LLM path](PR-69-retire-prev-scope-history-tail-from-main-path.md) **— Runtime deployed + smoke-verified 2026-04-25** | PR-67, PR-68 | R9 cleanup | 0.5–1 d | __ |
| PR-70  | `[✓]`  | [Delete Runtime-derived wake memory; keep explicit child-skill summary only](PR-70-explicit-child-skill-summary-only.md) **— Runtime+Cortex deployed + smoke-verified 2026-04-27** | PR-65..PR-69 | Memory correctness | 0.5–1 d | __ |
| PR-71  | `[✓]`  | [Keep no-tool retry attempts out of canonical LLM context](PR-71-no-tool-retry-private-context-cleanup.md) **— Runtime deployed + smoke-verified 2026-04-27** | PR-70 preferred | Context correctness | 0.5 d | __ |
| PR-72  | `[✓]`  | [Align prompt and tool contract with agent-root continuity](PR-72-agent-root-prompt-contract-cleanup.md) **— Runtime+Business deployed + smoke-verified 2026-04-27** | PR-70, PR-71 | Prompt contract | 0.5 d | __ |
| PR-73  | `[✓]`  | [Improve folded-scope rendering and empty-summary policy](PR-73-folded-scope-rendering-and-empty-summary-policy.md) **— Cortex deployed + smoke-verified 2026-04-27** | PR-70 | LLM input quality | 0.5 d | __ |
| PR-74  | `[✓]`  | [Delete Cortex auto-summary / Compactor path](PR-74-cortex-delete-compactor-auto-summary.md) **— Cortex deployed + smoke-verified 2026-04-27** | PR-70, PR-73 | Cortex boundary + memory correctness | 0.5–1 d | __ |
| PR-75  | `[✓]`  | [Remove BusinessProxy memory/task surfaces from Cortex](PR-75-remove-cortex-business-proxy-memory-task.md) **— Cortex deployed + smoke-verified 2026-04-27** | PR-74 preferred | Cortex ownership boundary | 0.5–1 d | __ |
| PR-76  | `[✓]`  | [Add Cortex boundary guardrails](PR-76-cortex-boundary-ci-guardrails.md) **— local guard + Cortex tests verified 2026-04-27** | PR-74, PR-75 | Regression prevention | 0.5 d | __ |
| PR-77  | `[✓]`  | [Tighten LLM tool descriptions around child-skill summaries](PR-77-llm-tool-description-child-skill-contract.md) **— Business+Runtime+Cortex deployed + smoke-verified 2026-04-27** | PR-74 preferred | Tool contract + agent behavior | 0.5 d | __ |
| PR-78  | `[✓]`  | [Make wake the LLM-closed turn scope and remove meta skill](PR-78-wake-scope-close-no-meta-skill.md) **— Cortex+Runtime+Business deployed + smoke-verified 2026-04-28** | PR-67, PR-73, PR-77 | Continuity correctness + tool contract | 0.5–1 d | __ |
| PR-79  | `[✓]`  | [Rename runtime `subagent_rest` to `wake_finalize`](PR-79-rename-subagent-rest-to-wake-finalize.md) | PR-78 | Conceptual cleanup | 0.5 d | closed |
| PR-80  | `[✓]`  | [Enforce single summary writer: only `skill_end(report=...)`](PR-80-scope-end-no-report-contract.md) | PR-78, PR-79 | Memory correctness | 0.5 d | closed |
| PR-81  | `[✓]`  | [Remove old rest/meta wording from active docs and guardrails](PR-81-finalize-docs-and-guardrails.md) | PR-79, PR-80 | Regression prevention | 0.5 d | closed |
| PR-83  | `[✓]`  | [Purge non-minimal continuity residues from active paths](PR-83-purge-non-minimal-continuity-residues.md) **— closed by PR-70/79/80/81/113/114 and PR-140..146 guardrails** | PR-78; may absorb PR-79/81 | P0 continuity cleanup | 0.5-1 d | closed |
| PR-84  | `[✓]`  | [Add Cortex minimal-structure invariant tests](PR-84-cortex-minimal-structure-invariants.md) | PR-82, PR-83 preferred | P0 structure guardrails | 0.5-1 d | closed |
| PR-85  | `[✓]`  | [Add LLM context smoke guardrails for the minimal structure path](PR-85-llm-context-minimal-structure-smoke-guardrails.md) | PR-82, PR-83, PR-84 preferred | P0 smoke guardrails | 0.5-1 d | closed |
| PR-86  | `[✓]`  | [Define execution-log lightweight metadata contract](PR-86-execution-log-light-metadata-contract.md) **— Runtime+App deployed + production smoke verified 2026-04-29** | PR-78+ | Entangled/App observability | 0.5-1 d | __ |
| PR-88  | `[closed-retired]`  | [Complete `log-payloads` lazy fetch and merge into App log view](PR-88-log-payload-lazy-fetch-and-app-cache-merge.md) **— superseded by PR-154A + PR-166C; do not treat as active path** | PR-86 preferred | Payload drilldown | 0.5-1 d | retired |
| PR-89  | `[✓]`  | [Expose LLM Factory log join key in think execution logs](PR-89-llm-factory-log-id-entangled-join.md) **— Runtime+App deployed + production smoke verified 2026-04-29** | PR-86 preferred | LLM Factory join | 0.5 d | __ |
| PR-90  | `[✓]`  | [Correct execution-log status semantics and add minimal lifecycle events](PR-90-execution-log-status-and-lifecycle-events.md) **— Runtime+App deployed + tests/smoke verified 2026-04-29** | PR-86 preferred | Timeline correctness | 0.5-1 d | __ |
| PR-91  | `[✓]`  | [Align Entangled client cache docs and guardrails with actual App cache](PR-91-entangled-client-cache-docs-and-guardrails.md) **— Docs/guardrail + Entangled client tests verified 2026-04-29** | PR-86 optional | Docs / guardrails | 0.25-0.5 d | __ |
| PR-92  | `[✓]`  | [Add semantic display metadata to execution logs](PR-92-execution-log-semantic-display-contract.md) **— Runtime deployed + production smoke verified 2026-04-29** | PR-86..PR-90 | User-facing log contract | 0.5 d | __ |
| PR-93  | `[✓]`  | [Render execution logs as user-facing events by default](PR-93-execution-log-user-facing-app-rendering.md) **— App deployed + tests/smoke verified 2026-04-29** | PR-92 preferred | App log UX | 0.5-1 d | __ |
| PR-94  | `[✓]`  | [Make execution-log expanded view an Agent Monitor, not a debug panel](PR-94-agent-monitor-expanded-view-no-debug.md) **— App deployed + tests/smoke verified 2026-04-29** | PR-92, PR-93 | Agent Monitor UX | 0.5 d | __ |
| PR-95  | `[✓]`  | [Physically remove dead execution-log diagnostics UI code](PR-95-remove-dead-execution-log-diagnostics-code.md) **— App deployed + tests/build verified 2026-04-29** | PR-94 | Agent Monitor cleanup | 0.25-0.5 d | __ |
| PR-96  | `[✓]`  | [Make `chat_reply` output standard Markdown](PR-96-chat-reply-standard-markdown-contract.md) **— Business+Cortex deployed + contract tests verified 2026-04-29** | PR-95 | Chat reply rendering contract | 0.25-0.5 d | __ |
| PR-97  | `[✓]`  | [Unify LLM tool schema source](PR-97-unify-llm-tool-schema-source.md) **— Cortex deployed + schema smoke verified 2026-04-29** | PR-96 | Tool schema SSOT | 0.5 d | __ |
| PR-98  | `[✓]`  | [Execution Log display contract SSOT](PR-98-execution-log-display-contract-ssot.md) **— Runtime+App deployed + production smoke verified 2026-04-29** | PR-97 | Agent Monitor contract | 0.5 d | __ |
| PR-99  | `[✓]`  | [Prompt contract fragments SSOT](PR-99-prompt-contract-fragments-ssot.md) **— shared contract guardrails verified 2026-04-29** | PR-98 | Prompt contract guardrails | 0.5 d | __ |
| PR-100 | `[✓]`  | [Entangled schema and App type guardrails](PR-100-entangled-schema-app-type-guardrails.md) **— App contract guardrails deployed 2026-04-29** | PR-99 | Entity schema guardrails | 0.5 d | __ |
| PR-101 | `[✓]`  | [Config reading contract guardrails](PR-101-config-reading-contract-guardrails.md) **— start.sh strict_config path deployed 2026-04-29** | PR-100 | Config parity | 0.5 d | __ |
| PR-102 | `[✓]`  | [Message lifecycle enum SSOT guardrails](PR-102-message-lifecycle-enum-ssot.md) **— Business+App contract guardrails deployed 2026-04-29** | PR-101 | Message lifecycle contract | 0.5 d | __ |
| PR-103 | `[✓]`  | [Entangled WS schema registered in Rust App cache](PR-103-entangled-ws-schema-rust-cache.md) **— Entangled/App deployed 2026-04-29** | PR-102 | Entangled schema SSOT | 0.5-1 d | __ |
| PR-104 | `[✓]`  | [Gateway AppWS sends only Entangled endpoint](PR-104-gateway-entangled-endpoint-only.md) **— Gateway/App deployed 2026-04-29** | PR-103 | Gateway boundary | 0.5 d | __ |
| PR-105 | `[✓]`  | [Remove TS REST schema bootstrap and old guardrails](PR-105-remove-ts-rest-schema-bootstrap.md) **— Frontend/Desktop deployed 2026-04-29** | PR-103, PR-104 | Old path cleanup | 0.5 d | __ |
| PR-106 | `[✓]`  | [Close Host Desktop device status false-error fix](PR-106-host-desktop-device-status-closure.md) **— App tests/build + frontend/desktop deploy verified 2026-04-30** | PR-105 | App device status | 0.5 d | __ |
| PR-107 | `[✓]`  | [Close VmControl WebRTC mDNS noise fix](PR-107-vmcontrol-webrtc-mdns-closure.md) **— compile + desktop deploy + Host Desktop smoke verified; VM/Android smoke deferred 2026-04-30** | PR-106 | WebRTC policy | 0.5 d | __ |
| PR-108 | `[✓]`  | [Consolidate backend optimization roadmap documents](PR-108-roadmap-optimization-doc-consolidation.md) **— docs merged and old file deleted 2026-04-30** | PR-106, PR-107 | Docs consolidation | 0.25 d | __ |
| PR-109 | `[✓]`  | [Refresh VmControl Cargo.lock deterministically](PR-109-vmcontrol-cargo-lock-determinism.md) **— cargo check --locked + desktop deploy verified 2026-04-30** | PR-107 | Build determinism | 0.25 d | __ |
| PR-110 | `[✓]`  | [Retire Runtime self-drive prompt modules](PR-110-retire-runtime-self-drive-prompt-modules.md) **— Runtime tests/deploy + remote deletion verified 2026-04-30** | PR-99, PR-105 | Old path cleanup | 0.25-0.5 d | __ |
| PR-111 | `[✓]`  | [Business owns system prompt assembly](PR-111-business-owned-system-prompt.md) **— Business+Runtime deployed + remote old-path deletion verified 2026-04-30** | PR-99, PR-110 | Prompt ownership boundary | 0.5-1 d | __ |
| PR-112 | `[✓]`  | [Retire Runtime BusinessClient legacy business-data wrappers](PR-112-retire-runtime-business-client-legacy-wrappers.md) **— Runtime tests/deploy + remote old-wrapper deletion verified 2026-04-30** | PR-111 | Runtime boundary cleanup | 0.25-0.5 d | __ |
| PR-113 | `[✓]`  | [Retire Wake IM Replay context path](PR-113-retire-wake-im-replay-context-path.md) **— Runtime deployed + remote old-path deletion verified 2026-04-30** | PR-67, PR-68, PR-69, PR-70 | Runtime context cleanup | 0.25-0.5 d | __ |
| PR-114 | `[✓]`  | [Remove Runtime `session.check_new_messages` dead handler](PR-114-remove-runtime-check-new-messages-handler.md) **— Runtime deployed + remote old-handler deletion verified 2026-04-30** | PR-46, P6-12, PR-113 | Runtime cleanup | 0.25 d | __ |
| PR-115 | `[✓]`  | [Remove Business `messages/unread*` zombie routes](PR-115-remove-business-unread-zombie-routes.md) | P6-12, PR-114 | Business cleanup | 0.25-0.5 d | Implemented, tested, deployed |
| PR-116 | `[✓]`  | [Remove `chat_messages.read` UI compatibility branch](PR-116-remove-chat-messages-read-compat.md) | P6-12, PR-114, PR-115 | Message lifecycle cleanup | 0.5-1 d | Implemented, tested, deployed |
| PR-117 | `[✓]`  | [Remove Business TaskManager legacy proxy](PR-117-remove-business-taskmanager-legacy-proxy.md) | PR-112 | Business cleanup | 0.25-0.5 d | Implemented, tested, deployed |
| PR-118 | `[✓]`  | [Remove deprecated Business `subagent_context` path](PR-118-remove-deprecated-subagent-context-path.md) | PR-67, PR-70, PR-113 | Business/Cortex boundary cleanup | 0.5-1 d | Implemented, tested, deployed |
| PR-119 | `[✓]`  | [Active Code Zombie Path Audit and First Cleanup Batch](PR-119-active-code-zombie-path-audit.md) | PR-114..PR-118 | Old path cleanup | 0.5-1 d | Implemented, tested, deployed |
| PR-120 | `[✓]`  | [Remove Device Service Retired Entangled CLI](PR-120-remove-device-entangled-cli.md) | PR-119 | Device cleanup | 0.25-0.5 d | Implemented, tested, deployed |
| PR-121 | `[✓]`  | [Gateway Entangled Sync Endpoint Discovery Boundary](PR-121-gateway-entangled-sync-discovery-boundary.md) **— Gateway deployed + remote old-path deletion verified 2026-04-30** | PR-104, PR-119 | Gateway boundary cleanup | 0.25-0.5 d | Implemented, tested, deployed |
| PR-122 | `[✓]`  | [Entangled Public WebSocket URL SSOT](PR-122-entangled-public-ws-url-ssot.md) **— Gateway deployed + public WS endpoint verified 2026-04-30** | PR-121 | Gateway boundary cleanup | 0.25 d | Implemented, tested, deployed |
| PR-123 | `[deployed]`  | [SubAgent IM target routing](PR-123-subagent-im-target-routing.md) | PR-122 | SubAgent IM correctness | 0.25-0.5 d | Verified closed 2026-05-01 |
| PR-124 | `[deployed]`  | [Spawn delivers initial task via `SUBAGENT_SEND`](PR-124-subagent-spawn-initial-task-im.md) | PR-123 | SubAgent IM unification | 0.5 d | Verified closed 2026-05-01 |
| PR-125 | `[deployed]`  | [Child subagent reports through parent IM](PR-125-subagent-parent-im-prompt.md) | PR-124 preferred | Prompt contract | 0.25-0.5 d | Verified closed 2026-05-01 |
| PR-126 | `[deployed]`  | [Remove `subagent_report` LLM tool path](PR-126-remove-subagent-report-tool.md) | PR-125 | Old path cleanup | 0.5 d | Verified closed 2026-05-01 |
| PR-127 | `[deployed]`  | [Remove `subagent_query` and `subagent_cancel` LLM tools](PR-127-remove-subagent-query-cancel-tools.md) | PR-126 preferred | Tool contract cleanup | 0.5 d | Verified closed 2026-05-01 |
| PR-128 | `[deployed]`  | [Remove `subagent_completed` notify-parent path](PR-128-remove-subagent-completed-notify-path.md) | PR-126 preferred | Lifecycle cleanup | 0.25-0.5 d | Verified closed 2026-05-01 |
| PR-129 | `[deployed]`  | [Remove `SPAWN_SUBAGENT` and `SUBAGENT_COMPLETED` message residues](PR-129-remove-spawn-completed-message-types.md) | PR-124, PR-128 | Message lifecycle cleanup | 0.5 d | Verified closed 2026-05-01 |
| PR-130 | `[deployed]`  | [Promote `display` to a real LLM + Runtime tool](PR-130-display-runtime-llm-tool.md) | PR-97 | Tool contract correctness | 0.5 d | Verified closed 2026-05-01 |
| PR-131 | `[deployed]`  | [Promote `chat_history` to a real LLM + Runtime tool](PR-131-chat-history-runtime-llm-tool.md) | PR-97 | Tool contract correctness | 0.5 d | Verified closed 2026-05-01 |
| PR-132 | `[deployed]`  | [Quarantine `audio_qa` until Runtime executor exists](PR-132-audio-qa-tool-quarantine.md) | PR-130 | Tool exposure cleanup | 0.25 d | Closed by quarantine then PR-136/PR-137 restore |
| PR-133 | `[deployed]`  | [Remove common `notebook_*` and `task_*` tool residues](PR-133-remove-common-notebook-task-tools.md) | PR-132 | Old path cleanup | 0.25-0.5 d | Verified closed 2026-05-01 |
| PR-134 | `[deployed]`  | [Keep Cortex step result projection as the sole result path](PR-134-cortex-step-result-projection-sole-path.md) | PR-86..PR-98, PR-130..PR-133 | Result-path cleanup | 0.5-1 d | Implemented, tested, deployed 2026-05-01 |
| PR-135 | `[deployed]`  | [Delete obsolete packaged result artifacts](PR-135-delete-obsolete-packaged-result-artifacts.md) | PR-134 | Physical artifact cleanup | 0.25 d | Implemented, tested, deployed 2026-05-01 |
| PR-136 | `[deployed]`  | [Port `audio_qa` to the Runtime native executor](PR-136-audio-qa-runtime-executor.md) | PR-132 | Tool execution restore | 0.5 d | Implemented, tested, deployed 2026-05-01 |
| PR-137 | `[deployed]`  | [Expose `audio_qa` from the common LLM tool schema](PR-137-audio-qa-common-schema.md) | PR-136 | Tool schema restore | 0.25-0.5 d | Implemented, tested, deployed 2026-05-01 |
| PR-138 | `[deployed]`  | [Route audio attachments toward `audio_qa`](PR-138-audio-attachment-routing.md) | PR-136, PR-137 | Attachment UX | 0.25 d | Implemented, tested, deployed 2026-05-01 |
| PR-139 | `[closed]` | [Branch and Submodule Mainline Residue Scan](PR-139-branch-submodule-mainline-residue-scan.md) | PR-138 | Mainline clarity | 0.25 d | No first-party branch drift found |
| PR-140 | `[deployed]` | [Retired Service and Packaged Artifact Residue Scan](PR-140-retired-service-artifact-residue-scan.md) | PR-139 | Old service cleanup | 0.25 d | Retired service residue removed from active paths; CI guard added |
| PR-141 | `[deployed]` | [Fallback / Compatibility / Deprecated Branch Residue Scan](PR-141-fallback-compat-deprecated-residue-scan.md) | PR-140 | Branch entropy cleanup | 0.5 d | Delete-now compatibility paths removed; tests added |
| PR-142 | `[deployed]` | [Tool Schema / Executor Source Residue Scan](PR-142-tool-schema-executor-source-residue-scan.md) | PR-141 | Tool ownership clarity | 0.25-0.5 d | App phantom tool placeholders cleaned; CI guard added |
| PR-143 | `[deployed]` | [Agent Loop / Subscriber / Scheduler Residue Scan](PR-143-agent-loop-subscriber-scheduler-residue-scan.md) | PR-142 | Agent loop clarity | 0.5 d | Subscriber required path; canary switch removed |
| PR-144 | `[deployed]` | [Prompt / Memory / Summary Residue Scan](PR-144-prompt-memory-summary-residue-scan.md) | PR-143 | Cortex minimality | 0.25-0.5 d | Prompt product-context boundary cleaned; tests added |
| PR-145 | `[deployed]` | [Entangled Schema and Config SSOT Residue Scan](PR-145-entangled-schema-config-ssot-residue-scan.md) | PR-144 | Entangled/config SSOT | 0.25-0.5 d | Generated entity-id pipeline deleted; SSOT guard added |
| PR-146 | `[deployed]` | [Documentation and Runbook Archaeology Residue Scan](PR-146-documentation-runbook-archaeology-residue-scan.md) | PR-145 | Docs cleanup | 0.5 d | Current docs rewritten; residue lint added |
| PR-147 | `[deployed]` | [Remove Cortex Disabled / No-op Runtime Path](PR-147-remove-cortex-disabled-noop-path.md) | PR-146 | Cortex required invariant | 0.5-1 d | Runtime/common tests passed; deployed via `./deploy runtime` |
| PR-148 | `[deployed]` | [Remove LLM Factory Model Fallback / Failover Branch](PR-148-remove-llm-factory-model-fallback.md) | PR-147 | LLM determinism | 0.25-0.5 d | Factory tests passed; deployed; smoke log `a10a8ef1-a543-4eb3-b477-20a2d68f39f9` |
| PR-149 | `[deployed]` | [Retire Business Notebook / Quadrant Task / Drive Profile Surfaces](PR-149-retire-business-notebook-task-drive-surfaces.md) | PR-148 | Product-surface cleanup | 0.5-1.5 d | 2026-05-01 |
| PR-150 | `[deployed]` | [Remove App Deprecated Compatibility Shells](PR-150-remove-app-deprecated-compat-shells.md) | PR-149 | App path cleanup | 0.5-1 d | 2026-05-01 |
| PR-151 | `[deployed]` | [Remove Device Binding Legacy Compatibility](PR-151-remove-device-binding-legacy-compat.md) | PR-150 | Device contract cleanup | 0.5-1 d | 2026-05-01 |
| PR-152 | `[deployed]` | [Gateway / Business / Entangled Boundary Review](PR-152-gateway-business-entangled-boundary-review.md) | PR-151 | Boundary cleanup | multi-step | Closed: Gateway kept to edge boundary, Business file metadata explicit, stale AppBridge request permission removed |
| PR-153 | `[deployed]` | [Queue / Session / Subscriber Lifecycle Review](PR-153-queue-session-subscriber-lifecycle-review.md) | PR-152 | Agent loop lifecycle cleanup | multi-step | Closed: subscriber/session lifecycle ownership guarded and deployed |
| PR-154 | `[deployed]` | [Agent Monitor User-Facing Review](PR-154-agent-monitor-user-facing-review.md) | PR-153 | Agent Monitor product surface | multi-step | Closed: normal monitor no longer exposes raw diagnostic payload path |
| PR-155 | `[deployed]` | [Runtime Tool Executor Coverage Review](PR-155-runtime-tool-executor-coverage-review.md) | PR-154 | Tool contract cleanup | multi-step | Closed: Common schema, Runtime executors, and monitor display kinds aligned |
| PR-156 | `[deployed]` | [Deploy / Config Overlay Residue Review](PR-156-deploy-config-overlay-residue-review.md) | PR-155 | Deploy/config cleanup | multi-step | Closed: old deploy/config switches removed and guarded |
| PR-157 | `[done]` | [App Gateway `/api/vm/*` Residue Review](PR-157-app-gateway-vm-http-residue-review.md) | PR-152 | App/Gateway boundary cleanup | multi-step | Big ticket: analyze, create small tickets, implement to closure |
| PR-157A | `[done]` | [Device Entangled VM Prep Actions](PR-157A-device-entangled-vm-prep-actions.md) | PR-157 | Device action cleanup | 0.25-0.5 d | Small ticket |
| PR-157B | `[done]` | [Remove App Gateway VM Service](PR-157B-remove-app-gateway-vm-service.md) | PR-157A | App old-path cleanup | 0.25-0.5 d | Small ticket |
| PR-157C | `[done]` | [Remove Agent-Scoped VM Status UI Residue](PR-157C-remove-agent-scoped-vm-status-ui-residue.md) | PR-157B | App old-path cleanup | 0.25-0.5 d | Small ticket |
| PR-157D | `[done]` | [Guard App Gateway VM HTTP Residue](PR-157D-guard-app-gateway-vm-http-residue.md) | PR-157B, PR-157C | Boundary guardrail | 0.25 d | Small ticket |
| PR-158 | `[deployed]` | [Runtime Tool Product Semantics Matrix](PR-158-runtime-tool-product-semantics-matrix.md) | PR-155, PR-157 | Tool product semantics | multi-step | Closed: product semantics matrix guards Common, Runtime, and App monitor |
| PR-159 | `[deployed]` | [Business Product Context Boundary Review](PR-159-business-product-context-boundary-review.md) | PR-158 | Business/Cortex context boundary | multi-step | Closed via PR-159A: product-context wording, Runtime client, and Cortex boundary guardrails deployed |
| PR-160 | `[done]` | [Online Entangled Data Shape Audit](PR-160-online-entangled-data-shape-audit.md) | PR-159 | Data shape cleanup | multi-step | Closed: online shape audit, cleanup, and guardrails completed |
| PR-161 | `[done]` | [No-Value Script and Runbook Cleanup](PR-161-no-value-script-runbook-cleanup.md) | PR-160 | Script/runbook cleanup | multi-step | Closed: no-value scripts/runbooks deleted and guarded |
| PR-162 | `[deployed]` | [Environment Domain and Storage Foundation](PR-162-environment-domain-storage-foundation.md) | PR-161 | Agent subject / environment foundation | multi-step | Closed: Common contract + Business repository/service deployed |
| PR-162A | `[deployed]` | [Environment Contract and Invariant Test Matrix](PR-162A-environment-contract-invariants.md) | PR-162 | Environment contract | 0.25 d | Common contract deployed; 108 common tests passed |
| PR-162B | `[deployed]` | [Environment Persistence Repository and Migrations](PR-162B-environment-persistence-repository.md) | PR-162A | Environment storage | 0.5-1 d | Business repository boundary deployed; hot path unchanged |
| PR-162C | `[deployed]` | [Environment Domain Service and Lifecycle State Machine](PR-162C-environment-domain-service.md) | PR-162B | Environment service | 0.5-1 d | Business service boundary deployed |
| PR-163 | `[deployed]` | [Runtime Environment Tool Integration](PR-163-runtime-environment-tool-integration.md) | PR-162 | LLM observation/action tools | multi-step | Environment IM tool integration completed and deployed |
| PR-163A | `[deployed]` | [Environment Tool Schema Candidates](PR-163A-environment-tool-schema-candidates.md) | PR-163 | Environment tool schema | 0.25 d | Candidate schemas deployed; active tools unchanged |
| PR-163B | `[deployed]` | [Runtime Executors for Environment IM Tools](PR-163B-runtime-environment-im-executors.md) | PR-163A | Environment tool executors | 0.5-1 d | Business internal API + Runtime candidate executors deployed; active tools unchanged |
| PR-163C | `[deployed]` | [Environment Tool Exposure and Old Communication Tool Cleanup](PR-163C-environment-tool-cutover-cleanup.md) | PR-163B | Tool cutover cleanup | 0.5-1 d | Environment IM exposed; old direct communication tools removed |
| PR-163C1 | `[deployed]` | [Activate Environment IM Tool Contracts](PR-163C1-activate-environment-im-tool-contracts.md) | PR-163B | Tool contract cutover | 0.25-0.5 d | Environment IM tools active in schema/executor/monitor contracts |
| PR-163C2 | `[deployed]` | [Cut Prompt and Turn Semantics to Environment IM](PR-163C2-cut-prompt-turn-semantics-to-environment-im.md) | PR-163C1 | Prompt/runtime cutover | 0.5 d | Prompt/no-tool warning/turn closer now use Environment IM |
| PR-163C3 | `[deployed]` | [Delete Superseded Direct Communication Tools](PR-163C3-delete-superseded-communication-tools.md) | PR-163C2 | Old path cleanup | 0.5-1 d | Old direct communication tool paths removed, deployed, and production-smoke verified |
| PR-164 | `[deployed]` | [Cortex Observation and Payload Integration](PR-164-cortex-observation-payload-integration.md) | PR-163 | Work trajectory / perception record | multi-step | PR-164A/PR-164B/PR-164C deployed |
| PR-164A | `[deployed]` | [Tool Result Observation Payload Write Path](PR-164A-tool-result-observation-payload-write-path.md) | PR-164 | Cortex payload ref | 0.5-1 d | Runtime tool results now write observation + payload_ref; Cortex rejects inline raw result |
| PR-164B | `[deployed]` | [Explicit Payload Inspection Tools](PR-164B-explicit-payload-inspection-tools.md) | PR-164A | Explicit observation tools | 0.5-1 d | `payload_read` and `payload_search` deployed; no hidden auto-summary path |
| PR-164C | `[deployed]` | [Reasoning and Action Trace Projection](PR-164C-reasoning-action-trace-projection.md) | PR-164A, PR-164B | Activity trace projection | 0.5-1 d | Cortex trace projection API deployed; App payload monitor display aligned |
| PR-165 | `[deployed]` | [Notification Wake and Prompt Cutover](PR-165-notification-wake-prompt-cutover.md) | PR-164 | Agent loop / prompt boundary | multi-step | PR-165A/PR-165B/PR-165C deployed; prompt receives Environment notifications, not hidden raw message bodies |
| PR-165A | `[deployed]` | [Environment Notification Prompt Source](PR-165A-environment-notification-prompt-source.md) | PR-165 | Prompt boundary / Environment observation | 0.5-1 d | Runtime prompt context now uses notification hints; `im_read({})` resolves wake ids |
| PR-165B | `[deployed]` | [Prompt and Tool Wording Notification-Only Cutover](PR-165B-prompt-tool-wording-notification-only.md) | PR-165A | Prompt contract | 0.25-0.5 d | Business/Common prompt wording aligned with notification -> `im_read` observation path |
| PR-165C | `[deployed]` | [Notification Lifecycle Close / Failure Semantics](PR-165C-notification-lifecycle-close-failure.md) | PR-165B | Lifecycle ownership | 0.5 d | Runtime lifecycle guardrails added; old UI receipt/filter switch removed |
| PR-166 | `[deployed]` | [Activity Timeline Projection and Old Path Cleanup](PR-166-activity-timeline-old-path-cleanup.md) | PR-165 | User-facing monitor / entropy cleanup | multi-step | Closed: Cortex projection, App phase rendering, and backend diagnostic payload retirement deployed |
| PR-166A | `[deployed]` | [Activity Timeline Projection Contract](PR-166A-activity-timeline-projection-contract.md) | PR-166 | Agent monitor projection | 0.5 d | Cortex trace projection now returns user-facing timeline records without debug ids/refs |
| PR-166B | `[deployed]` | [App Monitor Activity Phase Rendering](PR-166B-app-monitor-activity-phase-rendering.md) | PR-166A, PR-166C | Agent monitor UX | 0.25-0.5 d | App execution-log monitor now labels events as observation/reasoning/action/summary |
| PR-166C | `[deployed]` | [Remove Backend `log-payloads` Diagnostic Payload Path](PR-166C-remove-backend-log-payloads-diagnostic-path.md) | PR-166, PR-154A | Old path cleanup | 0.5 d | Backend raw payload entity/action/write path removed; services deployed |
| PR-167 | `[done]` | [Environment Dedicated Domain Store](PR-167-environment-dedicated-domain-store.md) | PR-166 | Environment domain completion | multi-step | Dedicated store/service/backfill closed; queue cutover remains PR-168 |
| PR-167A | `[done]` | [Dedicated Environment Entity Schema and Contract Guardrails](PR-167A-environment-entity-schema-contracts.md) | PR-167 | Environment schema | 0.5 d | Dedicated Environment entities registered, tested, deployed |
| PR-167B | `[done]` | [Dedicated Environment Repository Read/Write Path](PR-167B-environment-dedicated-repository.md) | PR-167A | Environment repository | 0.5-1 d | Repository moved to dedicated Environment entities; messages remain projection only |
| PR-167C | `[done]` | [Environment Generic Event API and Lifecycle State Machine](PR-167C-environment-domain-service-state-machine.md) | PR-167B | Environment service | 0.5 d | Generic event + notification APIs added and tested |
| PR-167D | `[done]` | [Environment Backfill and Message-Backed Repository Removal](PR-167D-environment-backfill-remove-message-backed-repo.md) | PR-167C | Data backfill / guard | 0.25-0.5 d | Production backfilled; repository no-message-read guard added |
| PR-168 | `[done]` | [Environment Notification Queue Cutover](PR-168-environment-notification-queue-cutover.md) | PR-167 | Agent loop ownership | multi-step | Environment notification owns wake trigger/lifecycle; old message outbox/lifecycle path physically removed |
| PR-168A | `[done]` | [Environment Notification Internal API](PR-168A-environment-notification-internal-api.md) | PR-167 | Business boundary | 0.25-0.5 d | Internal list/claim/processed/failed APIs added |
| PR-168B | `[done]` | [Environment Notification Dispatch Lease](PR-168B-environment-notification-dispatch-lease.md) | PR-168A | Queue ownership boundary | 0.25-0.5 d | Dispatch lease added before subscriber cutover |
| PR-168C | `[done]` | [Environment Notification Subscriber Cutover](PR-168C-environment-notification-subscriber-cutover.md) | PR-168B | Subscriber trigger source | 0.5 d | Subscriber now dispatch-claims Environment notifications; old outbox polling removed from hot loop |
| PR-168D | `[done]` | [Runtime Environment Notification Finalization](PR-168D-runtime-environment-notification-finalization.md) | PR-168C | Runtime lifecycle ownership | 0.5 d | Runtime tests/deploy + production smoke verified; hot path transitions Environment notifications claimed/processed |
| PR-168E | `[done]` | [Remove Message-Lifecycle / Outbox Notification Compatibility](PR-168E-remove-message-lifecycle-outbox-compat.md) | PR-168D | Old path cleanup | 0.5-1 d | Runtime/Business/Common/Entangled old path removed, deployed, and prod old tables dropped |
| PR-169 | `[closed]` | [App Cortex Activity Timeline Cutover](PR-169-app-cortex-activity-timeline-cutover.md) | PR-166, PR-168 preferred | Agent Monitor source of truth | multi-step | Superseded by PR-193; old action/Cortex HTTP projection path removed |
| PR-170 | `[closed]` | [Payload Interpretation Tools](PR-170-payload-interpretation-tools.md) | PR-164 | Explicit observation interpretation | multi-step | `payload_read/search/summarize/qa` are explicit tools |
| PR-171 | `[closed]` | [Final Old Path Physical Deletion and Guardrails](PR-171-final-old-path-physical-deletion.md) | PR-167..PR-170 | Entropy cleanup | multi-step | Old monitor/tool/summary paths deleted and guarded |
| PR-172 | `[closed]` | [Roadmap Status Index Reconciliation](PR-172-roadmap-status-index-reconciliation.md) | PR-169..PR-171 | Documentation entropy cleanup | 0.25 d | Index reconciled |
| PR-173 | `[closed]` | [Environment IM History Observation Tools](PR-173-environment-im-history-observation-tools.md) | PR-167, PR-168 | Explicit Environment observation | 0.5-1 d | `im_history/search/context` implemented without reviving `chat_history` |
| PR-174 | `[closed]` | [Remove Execution Logs Diagnostic Entity Tail](PR-174-remove-execution-logs-diagnostic-entity-tail.md) | PR-169, PR-171 | Old diagnostic path deletion | 0.5-1 d | Remaining `execution-logs` tail physically removed and guarded |
| PR-175 | `[closed]` | [Agent Perception Document Decision Cleanup](PR-175-agent-perception-doc-decision-cleanup.md) | PR-169..PR-173 | Architecture documentation correctness | 0.25 d | Stale undecided wording replaced with current decisions |
| PR-176 | `[closed]` | [Step Ref / Payload Ref Naming Cleanup](PR-176-step-ref-payload-ref-naming-cleanup.md) | PR-171 | Naming entropy cleanup | 0.5-1 d | Active `result_id` join-key wording replaced by `step_ref` |
| PR-177 | `[closed]` | [Canonical SubAgent Spawn Endpoint](PR-177-canonical-subagent-spawn-endpoint.md) | PR-124, PR-168 | Business endpoint entropy cleanup | 0.25 d | Duplicate agent-scoped Business endpoint removed; PR-178 removes Cortex proxy mutation |
| PR-178 | `[closed]` | [Remove Cortex SubAgent Spawn Proxy Mutation](PR-178-remove-cortex-subagent-spawn-proxy.md) | PR-177 | Cortex/Runtime/Business boundary cleanup | 0.25 d | Direct Cortex proxy spawn write path removed; Runtime tool remains canonical Agent action executor |
| PR-179 | `[closed]` | [Cortex legacy CLI/proxy surface cleanup](PR-179-cortex-legacy-cli-proxy-surface-cleanup.md) | PR-178 | Cortex boundary cleanup | 0.5 d | BusinessProxy route, CLI commands, startup wiring, and active docs removed; Cortex deployed |
| PR-180 | `[closed]` | [Business device proxy route boundary review](PR-180-business-device-proxy-route-boundary-review.md) | PR-179 | Business/Device boundary cleanup | 0.5-1 d | Review closed by PR-180A |
| PR-180A | `[closed]` | [Delete Business device proxy routes with no active caller](PR-180A-delete-business-device-proxy-routes.md) | PR-180 | Business/Device boundary cleanup | 0.25-0.5 d | Removed Business qemu/vm/mobile/hd forwarding routes and proxy helper; Business deployed |
| PR-181 | `[closed]` | [SubAgent spawn write normalization](PR-181-subagent-spawn-write-normalization.md) | PR-177, PR-178 | Environment/SubAgent single-writer cleanup | 0.5 d | Review closed by PR-181A |
| PR-181A | `[closed]` | [SubAgent spawn uses Environment as the single IM writer](PR-181A-subagent-spawn-environment-single-writer.md) | PR-181 | Environment/SubAgent single-writer cleanup | 0.25-0.5 d | Removed direct `messages` append from spawn; Environment writes projection; Business deployed |
| PR-182 | `[closed]` | [Back-compat naming and branch cleanup](PR-182-backcompat-naming-branch-cleanup.md) | PR-179..PR-181 | Maintenance entropy cleanup | 0.5-1 d | Closed by PR-182A and PR-182B |
| PR-182A | `[closed]` | [Delete legacy Business health stubs](PR-182A-delete-legacy-business-health-stubs.md) | PR-182 | Business/Common config cleanup | 0.25 d | Removed retired app-ws/stuck-sending stubs and config; Business deployed |
| PR-182B | `[closed]` | [Remove unused Cortex compatibility helpers](PR-182B-remove-cortex-compat-helpers.md) | PR-182 | Cortex naming cleanup | 0.25 d | Removed unused helpers and compatibility wording; Cortex deployed |
| PR-183 | `[closed]` | [Gateway Auth / File Proxy boundary cleanup](PR-183-gateway-auth-file-proxy-boundary-cleanup.md) | PR-182 | Gateway boundary cleanup | 0.5 d | Closed by PR-183A and PR-183B; Gateway deployed |
| PR-183A | `[closed]` | [Gateway auth token transport tightening](PR-183A-gateway-auth-token-transport-tightening.md) | PR-183 | Gateway auth boundary | 0.25 d | Removed direct validate query token fallback |
| PR-183B | `[closed]` | [Gateway file proxy file-id boundary](PR-183B-gateway-file-proxy-file-id-boundary.md) | PR-183 | Gateway file boundary | 0.25 d | Removed direct raw-path GET proxy |
| PR-184 | `[closed]` | [Runtime Queue Client compatibility cleanup](PR-184-runtime-queue-client-compat-cleanup.md) | PR-182 | Runtime queue API cleanup | 0.25 d | Closed by PR-184A; Runtime deployed |
| PR-184A | `[closed]` | [Remove SagaClient.get_saga alias](PR-184A-remove-sagaclient-get-saga-alias.md) | PR-184 | Runtime queue API cleanup | 0.25 d | Removed old SagaClient alias |
| PR-185 | `[closed]` | [App Device / VM historical naming cleanup](PR-185-app-device-vm-historical-naming-cleanup.md) | PR-182 | App device naming cleanup | 0.5 d | Closed by PR-185A and PR-185B |
| PR-185A | `[closed]` | [Rename Device VNC target hook](PR-185A-rename-device-vnc-target-hook.md) | PR-185 | App device naming cleanup | 0.25 d | Renamed stale VNC hook |
| PR-185B | `[closed]` | [Remove useDevices legacy sync helpers](PR-185B-remove-use-devices-legacy-sync-helpers.md) | PR-185 | App device hook cleanup | 0.25 d | Removed unused sync helper aliases |
| PR-186 | `[closed]` | [Agent Main Path End-to-End Invariants](PR-186-agent-main-path-end-to-end-invariants.md) | PR-162..PR-171 | Agent main path acceptance | multi-step | Runtime/Business/Cortex/App acceptance tests and cross-repo guard closed |
| PR-186A | `[closed]` | [Runtime Wake Observation / Reply Lifecycle Acceptance](PR-186A-runtime-wake-observation-reply-lifecycle.md) | PR-186 | Runtime acceptance | 0.25-0.5 d | Added Runtime main-path acceptance |
| PR-186B | `[closed]` | [Business Environment Notification Hot-Path Acceptance](PR-186B-business-environment-notification-hot-path.md) | PR-186A | Environment acceptance | 0.25-0.5 d | Added Business Environment hot-path acceptance |
| PR-186C | `[closed]` | [Cortex Trace and Payload Invariant Acceptance](PR-186C-cortex-trace-payload-invariants.md) | PR-186B | Cortex acceptance | 0.25-0.5 d | Added Cortex trace/payload acceptance |
| PR-186D | `[closed]` | [App Agent Monitor Public-Surface Acceptance](PR-186D-app-agent-monitor-public-surface.md) | PR-186C | App monitor acceptance | 0.25-0.5 d | Added Activity Timeline acceptance |
| PR-186E | `[closed]` | [Cross-Repo Old-Path Residue Guard and Closure](PR-186E-cross-repo-old-path-residue-guard.md) | PR-186D | Entropy guard | 0.25 d | Added cross-repo main-path guard |
| PR-187 | `[closed]` | [Main Path Guard CI Enforcement and Stale Ticket Archival](PR-187-main-path-guard-ci-and-stale-ticket-archival.md) | PR-186 | CI/docs entropy guard | multi-step | Main-path guards wired into CI/root tests; stale PR-90/91 checklist residue archived |
| PR-187A | `[closed]` | [Wire Main-Path Guards Into CI and Root Test Entrypoint](PR-187A-wire-main-path-guards-into-ci.md) | PR-187 | CI guardrail | 0.25 d | Added guard bundle to GitHub lint and run_all_tests; removed missing old lint step |
| PR-187B | `[closed]` | [Archive Stale Ticket Checklist Residue](PR-187B-archive-stale-ticket-checklist-residue.md) | PR-187A | Docs entropy cleanup | 0.25 d | PR-90/91 no longer expose stale unchecked subtasks |
| PR-188 | `[closed]` | [Agent Monitor Main Scope Resolution](PR-188-agent-monitor-main-scope-resolution.md) | PR-169, PR-186 | Agent Monitor correctness | multi-step | Superseded by PR-193 Entangled projection; historical action path removed |
| PR-188A | `[closed]` | [Business Activity Timeline Main Subagent Resolution](PR-188A-business-activity-timeline-main-subagent-resolution.md) | PR-188 | Business/Monitor boundary | 0.25 d | Missing subagent_id resolves to real main subagent id |
| PR-188B | `[closed]` | [Agent Monitor Default Scope Guard](PR-188B-agent-monitor-default-scope-guard.md) | PR-188A | Regression guard | 0.25 d | Default monitor path guarded against literal `main` scope drift |
| PR-189 | `[closed]` | [Entangled Schema Registration Broadcast](PR-189-entangled-schema-registration-broadcast.md) | PR-145 | App startup / Entangled schema readiness | 0.25 d | Schema registration now broadcasts updated schema to already-connected WS clients |
| PR-193 | `[closed]` | [Agent Monitor Entangled Projection Cutover](PR-193-agent-monitor-entangled-projection-cutover.md) | PR-169, PR-188, PR-191 | Agent Monitor product projection | multi-step | Entangled projection entities replaced polling action/Cortex HTTP read path |
| PR-193A | `[closed]` | [Agent Activity Entangled Entity Contracts](PR-193A-agent-activity-entangled-entity-contracts.md) | PR-193 | Entity contract | 0.25-0.5 d | App-facing activity records/participants contracts and route subscriptions added |
| PR-193B | `[closed]` | [Runtime Agent Activity Projection Write Path](PR-193B-runtime-agent-activity-projection-write-path.md) | PR-193A | Runtime materialization | 0.5-1 d | Runtime materializes public monitor rows on trace write path |
| PR-193C | `[closed]` | [App Agent Monitor Entangled Read Path](PR-193C-app-agent-monitor-entangled-read-path.md) | PR-193B | App read path | 0.5 d | Monitor reads Entangled cache, not action polling |
| PR-193D | `[closed]` | [Delete Activity Timeline Action Hot Path](PR-193D-delete-activity-timeline-action-hot-path.md) | PR-193C | Old path deletion | 0.25 d | Removed agents.activity_timeline action and Cortex trace/project endpoint |
| PR-193E | `[closed]` | [Agent Monitor Projection Guardrails and Docs](PR-193E-agent-monitor-projection-guardrails-and-docs.md) | PR-193D | Guardrails/docs | 0.25 d | Docs and static guards aligned to one Entangled projection path |
| PR-195 | `[closed]` | [Remove frontend noVNC client residue](PR-195-remove-frontend-novnc-client.md) | PR-185A | App cleanup | 0.25 d | Browser noVNC assets/dependency/alias removed; Rust VNC/RFB backend preserved |
| PR-207 | `[closed]` | [Cortex Blob-backed Store Cutover](PR-207-cortex-blob-store-cutover.md) | PR-206 | Storage boundary cleanup | multi-step | Cortex direct S3/OSS store removed; Blob Service owns object storage |
| PR-208 | `[closed]` | [Current Documentation Drift Cleanup](PR-208-current-doc-drift-cleanup.md) | PR-207 | Docs entropy cleanup | 0.25 d | Current docs no longer present old Gateway/outbox paths as active |
| PR-209 | `[closed]` | [Agent Monitor Final Product Shape](PR-209-agent-monitor-final-product-shape.md) | PR-193, PR-186D, PR-208 | Agent Monitor product contract | 0.25 d | Bottom capsule, activity layer, taxonomy, detail, and acceptance matrix defined |
| PR-210 | `[closed]` | [Maintenance Tail Cleanup](PR-210-maintenance-tail-cleanup.md) | PR-209 | Maintenance entropy cleanup | 0.25-0.5 d | Active `_sync` worker naming tails removed; stale roadmap archaeology fenced and guarded |
| PR-211 | `[closed]` | [Blob Large File / Multipart / Audio Compression Review](PR-211-blob-large-file-multipart-audio-review.md) | PR-207 | Blob boundary / roadmap cleanup | 0.25 d | Historical Blob upload state recorded; PR-212..PR-216 closed the multipart/audio/base64-removal follow-up chain |
| PR-212 | `[closed]` | [Blob Multipart Contract and Backend Support](PR-212-blob-multipart-contract-backend.md) | PR-211 | Blob large-file upload | 0.5 d | Multipart session API, raw part upload, complete/abort/list/expire, and tests |
| PR-213 | `[closed]` | [App Large Upload Cutover](PR-213-app-large-upload-cutover.md) | PR-212 | App upload data-plane cleanup | 0.5 d | App large attachments use multipart direct Blob upload and Gateway control-plane registration |
| PR-214 | `[closed]` | [Audio Compression Path](PR-214-audio-compression-path.md) | PR-211, PR-212 | Audio upload efficiency | 0.5 d | Voice recording now produces compressed AAC/M4A bytes and uploads audio through multipart `audio-input` blobs |
| PR-215 | `[closed]` | [Blob Payload Limits and Observability](PR-215-blob-payload-limits-observability.md) | PR-211 | Blob failure semantics / observability | 0.25 d | Blob Service now has explicit payload limits, 413 errors, and raw-payload-safe lifecycle logs |
| PR-216 | `[closed]` | [Remove Base64 Blob Upload Path](PR-216-remove-base64-blob-upload.md) | PR-212, PR-213, PR-214, PR-215 | Blob upload old-path deletion | 0.5 d | App/Gateway/Blob Service base64 upload path removed; all chat attachments upload via multipart raw bytes |
| PR-217 | `[closed]` | [Direct Blob Download Edge](PR-217-direct-blob-download-edge.md) | PR-216 | Blob download data-plane cleanup | 0.25 d | App attachment downloads use `/blob/` edge; Gateway app Blob fetch/download/presign data-plane routes removed |
| PR-218 | `[closed]` | [Retired Tail Residue Cleanup](PR-218-retired-tail-residue-cleanup.md) | PR-216, PR-217 | Old-path residue cleanup | 0.5 d | Removed retained storage artifact, Blob edge doc wording, retired result-store naming fixtures, and Android JSON-base64 file/app endpoints |
| PR-219 | `[closed]` | [Runtime Queue / Saga Residue Cleanup](PR-219-runtime-queue-saga-residue-cleanup.md) | PR-141 | Runtime queue/saga cleanup | 0.5 d | Removed saga start surface, current-step live state, queue/saga compatibility helpers, and instance-management exports |
| PR-220 | `[closed]` | [Cortex Payload / Base64 Residue Review](PR-220-cortex-payload-base64-residue-review.md) | PR-207, PR-218 | Cortex payload boundary | 0.5 d | Cortex payload writes now use Blob multipart uploads; direct JSON/base64 blob write path guarded out |
| PR-221 | `[closed]` | [Legacy / Compatibility Documentation And Script Drift Cleanup](PR-221-doc-script-drift-cleanup.md) | PR-218 | Docs/scripts drift cleanup | 0.25 d | Retired relay migration script deleted and active Gateway/VMControl/WebRTC/Blob docs aligned to current paths |
| PR-222 | `[closed]` | [Compatibility Alias / Fallback Test Naming Cleanup](PR-222-compat-alias-fallback-test-name-cleanup.md) | PR-141 | Alias/fallback naming cleanup | 0.25 d | Device config aliases removed; Business owner/device lookup fallback paths removed; guard tests renamed to current vocabulary |
| PR-223 | `[closed]` | [Edge Repo Contract Pass](PR-223-edge-repo-contract-pass.md) | PR-219..PR-222 | Edge repo contract cleanup | 0.25 d | QUIC config made explicit; VMUse stale fallback/legacy wording removed while preserving MCP-local base64 transport |
| PR-224 | `[closed]` | [Root Pytest Boundary Cleanup](PR-224-root-pytest-boundary.md) | PR-219..PR-223 | Root test entrypoint cleanup | 0.25 d | Root `pytest` now runs only root CI guard tests; stale Gateway-dependent `test_skills.py` removed |
| PR-225 | `[closed]` | [Residual App/Common/Docs Tail Cleanup](PR-225-residual-app-common-docs-tail-cleanup.md) | PR-224 | Maintenance entropy cleanup | 0.25-0.5 d | App VMUse resources synchronized and guarded; live compatibility tails removed; historical docs no longer look active |
| PR-226 | `[closed]` | [Guardrail Drift Cleanup](PR-226-guardrail-drift-cleanup.md) | PR-193, PR-225 | CI guard correctness | 0.25 d | Retired-path/main-path guards now match the current Entangled Activity projection path |
| PR-227 | `[closed]` | [Ignored Generated Artifact Hygiene](PR-227-ignored-generated-artifact-hygiene.md) | PR-225 | Workspace hygiene | 0.25 d | Ignored generated artifacts cleaned and source/resource hygiene guard added |
| PR-228 | `[closed]` | [Business Subagent State Matrix Authority Cleanup](PR-228-business-subagent-state-authority-cleanup.md) | PR-168E, PR-225 | Entangled authority boundary | 0.25-0.5 d | Business no longer exports or tests a duplicate subagent transition matrix as a truth source |
| PR-229 | `[closed]` | [Chat Message Lifecycle Shape Removal](PR-229-chat-message-lifecycle-shape-removal.md) | PR-168E, PR-225 | Message projection cleanup | 0.5 d | `messages` projection no longer keeps retired Agent-loop lifecycle columns/contracts |
| PR-230 | `[closed]` | [App One-off Patch Script Cleanup](PR-230-app-one-off-patch-script-cleanup.md) | PR-225 | App maintenance cleanup | 0.25 d | Tracked one-off UI patch and old AVD migration scripts removed |
| PR-231 | `[closed]` | [VNC / noVNC Boundary Cleanup](PR-231-vnc-novnc-boundary-cleanup.md) | PR-195, PR-225 | App VM display boundary | 0.5 d | Browser noVNC/VncProxy route surface removed while preserving required RFB capture paths |
| PR-232 | `[closed]` | [Roadmap Archaeology Noise Cleanup](PR-232-roadmap-archaeology-noise-cleanup.md) | PR-210, PR-225 | Documentation entropy cleanup | 0.25-0.5 d | Historical retired-path wording is fenced by stronger archaeology guard |
| PR-233 | `[deployed]` | [Active IM Delivery vs Wake Creation Hardening](PR-233-active-im-delivery-vs-wake-creation.md) | PR-153, PR-168, PR-186 | Agent loop lifecycle / explicit dependency boundary | multi-step | Active IM attaches to current wake; sleeping/dead sessions create new/recovery wakes |
| PR-233A | `[x]` | [Queue Active Inbox Dispatch Decision](PR-233A-session-dispatch-active-inbox.md) | PR-233 | Queue lifecycle | 0.5-1 d | Done |
| PR-233B | `[x]` | [Runtime `session.attach_input` Active Wake Delivery](PR-233B-runtime-session-attach-input.md) | PR-233A | Runtime/Cortex input delivery | 0.5-1 d | Done |
| PR-233C | `[x]` | [Dead Active Session Recovery and Structural Archive](PR-233C-dead-active-session-recovery.md) | PR-233A, PR-233B | Recovery / Cortex lifecycle | 1 d | Done |
| PR-233D | `[x]` | [Context Attached Input Observation Guardrails](PR-233D-context-attached-input-observation-guards.md) | PR-233B, PR-233C | Prompt/im_read observability | 0.5 d | Done |


---

## 2026-04-22 事故 → 工单映射

用户发 "hi hi" / "现在几点了" 连发消息后 agent 反复回旧消息、continuity 层不生效的那次事故，根因 A~F 对应的票：

| 现象（观察到的症状）                                             | 根因                                                                 | 票           | Phase           |
| ---------------------------------------------------------- | ------------------------------------------------------------------ | ----------- | --------------- |
| 新 user message 消失、11 条旧 USER_MESSAGE 每轮被重新注入 scope context | A：`handle_context_read` 扫 agent-wide `read=0` 而非 `payload.message_ids` | **PR-46**   | hotfix          |
| HealthWorker 对 4 天前的 pending USER_MESSAGE 无限 recovery      | B：recovery 没有绝对年龄上限 + 历史脏数据从未清理                                   | **PR-47**   | hotfix          |
| `subagents.handoff_notes` / `historical_summary` 一直 NULL    | C：LLM 端无 `_exec_subagent_rest` executor（PR-45 Wave 1.5 缺口）        | **PR-49**   | wave 1.5        |
| scope 永不进入 sleeping，PR-42/44/45 注入路径从未跑到                  | D：agent chat_reply 之后不 rest 也不 skill_end，runtime 没兜底               | **PR-48**   | hotfix          |
| Historical PR-44 `<CHAT_HISTORY>` replay symptom                  | E：D 的衍生（scope 不关，session.init 从不重新跑，`wake_replay_pending` flag 无处设置）| 由 **PR-48** 治本；顺带由 **PR-50** 做字节 cap | — |
| 连发 3 条消息 = 3 次 session.init；LLM 看到连珠炮拆散                   | F：subscriber 未做 IM 语义合批                                             | **PR-50**   | optimization    |

**推荐执行顺序**：PR-46 → PR-48 + PR-49（并行）→ PR-47 → PR-50。PR-46 是主动脉修复；PR-48/49 治本 "agent 不关门"；PR-47 清历史渣；PR-50 做 IM 体感优化。

**如果只能先上一张**：**PR-46**。它独立解决"新消息进不进 scope"的最严重一条，不需要 LLM 行为改变，也不依赖任何其他 PR，部署后今天这个事故模式立刻消失。

---

## 快速路径（新人开工顺序）

1. **今天/明天**（≤ 1 人日）：并行开 PR-01 / PR-02 / PR-03 / PR-04（M0 全部）
2. **本周**：PR-05 → PR-06，PR-07 → PR-08，PR-09（schema 迁移单独 PR）
3. **下周**：PR-10（关键）→ PR-11 / PR-12 / PR-13 并行
4. **W3-4**：PR-14 → PR-15 → PR-16 → PR-17（canary）→ PR-18 / PR-19
5. **W5-6**：PR-20..PR-27
6. W7+：PR-28+

---

## Review 归档

Reviewer 对已交付工单的评审意见，归档在 `reviews/PR-NN-review.md`：


| 工单    | Review                                             | 结论                       |
| ----- | -------------------------------------------------- | ------------------------ |
| Historical PR-01 review | [reviews/PR-01-review.md](reviews/PR-01-review.md) | archived historical review; PR-01 later closed |


## 跨工单基线（所有 PR 都应满足）

- **可观测性**：改动路径的入口处有 log（带 `scope_id` / `agent_id` / `caller`）
- **幂等**：任何写操作重复执行语义不变
- **fail-fast**：配置错误 / 依赖缺失 → 启动期爆；运行期错误不可被静默吞
- **Rollback**：每 PR 单独 revert 不破坏上游 PR
- **测试**：单测覆盖正常路径 + 至少两个失败分支
