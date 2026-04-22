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
| PR-43  | `[ ]`  | [Scope 续链 previous_scope_id + cortex assembly 读上一次 scope 尾部 K 步（R9 状态层）](PR-43-scope-chain-previous-id.md) | PR-20, PR-29, PR-39, PR-42          | R9 + R4                 | 2–3 d                        | __          |
| PR-44  | `[x]`  | [Wake 首轮 IM 流回放（最近 K 条 chat_messages 前置注入）](PR-44-wake-im-stream-replay.md) | PR-38, PR-42                        | R9 + R4                 | 0.5–1 d（2026-04-21 完成）                      | wangchaoqun          |


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
| PR-01 | [reviews/PR-01-review.md](reviews/PR-01-review.md) | `[~]` 返工（包名错位；详见 review） |


## 跨工单基线（所有 PR 都应满足）

- **可观测性**：改动路径的入口处有 log（带 `scope_id` / `agent_id` / `caller`）
- **幂等**：任何写操作重复执行语义不变
- **fail-fast**：配置错误 / 依赖缺失 → 启动期爆；运行期错误不可被静默吞
- **Rollback**：每 PR 单独 revert 不破坏上游 PR
- **测试**：单测覆盖正常路径 + 至少两个失败分支

