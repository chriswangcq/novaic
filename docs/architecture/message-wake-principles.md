# Message → Wake 架构承诺

> **SSOT**。本文确立 "用户消息 / 系统事件 → Agent 唤醒 → Scope / Session → LLM 循环" 这条主干路径必须遵守的 **8 条架构承诺 (R1–R8)**。任何关于 Queue Service / dispatch / HealthWorker / Entangled 消息 / Cortex scope 的重构，都必须先对齐本页，再下沉到 [roadmap/message-wake-refactor.md](../roadmap/message-wake-refactor.md) 的实施清单。
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
   - **Metric**：`novaic_messages_pending_seconds`（histogram），`novaic_messages_orphaned_total`（counter）。
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

## 四、与 Cortex Invariants 的关系

本页 R1–R8 与 [cortex/invariants.md](../cortex/invariants.md) 的 INV-1~10 **不冲突、层次不同**：

- **INV-x**：Cortex 内部（并发、生命周期、锁、错误分类、观测）的硬约束。
- **R-x**：**跨服务链路**（Entangled / Business / Queue / Runtime / Cortex）的硬约束。

本次 hihi 事件里，INV-x 全部健康（Redis 锁生效、scope 生命周期干净），问题出在 R-x 完全缺位。

---

## 五、与本次 bug 的对照

| 今日症状 | 被哪条彻底消解 |
| --- | --- |
| `user_id=""` 硬编码 → 400 | **R2 + R3**（Assembler 必然拿得到 user_id） |
| `/recover/all` 401 没人发现 | **R7** |
| HealthWorker 是唯一通路 | **R1 + R6** |
| 10 分钟没人知道卡住 | **R5** |
| 排查要串四份日志 | **R4**（scope_id 贯穿） |
| `user_response` vs `user_message` 枚举漂移 | **R2**（枚举集中） |
| `processed / read / claimed_by` 三字段各说各话 | **R4 + R8** |

---

## 六、落地

- 实施清单（可勾选）：[roadmap/message-wake-refactor.md](../roadmap/message-wake-refactor.md)
- 技术债索引：[roadmap/technical-debt.md](../roadmap/technical-debt.md)（已引用本页）
- Cortex 内部硬约束：[cortex/invariants.md](../cortex/invariants.md)、[cortex/hardening-checklist.md](../cortex/hardening-checklist.md)
