# Message → Wake 架构承诺

> **SSOT**。本文确立 "用户消息 / 系统事件 → Agent 唤醒 → Scope / Session → LLM 循环" 这条主干路径必须遵守的 **10 条架构承诺 (R1–R10)**。任何关于 Queue Service / dispatch / HealthWorker / Entangled 消息 / Cortex scope 的重构，都必须先对齐本页，再下沉到 [roadmap/message-wake-refactor.md](../roadmap/message-wake-refactor.md) 的实施清单。
>
> 2026-04-23 update：Phase 6（P6）收尾，将 `R9 Wake Continuity` 与 `R10 Consumer SSOT` 从 roadmap 标签**正式上升为架构承诺**，并补 §七 P6 事故复盘。
>
> 本文与 [cortex/invariants.md](../cortex/invariants.md) 平级：后者约束 Cortex 内部的并发/生命周期；本文约束 **跨服务的触发链路**。
>
> 起源：2026-04-17 `hihi` 消息 10 分钟无响应事件。表层是 `Queue Service /dispatch` 恒 400 + `/recover/all` 恒 401，根因是架构层 **"消息事件驱动"抽象缺位**（详见 §"诊断"）。

---

## 一、诊断（症状 → 架构裂痕）

| 今日症状 | 表层原因 | 架构裂痕 |
| --- | --- | --- |
| `hihi` 10 分钟没被处理 | HealthWorker 兜底 dispatch 被 Queue Service 拒 400 | **USER_MESSAGE 根本没有"主路径"，仅靠 30s 轮询兜底** |
| dispatch `user_id=""` 硬编码 | HealthWorker 从 `/internal/messages/unread-grouped` 拿不到 user_id | **跨服务合约没有统一字段矩阵**；**Cortex 内部 tenant 约束外泄成上游 HTTP 强校验** |
| `/api/queue/recover/all` 恒 401 | HealthWorker 裸 `httpx.Client` 没带 internal key | **internal auth 散弹式加固，没有调用方索引** |
| 卡了 10 分钟没人知道 | 只有 warning 日志，无 metric/alert | **"pending 消息"不是一等事件，异步进度不可观测** |
| 排查要串 entangled/gateway/queue/cortex 四份日志 | 无跨服务 trace | **scope_id 没被推成跨服务 trace 载体** |
| `trigger_type` 枚举漂移（`user_response` vs `user_message`） | 4 个触发点各写一份 | **没有单一的 Dispatch Assembler** |

底层是**同一件事**：Entangled 的写入事件**没有被抽象成服务端可订阅的 changefeed**，于是每个写入点都要靠"代码约定"手动再调 dispatch；约定一破就靠"兜底"挣扎；兜底再破就只能人肉。

---

## 二、承诺清单

| ID | 承诺 | 强制级别 |
| --- | --- | --- |
| **R1** | "消息到达 → wake" 必须有一条**一等公民**的主路径；`HealthWorker` 只做 recovery，不做主路径 | `[CONTRACT]` |
| **R2** | 所有 wake dispatch 必须通过唯一的 **Dispatch Assembler**；禁止直接 `httpx.post("/api/queue/dispatch")` | `[CODE]` |
| **R3** | `(agent_id → owner_user_id)` 由 **AgentOwnershipResolver** 统一解析；Cortex 的 tenant 约束**不许**外泄成上游 HTTP 契约 | `[CODE]` |
| **R4** | **Scope = 唯一 trace 载体**；**Message = lifecycle 事件**；两者通过 `scope.inputs[]` / `message.claimed_by_scope` 双向关联 | `[CODE]` |
| **R5** | `message.pending_for > 阈值` 是**一等事件**，必须产出 metric + alert，不只是 warning 日志 | `[CODE]` |
| **R6** | Entangled 对 `messages`（以及任何"触发实体"）的写入 = **服务端可订阅 changefeed**；dispatch 是 subscriber，而不是写入者的责任 | `[CODE]` |
| **R7** | Internal auth 走**唯一**颁发通道（统一 `internal_client`），加保护必须索引调用方 | `[CODE]` |
| **R8** | 一等实体（message / subagent / scope / saga / task）有**唯一权威状态枚举**与**受控转移**；废除"多字段拼状态" | `[CONTRACT]` 逐步 `[CODE]` |
| **R9** | **Wake Continuity**：agent 跨 sleep/wake 必须能继承**文字层（handoff notes + historical summary）**、**状态层（scope 链 / previous_scope_id）**、**IM 流层（chat history replay）**三层短期记忆，否则每次醒来都是失忆 | `[CODE]`（producer + consumer 两端） |
| **R10** | **Consumer SSOT**：runtime/消费端**只信 dispatch 透传的 id 集合**（`scope.meta.input_message_ids` 由 `/v1/scope/append_input` 落地，由 session.init / dispatch metadata 透传）；**禁止**消费端自己扫 `lifecycle='pending'` / `read=0` 反推"这次要处理哪些消息" | `[CODE]`（由 PR-46 强制；fallback 路径加 kill switch 不算违反） |

符号：
- `[CODE]`：在代码/中间件/断言层面强制。
- `[CONTRACT]`：靠评审 + 注释 + 调用方遵守。

---

## 三、逐条详述

### R1. "消息到达 → wake" 一等主路径

**现状**  
- `SPAWN_SUBAGENT` / `SUBAGENT_SEND` 在 `Business` 的 API handler 里 fire-and-forget 调 `_dispatch_trigger`（代码约定，分散）。  
- `USER_MESSAGE` **没有任何实时 dispatch 入口**，唯一通路是 `HealthWorker._scan_unhandled_messages` 30s 轮询。  
- `HealthWorker` 的命名、日志级别、间隔都表明它是 fallback，但对 USER_MESSAGE 它是**唯一路径**。

**承诺**
1. 任一 "能触发 wake 的消息"（USER_MESSAGE / SUBAGENT_SEND / SPAWN_SUBAGENT / SYSTEM_WAKE / …）落地 Entangled 时，**必须同步触发**一次 dispatch 尝试。
2. 这次尝试走主路径（R6 的 changefeed subscriber → R2 的 Assembler → Queue Service）。
3. `HealthWorker` 仅负责：
   - 已经 dispatch 但未进 active session 的"孤儿 saga"回收（task_timeout / saga_timeout）；
   - 主路径漏检的 `pending` 消息的**监控告警**（R5），不做再触发（或再触发时打上 `recovered=true` 标签，metric 分开）。
4. 主路径失败是一等故障；必须立刻对调用方可见（5xx 或显式 error 响应），**不允许**静默留给兜底。

**反例**：HealthWorker 打 warning，主路径什么都没做却返回 `200 OK`。

---

### R2. Dispatch Assembler：唯一合法 dispatch 入口

**现状**  
`subagent_id = f"main-{agent_id[:8]}"` 这一行代码在 `Business._dispatch_trigger` 和 `HealthWorker._scan_unhandled_messages` **各写了一份**。`trigger_type` 的取值在不同地方不同（`user_response` / `user_message`）。每加一个触发点，就多一次 "忘了 user_id / subagent_id 取错" 的机会。

**承诺**
1. 新增 `novaic_common.wake.DispatchAssembler`（库级），签名类似：
   ```
   assemble(trigger_source, agent_id, *, subagent_id=None, message_ids=None, metadata=None) -> DispatchRequest
   ```
   负责：
   - 解析 `user_id`（via R3 的 AgentOwnershipResolver）；
   - 推导 `subagent_id`（默认 `main-<agent_id[:8]>`，允许显式覆盖）；
   - 规范化 `trigger_type`（权威枚举：见下）；
   - 校验输出符合 Queue Service `/dispatch` 合约。
2. 所有触发点强制经 Assembler；CI 规则禁止再出现直接 `POST /api/queue/dispatch` 的字符串（除 Assembler 本身和测试）。
3. 权威 `trigger_type` 枚举（`novaic_common.wake.TriggerType`）：
   - `user_message` — 用户发的 USER_MESSAGE
   - `subagent_send` — 父 agent → 子 agent 的 SUBAGENT_SEND
   - `spawn_subagent` — SPAWN_SUBAGENT
   - `scheduled_wake` — `wake_at <= now` 定时
   - `system_wake` — 其它系统触发
   - `recovered` — 兜底补投（仅 HealthWorker 使用）
4. `wake_triggers` 表结构使用**同一枚举**。当前 `[{"type":"user_response"}]` 和 handler 默认 `user_message` 的漂移必须修平。

---

### R3. AgentOwnershipResolver：Cortex tenant 约束不许外泄

**现状**  
Cortex Meta skill 需要 `user_id` → Queue Service `/dispatch` 硬性 `user_id` 必填 → 所有上游触发点都被迫"生成"这个字段。上游数据源 `unread-grouped` 压根不返 user_id，于是 `""` 硬编码，400。

**承诺**
1. `(agent_id → owner_user_id)` 是**稳定事实**（agent 的 owner 不会变），应当由**一处**解析，不许每个 caller 自己拼。
2. 新增 `novaic_common.agents.AgentOwnershipResolver`：
   - 方式：Business 提供 `GET /internal/agents/{agent_id}/owner` 端点（或进程内缓存接口）；
   - Resolver 缓存（TTL 可调，5 min 起步），agent owner 本来就不常变。
3. `DispatchAssembler`（R2）在组装时**必须**调用 Resolver；上游只管传 `agent_id`。
4. Queue Service `/dispatch` 的 `user_id` 强校验**保留**（作为安全 tripwire），但不再穿透到上游——因为上游根本不直接调该端点（R2 已兜住）。
5. 若 Resolver 解析失败（agent 不存在 / 无 owner）→ Assembler 抛 `DispatchError(kind="no_owner")`；主路径显式失败，**不许**静默降级为 `user_id=""`。

---

### R4. Scope = 唯一 trace；Message = lifecycle 事件

**现状**  
- Message 的状态分散在 `read / processed / claimed_by / claimed_at / status` 五个独立字段，且在 hihi 事件里**全都是初始值**，无法告诉你它卡在哪一步。  
- Scope 不登记它消费了哪些 input message。  
- 没有跨服务 `scope_id` 日志前缀；排查要人肉串库。

**承诺**
1. **Message lifecycle 权威状态机**（N:1 安全，多消息可被同一 scope 认领）：
   ```
   pending
     ├── claimed(by_scope=<scope_id>)    # dispatch 成功 → 由某个 scope 吸入
     │      └── consumed                 # 该 scope 已处理完毕（scope_end 成功）
     ├── orphaned                        # 超时未被任何 scope 认领（R5 告警触发）
     └── deduped                         # 已被别的 trigger 归并，不再处理
   ```
   旧字段（`read / processed / claimed_by / claimed_at / status`）的语义合并进上面的状态 + metadata；`claimed_by` 含义从"worker_id"统一为"scope_id"。
2. **Scope metadata 反向登记 inputs**：Cortex `meta.json` 增加 `input_message_ids: [<msg_id>, ...]`，在 `session.init` 时写入；之后该 scope 期间继续 buffer 进来的消息以 `scope.append_input(msg_id)` 追加。
3. **scope_id 成为跨服务 trace_id**：
   - 所有后端服务（Business / Queue / Saga worker / Task worker / Cortex）的日志必须带 `scope_id=...`（或语义同源的 `trace_id`）。
   - 建议统一 logger context：`novaic_common.logging.bind(scope_id=...)`，handler 入口自动绑定。
4. "这条消息去哪了" 变成一次查询：
   ```
   message_id → claimed_by_scope → scope_id → 跨服务 trace
   ```

---

### R5. Pending 超时 = 一等事件

**现状**  
`msg pending 10min 无 scope` 这件事只在 health log 里躺着一行 warning。

**承诺**
1. 明确阈值（建议起步 `pending > 30s` 异常，`> 5min` 严重），阈值可配置。
2. 超时本身是**事件**，必须落在以下至少两处：
   - **Metric**：`outbox_lag_seconds` / `outbox_backlog_count`（gauge，subscriber tick 每轮更新，PR-32），`orphans_total{severity=warn|crit|permanent}`（counter，HealthWorker scan，PR-26 + TD-5）。
   - **可查视图**：`GET /internal/messages/orphaned` 或 CLI 工具直接列出。
   - **Alert**：至少一条"超过阈值 N 条 orphaned 消息"的告警（先内部 SSE / 日志 marker，后接正式告警系统）。
3. `HealthWorker` 职责转为 emitter：只负责检测 + emit 事件，**不再**隐式 re-dispatch（或 re-dispatch 必须带 `trigger_type=recovered` 在 metric 上可区分）。

---

### R6. Entangled 写入 = 服务端可订阅 changefeed

**现状**  
Entangled 的 `notifier` 只推同步客户端（Tauri / 浏览器），服务端 subscriber 不存在。于是"消息写入 → 唤醒"靠每个写入者自己 `_dispatch_trigger`。

**承诺**
1. 在 Entangled 侧为 `messages` 实体确立**内部 changefeed**。实现可选：
   - 进程内 pub/sub（简单，Entangled 是唯一进程）；
   - **outbox 表 + Business 侧 poller**（更解耦，可跨进程，推荐）；
   - 复用已有 notifier 抽象扩成"多 subscriber"（最小侵入）。
2. **Dispatch subscriber** 成为 changefeed 的一个消费者：
   - 收到新 `messages` 事件 → R2 的 Assembler → Queue Service；
   - 订阅器本身幂等（message_id 去重）；
   - 失败 → 消息留在 changefeed（或 outbox）可重试。
3. 写入者**不再承担** dispatch 责任：
   - `Business._dispatch_trigger` 在 `subagent_send` / `spawn_subagent` 路径中删除（由 subscriber 接管）；
   - 旧的 "HealthWorker fallback dispatch" 删除（R1、R5 已接管）。

---

### R7. Internal auth 统一策略

**现状**  
Queue Service `/recover/all` 加了 internal key 校验；HealthWorker 裸 `httpx.Client` 没带 → 恒 401。

**承诺**
1. 内部调用身份**只有一种颁发方式**：`novaic_common.http.clients.internal_client(service_name=..., base_url=...)`，自动注入：
   - `X-Internal-Key`（或对应头）
   - `X-Internal-Service: <caller-name>`（调用方身份，用于目标服务审计/限流）
2. 禁止在业务代码中再出现裸 `httpx.Client()`；CI 规则检查。
3. 任一新端点加 auth 保护时：
   - PR 描述必须列出"谁在调我"（通过搜索 `internal_client(base_url=<that_service>)` 得到）；
   - 所有这些调用方必须在**同一 PR 或前置 PR** 中升级到带身份的 client。
4. 老的 `internal_client` 已在 `novaic_common.http.clients`，只需把"默认就注身份头"这件事做成默认行为。

---

### R8. 状态机化一等实体

**现状**  
- `chat_messages`：`read / processed / claimed_by / claimed_at / status` 五字段拼状态。
- `subagents`：`status / wake_at / wake_triggers / need_rest / summary_lock` 拉平。
- `tq_tasks` 相对干净（`status / claimed_by / heartbeat_at / next_retry_at`），是目前最好的参照。

**承诺**
1. 每个一等实体一份：
   - **权威 Status 枚举**（Python `Enum`，schema `CHECK`）；
   - **转移表**（`ALLOWED_TRANSITIONS: dict[from, set[to]]`）；
   - **唯一写入函数** `update_state(entity, from, to, reason, metadata)`；禁止 `UPDATE table SET status=...` 散落代码。
2. 实体范围与负责模块（初步）：
   - `Message` — Entangled schema + `novaic-entangled` entity handler；
   - `Subagent` — Business subagent_utils；
   - `Scope` — Cortex scope state；
   - `Saga` / `Task` — 已有 Queue Service saga_repo / task_repo（主要补"转移统一入口"）。
3. 状态变更必须写入**转移日志**（可以是每个实体的 `state_log` 表/字段，或 metric 事件），便于事后追"为什么还在 sleeping"。
4. 这是长期重构；Phase 化推进（见实施清单）。

---

### R9. Wake Continuity：跨 sleep/wake 的短期记忆三层

**现状（P6 之前）**
- Agent 每次醒来 session.init 拉一个纯净 context，只塞 system prompt + 当前 trigger message。
- 上一次 scope 写的 `handoff_notes`、历史轮次压缩的 `historical_summary`、用户在 agent 睡眠期间发的未读 IM 消息，**全部不可见**。
- 表现：用户发"继续上次那个任务"，agent 回"请问上次是哪个任务"；agent 自己写的"下次醒来先处理 X"便条永远没被自己读到。

**承诺**（落地于 P6 Phase 6，2026-04-21 ~ 23 系列 PR）

Wake continuity 分三层，任一层 producer 断链都算违反本承诺：

1. **文字层**（PR-42 consumer + PR-45 / PR-49 producer）
   - `subagents.handoff_notes` — LLM 自述便条，由 `subagent_rest` tool 工具调用写入（PR-49 实现 executor）
   - `subagents.historical_summary` — 自动滚动摘要，由 rest saga 写入（PR-45 Wave A）
   - session.init 渲染为 `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` system message（PR-42 builder）
   - Dispatch metadata 透传（PR-45 Wave B — DispatchSubscriber 注入 / HealthWorker 注入）
2. **状态层**（PR-43，规划中）
   - `scope.meta.previous_scope_id` 指向上一次该 agent 的已 archived scope 根
   - session.init 可选读取 `<PREV_SCOPE_TAIL>` 段
3. **IM 流层**（PR-44 + PR-50 Wave 1）
   - session.init 在 trigger message 之外回溯最近 N 条 USER_MESSAGE/AGENT_REPLY 塞入 `<CHAT_HISTORY>` 段
   - 字节 cap 由 `WAKE_REPLAY_MAX_BYTES` 控制，溢出时插入 `CHAT_HISTORY_TRUNCATED` 系统消息

**边界**
- Wake continuity 不等于"无限上下文"—— 它是 agent 自己 + 系统帮它省下的**必要、有界**短期记忆。
- 每一层都可通过 env 关闭：`WAKE_CONTINUITY_TEXT=0` / `WAKE_SCOPE_CHAIN=0` / `WAKE_IM_REPLAY_ENABLED=0`。

**反例**
- P6 初期（2026-04-21）线上：`subagents.handoff_notes` 永远 NULL，因为 `subagent_rest` tool 没有 executor（PR-49 之前）；user 眼里是"agent 失忆"。
- `scope` 永远不关（PR-48 之前）→ session.init 从不重跑 → R9 全层集体空跑。

---

### R10. Consumer SSOT：runtime 消费端只信 dispatch 透传的 id 集合

**现状（P6 之前）**
- Runtime 的 `handle_context_read` 每次被调用，都重新扫 Entangled `chat_messages where read=0`（"所有未读消息"）拼当前 context。
- 多条消息挤到同一个 wake：第一条处理完、第二、三条还没 `read=1`，下一 LLM round 的 context-read 再扫一次，**把已经处理过的消息又读一遍**，agent 反复回复同一段内容。
- 更恶性：`read=0` 的消息如果跨多个 agent，消费端无法区分"这是给我的"还是"给别人的"。

**承诺**（落地于 PR-46，2026-04-22 部署）

1. **SSOT**：本次 wake 的"输入消息集合"**只有一处**权威来源 —— `scope.meta.input_message_ids`：
   - 写入者：Subscriber 在 dispatch 成功后调 `POST /v1/scope/append_input`（saga_started / buffered 两个分支都会）
   - 写入者：Runtime `handle_session_init` 从 dispatch payload 的 `metadata.message_ids` 落地
2. **读取**：消费端（`handle_context_read` / 其它任何 runtime consumer）**只信** `scope.meta.input_message_ids` 的内容，逐 id 调 `entity_get` 补齐 body。**禁止**：
   - `SELECT * FROM chat_messages WHERE read=0`
   - `SELECT * FROM chat_messages WHERE lifecycle='pending'`
   - 任何不以 `input_message_ids` 为起点的扫表式拼装
3. **Kill switch**：`CONTEXT_READ_BY_IDS=0` 恢复 legacy scan（仅供应急回退；正常请求必须走 by-ids 路径）。
4. **新消息落地**：在 agent wake 执行中途到达的新消息，通过 `append_input` 扩充 `input_message_ids`，让下一 round 的 context-read 自然看见；不走"消费端再扫一次"的路径。

**为什么叫 Consumer SSOT**  
`R4 (Scope = trace 载体)` 已经承诺 scope.inputs 是双向链路，R10 是它的**强化版**：明确"**非授权扫表**是一等禁用行为"。这条在 P6 之前是"最佳实践"，在 PR-46 之后是 `[CODE]` 契约。

**反例**（全部在 P6 期间修掉）
- `handle_context_read` 扫 `read=0` → 重复消费 → 重复回复（PR-46 修）
- `chat_messages.read` 字段被 runtime 读作"这条我见过没" → 已由 R10 明确降级为 **UI-only**（下方 §UI-only 列表）

**UI-only 字段清单**（任何 runtime/subscriber/assembler/healthworker 代码对这些字段的**读取**都视为违反 R10；写入由 UI/Business API 层独占）：
- `chat_messages.read` — 客户端未读气泡
- `chat_messages.starred` / `chat_messages.pinned`（若后续引入）

---

## 四、与 Cortex Invariants 的关系

本页 R1–R8 与 [cortex/invariants.md](../cortex/invariants.md) 的 INV-1~10 **不冲突、层次不同**：

- **INV-x**：Cortex 内部（并发、生命周期、锁、错误分类、观测）的硬约束。
- **R-x**：**跨服务链路**（Entangled / Business / Queue / Runtime / Cortex）的硬约束。

本次 hihi 事件里，INV-x 全部健康（Redis 锁生效、scope 生命周期干净），问题出在 R-x 完全缺位。

---

## 五、与本次 bug 的对照

回归不能只靠承诺背书——每条都给出**可 grep 的当下证据**（metric 名 + 日志关键字），避免"说好了"但实际上没 hookup 的静默失败。evidence 列来自 PR-05 / PR-06 / PR-10 / PR-14 / PR-16 / PR-24 / PR-26 / PR-31 / PR-32 的落地位点。

| 今日症状 | 被哪条彻底消解 | metric evidence | log evidence |
| --- | --- | --- | --- |
| `user_id=""` 硬编码 → 400 | **R2 + R3**（Assembler 必然拿得到 user_id） | `ownership_resolver_total{result=hit\|miss\|error}` / `dispatch_total{result=no_owner}` (PR-32) | `event=resolver_hit` / `event=dispatch action=... user_id=...`（common.wake.assembler DEBUG 线） |
| `/recover/all` 401 没人发现 | **R7** | `internal_requests_total{caller,target,status}` (PR-06 + PR-32，response event-hook) | `common.middlewares.caller_logging` 写的 `incoming ... caller=...` 每条请求都带；401 → `status=401` label 直接上 metric |
| HealthWorker 是唯一通路 | **R1 + R6** | `subscriber_delivered_total{trigger}` vs `healthworker_recovered_total` 比值（PR-19 + PR-32） | `event=outbox_enqueue message_id=... trigger=...`（Entangled write path） / `event=subscriber_delivered id=...` |
| 10 分钟没人知道卡住 | **R5** | `outbox_lag_seconds` / `outbox_backlog_count` gauge (PR-32, subscriber tick) + `orphans_total{severity=warn\|crit\|permanent}` (PR-26 emission + TD-5 hook into PR-32 registry) | `ORPHAN message_id=... age=...` / `orphan_warn ...` / `PERMANENT_ORPHAN message_id=... kind=...` (HealthWorker) |
| 排查要串四份日志 | **R4**（scope_id 贯穿） | — | `install_service_logging` 的 `%(scope_id)s` 列在 business/entangled/cortex/subscriber 四份日志上格式一致（PR-24）；`/internal/messages/<id>/trace` 把四份合成一个响应（PR-25） |
| `user_response` vs `user_message` 枚举漂移 | **R2**（枚举集中） | `outbox_enqueued_total{trigger_type}` / `dispatch_total{trigger_type}` label 域由 `TriggerType` 枚举收敛（PR-09 + PR-32） | `event=outbox_enqueue ... trigger=<canonical>` — 非枚举值在入口 raise，不会落日志 |
| `processed / read / claimed_by` 三字段各说各话 | **R4 + R8** | — | `message_state_transitions` 持久表（PR-21 + PR-31）+ `event=message_state msg=... from=... to=...` 日志；`subagent_state_transitions` 同形（PR-28 + PR-31b）；`transition("claimed")` 由 subscriber 独家写（PR-22） |
| agent 每几分钟自动醒来（无用户动作） | **R10**（消费端不再扫 `read=0` 造假触发） + R8 amend（PR-41 非 trigger 类消息建 SQL 时就 `lifecycle=consumed`） | `orphans_total{severity=warn}` 应当趋零 | `event=message_state ... to=consumed reason=non_trigger_on_create`（PR-41 amend） |
| agent 醒来看不见历史上下文（"失忆"） | **R9**（三层分别走完 producer → consumer） | `continuity_resolve_total{result=ok\|empty\|not_found\|error}`（PR-45 subscriber 侧） | `event=continuity_resolve agent=... result=ok`（DispatchSubscriber） / session.init 的 `<HANDOFF_NOTES>`/`<HISTORICAL_SUMMARY>` 段 |
| 同一条 user message 被 agent 连续复读 | **R10**（PR-46: context.read 只读 `scope.meta.input_message_ids`） | — | `event=context_read source=input_message_ids count=N`（PR-46 log；legacy scan 路径被 env kill switch 隔离） |
| scope 永远 running 导致 R9 全层空跑 | **R8 + R9 producer 闸**（PR-48 Turn Finalizer：LLM 只调 `chat_reply` 一类 closer 工具时强制 `subagent_rest`） | `turn_finalizer_forced_rest_total`（PR-48） | `event=turn_finalizer action=forced_rest reason=only_closer_tools` |
| 消息停在 `claimed` 永远无人消费 | **R8 + R4**（PR-51 Part 2：HealthWorker 每 30s 扫双轴老 claimed 行，转 consumed） + **R10**（PR-52：subscriber 重试不再为死 scope 再起新 scope） | `stuck_claimed_total{axis=lifecycle\|created}`（PR-51 Part 2） / `subscriber_stale_claim_total{result=...}`（PR-52） | `STUCK_CLAIMED msg=... age=... axis=...`（HealthWorker） / `STALE_CLAIM_DEAD_SCOPE msg=... scope=...`（subscriber） |
| `<CHAT_HISTORY>` 膨胀到 token 预算爆表 | **R9 IM 流层 + 预算纪律**（PR-50 Wave 1 `WAKE_REPLAY_MAX_BYTES` 硬字节 cap + 截断标记） | — | session.init context 尾部出现 `CHAT_HISTORY_TRUNCATED system message`（PR-50 Wave 1） |

补 metric 查询入门（`/metrics` 的两个常见用法）：

```bash
# 消息堆多少、最老一条多久了
curl -s http://business:19998/metrics | grep -E '^(outbox_backlog_count|outbox_lag_seconds)'
# 内部调用 401 / 5xx 占比
curl -s http://business:19998/metrics | grep '^internal_requests_total{.*status=(4|5)'
```

后续恢复实时流量前，把这两条串进 `scripts/canary/bake-snapshot.sh` 的 `metric` 段（PR-35 §B2 曾取消的 cron 快照位已预留）。

---

## 六、事故复盘 — P6 期间（2026-04-21 ~ 04-23）

**起源**：两个用户抱怨串在一起爆出整条 wake continuity 生产线的裂纹。

1. **"agent 每几分钟自动苏醒一次"** — 明明没发消息，日志里却有周期性 wake。
2. **"苏醒时没有带历史 scope，上下文设计的很糟糕"** — 让 agent 续做上次的事，它当场失忆。

**诊断**（六条根因，每条一张工单）

| 根因 | 表现 | 修复 | 承诺落地 |
| --- | --- | --- | --- |
| **A** `handle_context_read` 扫 `read=0` 反推输入 | 同一条消息被 agent 反复回复 | **PR-46**：只按 `scope.meta.input_message_ids` 装配 context，逐 id `entity_get` | **R10** 成为 `[CODE]` |
| **B** HealthWorker 无年龄上限地 recover 古老 `pending` 行 | 一条几天前的 `hihi` 突然被重新派发，唤出新 scope | **PR-47**：`MAX_RECOVERY_AGE_SEC` + `pending → consumed` 管理性短路 | R5 加固 |
| **C** `subagent_rest` LLM 工具没有 executor | `handoff_notes` 永远 NULL，文字层 producer 断链 | **PR-49**：实现 `_exec_subagent_rest` 落库 | **R9 文字层 producer** 闭合 |
| **D** scope 永远 running（LLM 只回复，不 rest） | session.init 从不重跑，R9 全层空跑 | **PR-48**：Turn Finalizer 强制 `subagent_rest` | **R8 + R9 producer 闸** |
| **E** `chat_messages.lifecycle` 对非 trigger 类消息（AGENT_REPLY 等）默认 `pending` | HealthWorker 误以为有事，每 30s 刷一次"自动苏醒" | **PR-41 + amend**：`_sql_create` / `append` 统一走 `_stamp_consumed_if_non_trigger` | R8 amend |
| **F** `<CHAT_HISTORY>` 无字节 cap + 聚合缺失 | 稠密会话下 token 预算爆表 | **PR-50 Wave 1** 字节 cap + 截断标记（Wave 2 business 端 60s 合批待开） | **R9 IM 流层 + 预算纪律** |

**连锁反应**（P6 修复过程中新发现）

| 连锁问题 | 触发条件 | 修复 |
| --- | --- | --- |
| `chat_messages.lifecycle='claimed'` 永不变 consumed（因原 scope 死亡 + PR-48 之前 scope 永不归档） | 任何 C/D/E 组合失败的历史残留 | **PR-51 Part 1**：一次性 SQL 迁移清 prod 25/28 行；**Part 2**：HealthWorker 双轴（`lifecycle_updated_at` 24h + `created_at` 72h）周期扫描 + Entangled/Business endpoint |
| Subscriber 重试把一条老 `pending` 派到**新** Queue session → 拉起全新 scope 填满 stuck-claimed | outbox retry（subscriber 曾经 die 在 assemble_sync 与 mark_delivered 之间） | **PR-52**：subscriber 在 `attempts > 0` 上 probe `chat_messages.lifecycle` + Cortex `meta.phase`，死 scope / live scope / consumed 都 `mark_delivered` 不再派发 |

**经验沉淀（新增 R-INV 的动因）**

- **R9 上升为 `[CODE]`**：P6 之前 continuity 是 "PR-42 设计文档里写了"，生产线上全断；现在 producer 三条链路、consumer 三个 render 位点、kill switch、metric 全部 `[CODE]` 级绑定。
- **R10 上升为 `[CODE]`**：根因 A 的教训——"消费端扫表自己反推输入"是**反模式**，必须 `[CODE]` 级禁止。PR-46 的 `CONTEXT_READ_BY_IDS` 默认 on 是技术落地，本页承诺是合同兜底。
- **UI-only 字段**：`chat_messages.read` 被不同代码各自解读成 "这条我处理过没"，是 R8 "多字段拼状态" 的活化石。明确列在 R10 下限定用途。

**Canary / 监控补齐**（待办，落在 P7）

- `ghost_scope_rate` — `scope 被创建 → 1 分钟内被 archive 但 chat_messages 仍在 claimed` 的比例，需要 PR-25 trace 视角 + metric。
- `wake_continuity_render_total{layer=text|state|im, result=ok|empty|truncated}` — 三层 render 落地率，一个指标看清 R9 是否还在活着。

---

## 七、落地

- 实施清单（可勾选）：[roadmap/message-wake-refactor.md](../roadmap/message-wake-refactor.md)
- 技术债索引：[roadmap/technical-debt.md](../roadmap/technical-debt.md)（已引用本页）
- Cortex 内部硬约束：[cortex/invariants.md](../cortex/invariants.md)、[cortex/hardening-checklist.md](../cortex/hardening-checklist.md)
