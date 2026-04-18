# Message → Wake 重构实施清单

> 基于 [architecture/message-wake-principles.md](../architecture/message-wake-principles.md) 的 8 条架构承诺 (R1–R8) 下沉成**可执行、可勾选、可追溯**的六阶段清单。
>
> **更细粒度的 PR 级工单（每 PR 一文件，含完整 checklist）→ [tickets/](tickets/README.md)**
> 本页仍是阶段/条目视角的 SSOT；tickets 目录是工程师每天做事用的工单。
>
> 状态标记：`[ ]` 未做、`[x]` 已完成、`[~]` 进行中、`[!]` 已确认为假警报（无需做）。
>
> 每项携带 ID（方便 PR/commit 引用）、承诺来源、严重度、范围、前置、验收标准、回归测试、可观测性要求、回滚方案。
>
> **Release gating rule**：
> - Phase 1 未清零前不允许对 `Business._dispatch_trigger` / `HealthWorker._scan_unhandled_messages` 做任何业务增量；  
> - Phase 2 未清零前不允许新增消息类型（新 trigger_type）；  
> - Phase 3 未清零前不允许声称系统具备"端到端异步可观测性"。

---

## 前置 / 工程卫生

| ID | Status | Item | 来源 |
| --- | --- | --- | --- |
| M0-1 | `[ ]` | `novaic_common.wake` 包骨架（`__init__.py`、`assembler.py`、`trigger_types.py`、`errors.py`） | R2 |
| M0-2 | `[ ]` | `novaic_common.agents.ownership` 包骨架 | R3 |
| M0-3 | `[x]` | `docs/architecture/message-wake-principles.md` 接入 `docs/README.md` 架构表 | — |
| M0-4 | `[x]` | `roadmap/technical-debt.md` 引用本页并标记"进行中" | — |
| M0-5 | `[x]` | CI lint 规则：禁止业务代码直接 `httpx.post(...".../api/queue/dispatch"...)` 字符串（allowlist：`common/wake/assembler.py`、tests） | R2 |
| M0-6 | `[x]` | CI lint 规则：禁止业务代码直接 `httpx.Client()`（allowlist：`common/http/clients.py`、测试工具） | R7 |

---

## Phase 1 — 合约对齐前置（R7 + R3 + R2）

> **目标**：在不动任何主路径的情况下，先把"字段 / 身份 / 入口"三层基础补齐，为 Phase 2 的路径切换做准备。
> **DoD**：全系统所有 dispatch 都经 Assembler；所有 internal 调用都带身份头；Cortex 的 user_id 需求有唯一 resolver。

### P1-1  统一 internal client（带身份头）
- Status: `[ ]`
- Severity: High（401 盲区）
- Scope: `novaic_common/http/clients.py`
- 前置：无
- 任务：
  - [ ] `internal_client(service_name, base_url, ...)` 增加 `service_name` 必填参数
  - [ ] 默认注入 `X-Internal-Key`（环境变量，已存在）+ `X-Internal-Service: <service_name>`
  - [ ] 为老调用点迁移（逐个 grep `internal_client(`）
- 验收：`rg "internal_client\(" novaic-*/` 所有命中都带 `service_name`
- 可观测性：Queue Service / Cortex 访问日志打印 `caller=<service_name>`
- 回滚：保留老函数签名做重载过渡，灰度回退只需改导入
- 承诺：R7

### P1-2  目标服务消费 `X-Internal-Service`
- Status: `[x]`
- Scope: `novaic-cortex/novaic_cortex/auth.py`（或等价位置）、`queue_service/auth.py`、`novaic-business/business/*/auth.py`
- 任务：
  - [x] auth 中间件读取 `X-Internal-Service`，未提供 → 记 WARN（灰度期不拒）
  - [x] 访问日志字段 `caller` 必带
- 验收：手工用三种身份（cortex/runtime/business）调 Queue Service，日志里 caller 正确
- 承诺：R7

### P1-3  `AgentOwnershipResolver` 实现
- Status: `[x]`
- Scope: `novaic_common/agents/ownership.py` + `novaic-business/business/internal/agents.py`
- 任务：
  - [x] Business 新增 `GET /internal/agents/{agent_id}/owner` → `{user_id}` / 404
  - [x] `AgentOwnershipResolver`（进程内 TTL 缓存，默认 5 min）
  - [x] `resolve(agent_id) -> str | raise AgentNotOwnedError`
- 验收：单测覆盖「命中 / 不存在 / 缓存命中 / TTL 过期」
- 回归：mock Business 404 → resolver raise 明确错误
- 承诺：R3

### P1-4  `TriggerType` 权威枚举
- Status: `[x]`
- Scope: `novaic_common/wake/trigger_types.py`
- 任务：
  - [x] `TriggerType(Enum)`：`USER_MESSAGE / SUBAGENT_SEND / SPAWN_SUBAGENT / SCHEDULED_WAKE / SYSTEM_WAKE / RECOVERED`
  - [x] 迁移现有字符串常量到枚举
  - [x] `wake_triggers` 默认值 `[{"type": "user_response"}]` **改为** `"user_message"`（schema 默认 + 迁移 SQL）
- 验收：`rg 'user_response'` 无剩余业务代码命中
- 迁移：`UPDATE subagents SET wake_triggers = REPLACE(wake_triggers, 'user_response', 'user_message')`（Entangled schema push 版本号 +1）
- 承诺：R2

### P1-5  `DispatchAssembler` 实现
- Status: `[x]`
- Scope: `novaic_common/wake/assembler.py`
- 任务：
  - [x] `DispatchRequest` dataclass（含所有 Queue Service 必填）
  - [x] `DispatchAssembler.assemble(trigger_source, agent_id, *, subagent_id=None, message_ids=None, metadata=None) -> DispatchRequest`
    - [x] 调 `AgentOwnershipResolver` 解析 user_id
    - [x] 默认 `subagent_id = f"main-{agent_id[:8]}"`
    - [x] 校验 trigger_source 是 `TriggerType` 枚举
    - [x] metadata 里附 `message_ids`（供 R4 的 scope.inputs 登记）
  - [x] `DispatchAssembler.dispatch(req) -> DispatchResult`（调 Queue Service `/dispatch`，走 P1-1 的 `internal_client`）
  - [x] 失败抛明确 `DispatchError(kind="no_owner"|"queue_400"|"queue_5xx"|"network")`，绝不吞
- 验收：
  - [x] 单测：mock resolver + mock HTTP，各路径覆盖
  - [x] 合约测试：assemble 输出必定通过 Queue Service `DispatchRequest.validate()`
- 承诺：R2 + R3

### P1-6  老 `_dispatch_trigger` 迁到 Assembler
- Status: `[x]`
- Scope: `novaic_business`, `novaic_health_worker`, `novaic_scheduler`
- 任务：
  - [x] 把原有的直接 `httpx.post('/dispatch')` 代码删掉
  - [x] 注入并调用 `DispatchAssembler.assemble_and_dispatch`
  - [ ] **暂时保留**函数名作为薄壳（Phase 2 会彻底删）
- 验收：subagent_send 端到端依然工作（单测 + 手工触发）
- 承诺：R2

### P1-7  `HealthWorker._scan_unhandled_messages` 迁到 Assembler
- Status: `[x]`
- Scope: `novaic-agent-runtime/task_queue/workers/health_worker_sync.py`
- 任务：
  - [ ] 用 `DispatchAssembler` 替换手工拼请求；
  - [ ] 不再硬编码 `user_id=""`（resolver 解析）；
  - [ ] Phase 2 会整个删掉，本步骤只是让它先不 400。
- 验收：health log 里 `Fallback dispatch failed` 消失（对现有未处理消息）
- 承诺：R2 + R3

### P1-8  `Scheduler worker` 迁到 Assembler
- Status: `[x]`
- Scope: `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py`
- 任务：
  - [x] 将旧的 `/dispatch` 定时唤醒调用迁为 `assembler.assemble_and_dispatch(TriggerType.SCHEDULED_WAKE, ...)`
- 验收：`rg 'httpx\..*/dispatch' novaic-agent-runtime/` 应当不再包含 scheduler_worker
- 承诺：R2

---

## Phase 2 — 主路径切换（R1 + R6）

> **目标**：让 Entangled 消息写入驱动 dispatch；HealthWorker 从"唯一主路径"降级为"recovery only"。
> **DoD**：没有任何业务代码手写 dispatch；dispatch 仅由 changefeed subscriber 发起。

### P2-1  选型 changefeed 载体
- Status: `[x]`
- Scope: `novaic-entangled/` + `novaic-business/` 决策会议
- 任务：
  - [ ] 在三种方案中二选一：
    - A. 进程内 pub/sub（Entangled 单进程；最简单；跨进程不可用）
    - B. **outbox 表 + Business poller**（解耦；跨进程；推荐）
    - C. Entangled 现有 notifier 扩多 subscriber（侵入小但耦合深）
  - [ ] 决策记录写入 `docs/architecture/message-wake-principles.md` 附录或本文
- 验收：决策文档落地
- 承诺：R6

### P2-2  实现 changefeed / outbox
- Status: `[x]`
- Scope: `Entangled/packages/server-python/entangled/sql/entity_store.py` + `novaic-business/business/schema_push.py`
- 方案 B 任务示例：
  - [ ] Entangled schema 新增 `message_outbox` 表 `(id, message_id, agent_id, type, created_at, delivered_at, attempts, last_error)`
  - [ ] 每次写 `chat_messages` 在同事务内插入 outbox 条目
  - [ ] Business 新增 poller 服务（或 entity_queue 子进程）：读 `delivered_at IS NULL` → 走 Assembler → mark delivered / 增 attempts
  - [ ] outbox 保留 7 天（运维可清理）
- 验收：
  - [ ] 并发写 100 条消息，100 条 outbox 事件都被消费；无丢失无重复（看 metric `dispatch_by_subscriber_total`）
  - [ ] subscriber crash 后重启可继续
- 可观测性：
  - [ ] metric `outbox_lag_seconds`（新事件 - 最老未消费）
  - [ ] metric `outbox_attempts_total{result=ok|retry|failed}`
- 承诺：R6

### P2-3  Dispatch subscriber（Business 侧或独立进程）
- Status: `[ ]`
- Scope: `novaic-business/business/subscribers/dispatch_subscriber.py`（新建）
- 任务：
  - [ ] 订阅 outbox / changefeed
  - [ ] 过滤：只消费 `wake-triggering` 消息类型（USER_MESSAGE / SUBAGENT_SEND / SPAWN_SUBAGENT / …）
  - [ ] 幂等：同一 message_id 已 dispatch 过 → 跳过
  - [ ] 调 `DispatchAssembler`
  - [ ] 成功 → mark outbox delivered；失败 → attempts+1，retry backoff
- 验收：
  - [ ] 发一条 USER_MESSAGE → Queue Service 收到且只收到一次 dispatch
  - [ ] Subscriber 重启 → 未消费事件会被重放但最终 exactly-once（靠 message_id 去重）
- 承诺：R1 + R6

### P2-4  删除"消息写入处手写 dispatch"
- Status: `[ ]`
- Scope: `novaic-business/business/internal/subagent.py`
- 任务：
  - [ ] 删 `_dispatch_trigger` 函数本体
  - [ ] `subagent_send` / `spawn_subagent` 写完消息后**不再**调它（由 subscriber 接管）
  - [ ] Grep 确认 `_dispatch_trigger` 无残留 caller
- 验收：subagent_send 端到端仍工作（由 subscriber 接管后）
- 回滚：P2-3 failing → 暂时恢复 P1-6 的 Assembler 直调，再查 subscriber
- 承诺：R1 + R6

### P2-5  HealthWorker 降级为 recovery
- Status: `[ ]`
- Scope: `novaic-agent-runtime/task_queue/workers/health_worker_sync.py`
- 任务：
  - [ ] 删除 `_scan_unhandled_messages` 的"re-dispatch 消息"职责
  - [ ] 只保留 `/api/queue/recover/all`（孤儿 task/saga 回收）
  - [ ] P3 才加"pending 超时 emitter"职责（不在此处）
- 验收：HealthWorker 日志里不再出现 `Fallback dispatch`；400/401 全绝
- 承诺：R1

### P2-6  端到端冒烟
- Status: `[ ]`
- 步骤：
  - [ ] 清库 → 发 `hihi` → 观察：
    - Entangled `chat_messages` 写入
    - outbox 事件产生（方案 B）
    - subscriber 消费日志
    - Queue Service 收到 1 次 dispatch（200 OK）
    - Saga 启动 / Cortex scope 建立
    - agent 回复
  - [ ] 压测：1 秒内 10 条消息 → 同一 agent → 只启 1 个 active session，其余 buffered（已由 P0-3 覆盖）
- 承诺：R1

---

## Phase 3 — Scope trace + Message lifecycle（R4）

> **目标**：让 "这条消息去哪了 / 这个 loop 卡哪了" 变成一次查询。

### P3-1  Scope metadata 登记 inputs
- Status: `[ ]`
- Scope: `novaic-cortex/novaic_cortex/scope.py` + `agent_runtime/handlers/runtime_handlers.py::handle_session_init`
- 任务：
  - [ ] Scope `meta.json` 增加字段：`input_message_ids: list[str]`
  - [ ] `session.init` payload 必带 `message_ids`（Assembler 已在 P1-5 metadata 里附）
  - [ ] Cortex API 新增 `POST /v1/scope/{id}/append_input { "message_ids": [...] }`（session 进行中继续 buffer 的消息追加登记）
- 验收：
  - [ ] 任一 scope 能通过 `meta.json` 查到它消费了哪些消息
  - [ ] N 条消息 buffer 进同一 scope → inputs 长度 = N
- 承诺：R4

### P3-2  Message lifecycle 状态字段
- Status: `[ ]`
- Scope: Entangled schema + `novaic-entangled` entity handlers
- 任务：
  - [ ] 新增状态枚举字段 `lifecycle: pending | claimed | consumed | orphaned | deduped`
  - [ ] 保留旧字段（`read / processed / claimed_by / claimed_at / status`）一个 release，观察期后删
  - [ ] `claimed_by` 语义改为 `claimed_by_scope`（存 scope_id）
  - [ ] 状态转移走唯一入口 `message_state.transition(msg_id, to, scope_id=...)`
- 验收：
  - [ ] 发消息 → pending
  - [ ] subscriber dispatch 成功 → claimed(scope_id=X)
  - [ ] scope_end 成功 → consumed
  - [ ] 超时未 claim → orphaned（Phase 4 告警）
- 承诺：R4 + R8（message 实体状态机化）

### P3-3  Subscriber 在 dispatch 成功时 transition → claimed
- Status: `[ ]`
- Scope: `novaic-business/business/subscribers/dispatch_subscriber.py`
- 任务：
  - [ ] Queue Service `/dispatch` 返回体带 `scope_id`（已有）
  - [ ] Subscriber 拿到 `scope_id` 后 transition 消息到 `claimed(by_scope=scope_id)`
- 验收：成功 dispatch 的消息 100% 落到 claimed
- 承诺：R4

### P3-4  scope_end 触发 consumed
- Status: `[ ]`
- Scope: Cortex `/v1/scope/{id}/end` / session.ended handler
- 任务：
  - [ ] scope_end 成功时（归档完成）→ 对 `scope.inputs` 里所有 message_id transition 到 `consumed`
  - [ ] scope_end 失败不 transition（保持 claimed，待重试或 orphan 超时）
- 验收：正常完成的 session 其 inputs 100% 变 consumed
- 承诺：R4

### P3-5  跨服务 `scope_id` 日志绑定
- Status: `[ ]`
- Scope: `novaic_common/logging/context.py`（新建）+ 全 handler 入口
- 任务：
  - [ ] `LogContext` contextvar；handler 入口 `bind(scope_id=..., agent_id=..., user_id=...)`
  - [ ] 默认 log formatter 输出 `scope_id=<id>` 前缀
  - [ ] Business / Queue / Saga worker / Task worker / Cortex 全部接入
- 验收：
  - [ ] 任取一个 scope_id，用 `rg "scope_id=<id>"` 能跨服务日志串出完整时间线
  - [ ] 人工在 troubleshooting.md 里加一条 "按 scope_id 聚合日志" 的例子
- 承诺：R4

### P3-6  "消息去哪了"查询端点
- Status: `[ ]`
- Scope: Business `/internal/messages/{id}/trace`
- 任务：
  - [ ] 根据 message_id 返回 `{lifecycle, claimed_by_scope, scope_meta, current_active_session}`
  - [ ] 调试 CLI：`novaic-cli msg trace <msg_id>`（可选）
- 验收：任一消息可以一键查到归属 scope + lifecycle
- 承诺：R4

---

## Phase 4 — Pending 超时告警（R5）

> **目标**：`msg.pending_for > 阈值` 成为一等事件。

### P4-1  Pending 检测 emitter
- Status: `[ ]`
- Scope: `novaic-agent-runtime/task_queue/workers/health_worker_sync.py`（重命名为 `recovery_worker_sync.py` 也可）
- 任务：
  - [ ] 扫 `lifecycle=pending AND created_at < now - threshold`
  - [ ] 每条 emit 事件：
    - metric `novaic_messages_orphaned_total{trigger_type=...}` +1
    - log `orphan_detected message_id=... age_seconds=...`（structured）
  - [ ] 阈值可配置（默认 30s warn / 5min crit）
- 验收：
  - [ ] 手工造一条"subscriber 挂掉导致 pending" → emitter 30s 内检测到
- 承诺：R5

### P4-2  Metric 端点
- Status: `[ ]`
- Scope: `novaic-agent-runtime/metrics.py` 或各服务现有 metric 端点
- 任务：
  - [ ] 新增 histogram `novaic_messages_pending_seconds`（定期采样 pending 队列 age 分布）
  - [ ] 新增 counter `novaic_messages_orphaned_total`
  - [ ] 新增 gauge `novaic_messages_pending_count`
- 验收：`curl /metrics` 看得到以上三个
- 承诺：R5

### P4-3  Orphan 可查视图 / CLI
- Status: `[ ]`
- Scope: Business `/internal/messages/orphaned`
- 任务：
  - [ ] 列出所有 `lifecycle=pending AND age > threshold` 的消息
  - [ ] CLI：`novaic-cli orphans list`
- 验收：运维可一键列出
- 承诺：R5

### P4-4  Alert 出口
- Status: `[ ]`
- Scope: 先用 log marker + SSE；后接正式 alert
- 任务：
  - [ ] `orphaned_count > N` 打 `ALERT` 级别日志（grep 友好）
  - [ ] 留 TODO：接入正式告警（pagerduty/飞书/Slack/...）
- 验收：阈值触发能被现有监控日志扫到
- 承诺：R5

### P4-5  Recovered re-dispatch（明确且独立）
- Status: `[ ]`
- Scope: `recovery_worker_sync.py`
- 任务：
  - [ ] 对 orphan 消息 re-dispatch 时 **必须** 用 `TriggerType.RECOVERED`
  - [ ] metric 标签 `trigger_type=recovered` 与主路径分开
  - [ ] 次数上限（例如 3 次），超过打 `ALERT` 不再重试
- 验收：主路径 metric 不与 recovery metric 混淆
- 承诺：R1 + R5

---

## Phase 5 — 状态机化（R8，长期）

> **目标**：废除"多字段拼状态"反模式。分实体逐步推进。

### P5-1  `Subagent` 状态机
- Status: `[ ]`
- Scope: `novaic-business/business/internal/subagent_utils.py` + Entangled schema
- 任务：
  - [ ] 定义 `SubagentStatus`（现已有枚举，补 transition 表）
  - [ ] 所有 `store.update("subagents", ..., {"status": ...})` 改走 `subagent_state.transition(...)`
  - [ ] `wake_at / need_rest / summary_lock` 归为 metadata，不再独立判断生命周期
- 验收：`rg 'subagents.*SET.*status'` 无散落 SQL；所有转移走单一入口
- 承诺：R8

### P5-2  `Scope` 状态机（Cortex 内）
- Status: `[ ]`
- Scope: `novaic-cortex/novaic_cortex/scope.py`
- 任务：
  - [ ] `ScopeState`：`creating / active / compacting / archiving / archived / failed`
  - [ ] meta.json `state` 字段
  - [ ] 所有 state 变更走唯一入口
- 验收：同上
- 承诺：R8（与 Cortex invariants 协同）

### P5-3  转移日志
- Status: `[ ]`
- Scope: 每个实体
- 任务：
  - [ ] 新增 `*_state_transitions` 表（或作为 entity event log）
  - [ ] 每次 transition 写一行 `(entity_id, from, to, reason, actor, timestamp)`
- 验收：事后能回放某实体的完整生命周期
- 承诺：R8

### P5-4  废弃旧字段
- Status: `[ ]`
- 条件：Phase 3-5 的 lifecycle / status 稳定运行至少 1 个 release
- 任务：
  - [ ] 删 `chat_messages.processed / read / claimed_by / claimed_at / status`
  - [ ] Schema push 版本号 +1；迁移脚本
- 承诺：R4 + R8

---

## 观测与验收（全 Phase 贯穿）

这些不是单独 phase，而是每一步都要满足的基线：

| ID | Status | Item | 承诺 |
| --- | --- | --- | --- |
| OBS-1 | `[ ]` | 所有跨服务 HTTP 调用带 `X-Internal-Service` | R7 |
| OBS-2 | `[ ]` | 所有跨服务日志带 `scope_id` 绑定 | R4 |
| OBS-3 | `[ ]` | metric：`dispatch_total{trigger_type, result}`、`outbox_lag_seconds`、`messages_pending_count`、`messages_orphaned_total` 齐全 | R5 |
| OBS-4 | `[ ]` | runbook：`docs/runbooks/troubleshooting.md` 加 "消息没回复的排查 SOP"（按 scope_id 聚合 / 查 orphan 视图 / 查 outbox lag） | R4 + R5 |
| OBS-5 | `[ ]` | `docs/architecture/message-wake-principles.md` §五"对照表"每条都有 metric / log 证据指向 | 所有 |

---

## 里程碑 / Release gating

| 里程碑 | 对应 Phase | 完成标志 |
| --- | --- | --- |
| **M1 — 合约对齐**（基础建设） | Phase 1 | 所有 dispatch 经 Assembler；internal auth 统一；resolver 可用 |
| **M2 — 主路径切换** | Phase 2 | 消息写入驱动 dispatch；HealthWorker 不再做 dispatch |
| **M3 — 可观测性** | Phase 3 + 4 | scope_id 贯穿日志；orphan 告警生效；"消息去哪了" 一键查 |
| **M4 — 状态机化** | Phase 5 | 所有一等实体单入口状态转移；旧字段清理 |

**Gating**：
- M1 未达成前，**任何**涉及 dispatch / 消息流的代码改动必须经过本文作者 review。
- M2 未达成前，**不允许**新增新的 wake trigger 类型。
- M3 未达成前，对用户声明"异步系统可观测"不成立；troubleshooting 仍需人肉串库。

---

## 附录 A — 关联文件与位置索引

### 现有代码（改造目标）
- `novaic-business/business/internal/subagent.py::_dispatch_trigger`（P2-4 删）
- `novaic-business/business/internal/subagent.py::subagent_send / spawn_subagent`（P1-6、P2-4）
- `novaic-agent-runtime/task_queue/workers/health_worker_sync.py::_scan_unhandled_messages`（P1-7、P2-5）
- `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py::dispatch`（P1-8）
- `novaic-agent-runtime/queue_service/routes.py::dispatch`（合约保留，R2 使其变成只面向 Assembler）
- `novaic-agent-runtime/queue_service/session_repo.py`（P0-3 已完成 dedupe，状态机化见 P5）
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py::handle_session_init`（P3-1 加 inputs）
- `novaic-cortex/novaic_cortex/*`（P3-1 scope meta；P5-2 scope 状态机）

### 新建代码
- `novaic-common/novaic_common/wake/{assembler,trigger_types,errors}.py`（Phase 1）
- `novaic-common/novaic_common/agents/ownership.py`（P1-3）
- `novaic-common/novaic_common/logging/context.py`（P3-5）
- `novaic-business/business/subscribers/dispatch_subscriber.py`（P2-3）
- `novaic-entangled/*/message_outbox.*`（P2-2，方案 B）
- `novaic-agent-runtime/task_queue/workers/recovery_worker_sync.py`（原 HealthWorker 改名，P4-1）

### 文档
- `docs/architecture/message-wake-principles.md`（架构承诺，SSOT）
- `docs/roadmap/message-wake-refactor.md`（本页）
- `docs/roadmap/technical-debt.md`（索引）
- `docs/runbooks/troubleshooting.md`（OBS-4：SOP 追加）

---

## 附录 B — 触发点迁移矩阵（P1-6/7/8 对照表）

| 现有入口 | 当前做法 | 迁移后 |
| --- | --- | --- |
| `Business.subagent_send` | `_dispatch_trigger(trigger_type="subagent_send", subagent_id=sub_id)` | Phase 1：`Assembler.assemble(TriggerType.SUBAGENT_SEND, agent_id, subagent_id=...)` Phase 2：**删除**，由 subscriber 接管 |
| `Business.spawn_subagent` | `_dispatch_trigger(trigger_type="spawn_subagent", ..., metadata={initial_context})` | 同上（initial_context 保留进 Assembler metadata） |
| `HealthWorker._scan_unhandled_messages` | 直调 `/dispatch` with `user_id=""` | Phase 1：`Assembler`（自动解 user_id） Phase 2：**整段删除** |
| `SchedulerWorker` 定时扫 `due-wake` | 直调 `/dispatch` with `TriggerType.SCHEDULED_WAKE` | Phase 1：改走 `Assembler` |
| **新**：USER_MESSAGE 写入 | 无人主动 dispatch，靠兜底 | Phase 2：outbox subscriber → `Assembler`（`TriggerType.USER_MESSAGE`） |

---

## 附录 C — 审视时间线

- 2026-04-17：`hihi` 事件发生，Phase 0 诊断完成
- Phase 1 / M1 预计完成：__（待排期）__
- Phase 2 / M2 预计完成：__（待排期）__
- Phase 3 + 4 / M3 预计完成：__（待排期）__
- Phase 5 / M4：长期

每 Phase 完成后在 `HANDOVER.md` 追加一条"最后更新"。
