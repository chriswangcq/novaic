# Message → Wake 重构实施清单

> 基于 [architecture/message-wake-principles.md](../architecture/message-wake-principles.md) 的 8 条架构承诺 (R1–R8) 下沉成**可执行、可勾选、可追溯**的六阶段清单。
>
> **更细粒度的 PR 级工单（每 PR 一文件，含完整 checklist）→ [tickets/](tickets/README.md)**
> 本页仍是阶段/条目视角的 SSOT；tickets 目录是工程师每天做事用的工单。
>
> 状态标记：`[ ]` 未做、`[x]` 已完成、`[~]` 进行中、`[!]` 落地时策略改变 / 并入别的 PR / 明确判定无需做。
>
> 每项携带 ID（方便 PR/commit 引用）、承诺来源、严重度、范围、前置、验收标准、回归测试、可观测性要求、回滚方案。
>
> **Release gating rule**：
>
> - Phase 1 未清零前不允许对 `Business._dispatch_trigger` / `HealthWorker._scan_unhandled_messages` 做任何业务增量；  
> - Phase 2 未清零前不允许新增消息类型（新 trigger_type）；  
> - Phase 3 未清零前不允许声称系统具备"端到端异步可观测性"。
>
> **2026-04-21 SSOT note**：本页 Phase 条目状态已与 [tickets/README.md](tickets/README.md)
> 对齐 —— PR-01..PR-35 全部 `[x]`。少数 `[!]` 表示"落地时策略变了"或"并入其他 PR"，
> 在对应条目里都有注释指向具体 PR / ADR。真正还未闭环的 `[ ]` 只剩正式告警出口（P4-4）。

---

## 前置 / 工程卫生


| ID   | Status | Item                                                                                                             | 来源  |
| ---- | ------ | ---------------------------------------------------------------------------------------------------------------- | --- |
| M0-1 | `[x]`  | `novaic_common.wake` 包骨架（`__init__.py`、`assembler.py`、`trigger_types.py`、`errors.py`） — PR-01                    | R2  |
| M0-2 | `[x]`  | `novaic_common.agents.ownership` 包骨架 — PR-02                                                                     | R3  |
| M0-3 | `[x]`  | `docs/architecture/message-wake-principles.md` 接入 `docs/README.md` 架构表                                           | —   |
| M0-4 | `[x]`  | `roadmap/technical-debt.md` 引用本页并标记"进行中"                                                                         | —   |
| M0-5 | `[x]`  | CI lint 规则：禁止业务代码直接 `httpx.post(...".../api/queue/dispatch"...)` 字符串（allowlist：`common/wake/assembler.py`、tests） | R2  |
| M0-6 | `[x]`  | CI lint 规则：禁止业务代码直接 `httpx.Client()`（allowlist：`common/http/clients.py`、测试工具）                                    | R7  |


---

## Phase 1 — 合约对齐前置（R7 + R3 + R2）

> **目标**：在不动任何主路径的情况下，先把"字段 / 身份 / 入口"三层基础补齐，为 Phase 2 的路径切换做准备。
> **DoD**：全系统所有 dispatch 都经 Assembler；所有 internal 调用都带身份头；Cortex 的 user_id 需求有唯一 resolver。

### P1-1  统一 internal client（带身份头）

- Status: `[x]` (PR-05)
- Severity: High（401 盲区）
- Scope: `novaic_common/http/clients.py`
- 前置：无
- 任务：
  - `internal_client(service_name, base_url, ...)` 增加 `service_name` 必填参数
  - 默认注入 `X-Internal-Key`（环境变量，已存在）+ `X-Internal-Service: <service_name>`
  - 为老调用点迁移（逐个 grep `internal_client(`）
- 验收：`rg "internal_client\(" novaic-*/` 所有命中都带 `service_name`
- 可观测性：Queue Service / Cortex 访问日志打印 `caller=<service_name>`
- 回滚：保留老函数签名做重载过渡，灰度回退只需改导入
- 承诺：R7

### P1-2  目标服务消费 `X-Internal-Service`

- Status: `[x]`
- Scope: `novaic-cortex/novaic_cortex/auth.py`（或等价位置）、`queue_service/auth.py`、`novaic-business/business/*/auth.py`
- 任务：
  - auth 中间件读取 `X-Internal-Service`，未提供 → 记 WARN（灰度期不拒）
  - 访问日志字段 `caller` 必带
- 验收：手工用三种身份（cortex/runtime/business）调 Queue Service，日志里 caller 正确
- 承诺：R7

### P1-3  `AgentOwnershipResolver` 实现

- Status: `[x]`
- Scope: `novaic_common/agents/ownership.py` + `novaic-business/business/internal/agents.py`
- 任务：
  - Business 新增 `GET /internal/agents/{agent_id}/owner` → `{user_id}` / 404
  - `AgentOwnershipResolver`（进程内 TTL 缓存，默认 5 min）
  - `resolve(agent_id) -> str | raise AgentNotOwnedError`
- 验收：单测覆盖「命中 / 不存在 / 缓存命中 / TTL 过期」
- 回归：mock Business 404 → resolver raise 明确错误
- 承诺：R3

### P1-4  `TriggerType` 权威枚举

- Status: `[x]`
- Scope: `novaic_common/wake/trigger_types.py`
- 任务：
  - `TriggerType(Enum)`：`USER_MESSAGE / SUBAGENT_SEND / SPAWN_SUBAGENT / SCHEDULED_WAKE / SYSTEM_WAKE / RECOVERED`
  - 迁移现有字符串常量到枚举
  - `wake_triggers` 默认值 `[{"type": "user_response"}]` **改为** `"user_message"`（schema 默认 + 迁移 SQL）
- 验收：`rg 'user_response'` 无剩余业务代码命中
- 迁移：`UPDATE subagents SET wake_triggers = REPLACE(wake_triggers, 'user_response', 'user_message')`（Entangled schema push 版本号 +1）
- 承诺：R2

### P1-5  `DispatchAssembler` 实现

- Status: `[x]`
- Scope: `novaic_common/wake/assembler.py`
- 任务：
  - `DispatchRequest` dataclass（含所有 Queue Service 必填）
  - `DispatchAssembler.assemble(trigger_source, agent_id, *, subagent_id=None, message_ids=None, metadata=None) -> DispatchRequest`
    - 调 `AgentOwnershipResolver` 解析 user_id
    - 默认 `subagent_id = f"main-{agent_id[:8]}"`
    - 校验 trigger_source 是 `TriggerType` 枚举
    - metadata 里附 `message_ids`（供 R4 的 scope.inputs 登记）
  - `DispatchAssembler.dispatch(req) -> DispatchResult`（调 Queue Service `/dispatch`，走 P1-1 的 `internal_client`）
  - 失败抛明确 `DispatchError(kind="no_owner"|"queue_400"|"queue_5xx"|"network")`，绝不吞
- 验收：
  - 单测：mock resolver + mock HTTP，各路径覆盖
  - 合约测试：assemble 输出必定通过 Queue Service `DispatchRequest.validate()`
- 承诺：R2 + R3

### P1-6  老 `_dispatch_trigger` 迁到 Assembler

- Status: `[x]`
- Scope: `novaic_business`, `novaic_health_worker`, `novaic_scheduler`
- 任务：
  - 把原有的直接 `httpx.post('/dispatch')` 代码删掉
  - 注入并调用 `DispatchAssembler.assemble_and_dispatch`
  - [!] **暂时保留**函数名作为薄壳 — 规划期的分步兜底；PR-18 已直接删除 `_dispatch_trigger`，不再需要薄壳过渡
- 验收：subagent_send 端到端依然工作（单测 + 手工触发）
- 承诺：R2

### P1-7  `HealthWorker._scan_unhandled_messages` 迁到 Assembler

- Status: `[x]`
- Scope: `novaic-agent-runtime/task_queue/workers/health_worker_sync.py`
- 任务：
  - 用 `DispatchAssembler` 替换手工拼请求（PR-12）
  - 不再硬编码 `user_id=""`（resolver 解析）（PR-12）
  - Phase 2 会整个删掉，本步骤只是让它先不 400（PR-19 已删除 `_scan_unhandled_messages`，HealthWorker 收敛为 recovery-only）
- 验收：health log 里 `Fallback dispatch failed` 消失（对现有未处理消息）
- 承诺：R2 + R3

### P1-8  `Scheduler worker` 迁到 Assembler

- Status: `[x]`
- Scope: `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py`
- 任务：
  - 将旧的 `/dispatch` 定时唤醒调用迁为 `assembler.assemble_and_dispatch(TriggerType.SCHEDULED_WAKE, ...)`
- 验收：`rg 'httpx\..*/dispatch' novaic-agent-runtime/` 应当不再包含 scheduler_worker
- 承诺：R2

---

## Phase 2 — 主路径切换（R1 + R6）

> **目标**：让 Entangled 消息写入驱动 dispatch；HealthWorker 从"唯一主路径"降级为"recovery only"。
> **DoD**：没有任何业务代码手写 dispatch；dispatch 仅由 changefeed subscriber 发起。

### P2-1  选型 changefeed 载体

- Status: `[x]` (方案 B：outbox + subscriber)
- Scope: `novaic-entangled/` + `novaic-business/` 决策会议
- 任务：
  - 在三种方案中二选一 → 采纳 **方案 B**（outbox 表 + Business poller）
  - 决策记录写入 `docs/architecture/message-wake-principles.md` 及 `tickets/PR-14-entangled-message-outbox.md`
- 验收：决策文档落地
- 承诺：R6

### P2-2  实现 changefeed / outbox

- Status: `[x]`
- Scope: `Entangled/packages/server-python/entangled/sql/entity_store.py` + `novaic-business/business/schema_push.py`
- 方案 B 任务：
  - Entangled schema 新增 `message_outbox` 表 `(id, message_id, agent_id, type, created_at, delivered_at, attempts, last_error, permanent_failure)`（PR-14）
  - 每次写 `chat_messages` 在同事务内插入 outbox 条目（PR-14 co-transactional insert）
  - Business 新增 poller 服务：`dispatch_subscriber` 读 `delivered_at IS NULL` → 走 Assembler → mark delivered / 增 attempts（PR-15 骨架 + PR-16 完整 poll/dedupe/retry）
  - outbox 保留 7 天（运维可清理）— `scripts/outbox-compact.sh` + `docs/runbooks/outbox-maintenance.md`
- 验收：
  - 并发写 100 条消息，100 条 outbox 事件都被消费；无丢失无重复（subscriber 幂等由 `idempotency_key=msg:{id}` + Queue Service dedupe 保证；PR-16 单测覆盖）
  - subscriber crash 后重启可继续（PR-16 claim TTL + retry backoff 测试）
- 可观测性：
  - metric `outbox_lag_seconds` — 落地于 PR-32（subscriber gauge）
  - metric `outbox_attempts_total{result=ok|retry|failed}` — 以 `subscriber_delivered_total` / `subscriber_retry_total` / `subscriber_failed_total` 三元对称形式落地于 PR-32
- 承诺：R6

### P2-3  Dispatch subscriber（Business 侧或独立进程）

- Status: `[x]` (PR-15 骨架 → PR-16 完整实现 → PR-17 canary 上线；bake gate 2026-04-19 撤销后直接转全量)
- Scope: `novaic-business/business/subscribers/dispatch_subscriber.py`（新建）
- 任务：
  - 订阅 outbox / changefeed（PR-16: `/v1/outbox/claim` 原子出队）
  - 过滤：只消费 `wake-triggering` 消息类型（USER_MESSAGE / SUBAGENT_SEND / SPAWN_SUBAGENT）→ 写入侧已由 `SqlEntityDef.outbox_trigger_types` 过滤
  - 幂等：同一 message_id 已 dispatch 过 → 跳过（`idempotency_key=msg:{id}`，由 Queue Service 去重）
  - 调 `DispatchAssembler`
  - 成功 → mark outbox delivered；失败 → attempts+1，retry backoff（指数退避）
- 验收：
  - 发一条 USER_MESSAGE → Queue Service 收到且只收到一次 dispatch（PR-17 canary 已转全量，bake gate 2026-04-19 撤销）
  - Subscriber 重启 → 未消费事件会被重放但最终 exactly-once（TTL 过期 + `idempotency_key=msg:{id}` 去重，PR-16 单测 + 线上观察）
- 承诺：R1 + R6

### P2-4  删除"消息写入处手写 dispatch"

- Status: `[x]` (PR-18)
- Scope: `novaic-business/business/internal/subagent.py`
- 任务：
  - 删 `_dispatch_trigger` 函数本体
  - `subagent_send` / `spawn_subagent` 写完消息后**不再**调它（由 subscriber 接管）
  - Grep 确认 `_dispatch_trigger` 无残留 caller
- 验收：subagent_send 端到端仍工作（由 subscriber 接管后）
- 回滚：P2-3 failing → 暂时恢复 P1-6 的 Assembler 直调，再查 subscriber
- 承诺：R1 + R6

### P2-5  HealthWorker 降级为 recovery

- Status: `[x]` (PR-19)
- Scope: `novaic-agent-runtime/task_queue/workers/health_worker_sync.py`
- 任务：
  - 删除 `_scan_unhandled_messages` 的"re-dispatch 消息"职责
  - 只保留 `/api/queue/recover/all`（孤儿 task/saga 回收）
  - P3 才加"pending 超时 emitter"职责（在此处分离；PR-26 增补）
- 验收：HealthWorker 日志里不再出现 `Fallback dispatch`；400/401 全绝
- 承诺：R1

### P2-6  端到端冒烟

- Status: `[x]` (PR-17 canary → 转全量后持续绿；`hihi` 回归闭环)
- 步骤：
  - 清库 → 发 `hihi` → 观察：
    - Entangled `chat_messages` 写入
    - outbox 事件产生（方案 B）
    - subscriber 消费日志
    - Queue Service 收到 1 次 dispatch（200 OK）
    - Saga 启动 / Cortex scope 建立
    - agent 回复
  - 压测：1 秒内 10 条消息 → 同一 agent → 只启 1 个 active session，其余 buffered（由 P0-3 + subscriber 幂等覆盖）
- 承诺：R1

---

## Phase 3 — Scope trace + Message lifecycle（R4）

> **目标**：让 "这条消息去哪了 / 这个 loop 卡哪了" 变成一次查询。

### P3-1  Scope metadata 登记 inputs

- Status: `[x]` (PR-20)
- Scope: `novaic-cortex/novaic_cortex/scope.py` + `agent_runtime/handlers/runtime_handlers.py::handle_session_init`
- 任务：
  - Scope `meta.json` 增加字段：`input_message_ids: list[str]`
  - `session.init` payload 必带 `message_ids`（Assembler 已在 P1-5 metadata 里附）
  - Cortex API 新增 `POST /v1/scope/{id}/append_input { "message_ids": [...] }`（session 进行中继续 buffer 的消息追加登记）
- 验收：
  - 任一 scope 能通过 `meta.json` 查到它消费了哪些消息
  - N 条消息 buffer 进同一 scope → inputs 长度 = N
- 承诺：R4

### P3-2  Message lifecycle 状态字段

- Status: `[x]` (PR-21)
- Scope: Entangled schema + `novaic-entangled` entity handlers
- 任务：
  - 新增状态枚举字段 `lifecycle: pending | claimed | consumed | orphaned | deduped`
  - [!] 保留旧字段（`read / processed / claimed_by / claimed_at / status`）一个 release，观察期后删 — 策略改为直接清理：PR-30 一次性删除，配合"历史数据可清"的上线决策（2026-04-21），不再走观察期
  - `claimed_by` 语义改为 `claimed_by_scope`（存 scope_id）
  - 状态转移走唯一入口 `message_state.transition(msg_id, to, scope_id=...)`
- 验收：
  - 发消息 → pending
  - subscriber dispatch 成功 → claimed(scope_id=X)
  - scope_end 成功 → consumed
  - 超时未 claim → orphaned（Phase 4 告警）
- 承诺：R4 + R8（message 实体状态机化）

### P3-3  Subscriber 在 dispatch 成功时 transition → claimed

- Status: `[x]` (PR-22)
- Scope: `novaic-business/business/subscribers/dispatch_subscriber.py`
- 任务：
  - Queue Service `/dispatch` 返回体带 `scope_id`（已有）
  - Subscriber 拿到 `scope_id` 后 transition 消息到 `claimed(by_scope=scope_id)`
- 验收：成功 dispatch 的消息 100% 落到 claimed
- 承诺：R4

### P3-4  scope_end 触发 consumed

- Status: `[x]` (PR-23)
- Scope: Cortex `/v1/scope/{id}/end` / session.ended handler
- 任务：
  - scope_end 成功时（归档完成）→ 对 `scope.inputs` 里所有 message_id transition 到 `consumed`
  - scope_end 失败不 transition（保持 claimed，待重试或 orphan 超时）
- 验收：正常完成的 session 其 inputs 100% 变 consumed
- 承诺：R4

### P3-5  跨服务 `scope_id` 日志绑定

- Status: `[x]` (PR-24)
- Scope: `novaic_common/logging/context.py`（新建）+ 全 handler 入口
- 任务：
  - `LogContext` contextvar；handler 入口 `bind(scope_id=..., agent_id=..., user_id=...)`
  - 默认 log formatter 输出 `scope_id=<id>` 前缀
  - Business / Queue / Saga worker / Task worker / Cortex 全部接入（`install_service_logging`）
- 验收：
  - 任取一个 scope_id，用 `rg "scope_id=<id>"` 能跨服务日志串出完整时间线
  - 人工在 troubleshooting.md 里加一条 "按 scope_id 聚合日志" 的例子
- 承诺：R4

### P3-6  "消息去哪了"查询端点

- Status: `[x]` (PR-25)
- Scope: Business `/internal/messages/{id}/trace`
- 任务：
  - 根据 message_id 返回 `{lifecycle, claimed_by_scope, scope_meta, current_active_session}`
  - [!] 调试 CLI：`novaic-cli msg trace <msg_id>`（规划期标 "可选"；endpoint 已覆盖，CLI 未建亦未计划）
- 验收：任一消息可以一键查到归属 scope + lifecycle
- 承诺：R4

---

## Phase 4 — Pending 超时告警（R5）

> **目标**：`msg.pending_for > 阈值` 成为一等事件。

### P4-1  Pending 检测 emitter

- Status: `[x]` (PR-26 + TD-5)
- Scope: `novaic-agent-runtime/task_queue/workers/health_worker.py`（未改名，保留为 HealthWorker；`_scan_and_recover_orphans`）
- 任务：
  - 扫 `lifecycle=pending AND created_at < now - threshold`
  - 每条 emit 事件：
    - metric `orphans_total{severity=warn|crit|permanent}` +1（PR-26 scanner + TD-5 hook into PR-32 registry；实际采用 `{severity}` 而非 `{trigger_type}` 以匹配 HealthWorker 的三档分级）
    - log `orphan_detected message_id=... age_seconds=...`（structured）
  - 阈值可配置（env 化，三档 warn/crit/permanent）
- 验收：
  - 手工造一条"subscriber 挂掉导致 pending" → emitter 阈值内检测到（集成测试 `tests/test_health_orphan_scan.py`）
- 承诺：R5

### P4-2  Metric 端点

- Status: `[x]` (PR-26 counter + PR-32 registry；两项 `[!]` 见下)
- Scope: `novaic-agent-runtime/metrics.py` 或各服务现有 metric 端点
- 任务：
  - [!] histogram `novaic_messages_pending_seconds` — PR-26 落地时判断 `outbox_lag_seconds` gauge 已覆盖"整体感觉慢"，histogram 推迟到真有 percentile 需求再加（见 `tickets/PR-26-orphan-emitter-metrics.md` 可观测性 checklist 注记）
  - counter `orphans_total{severity}` 实现见 PR-26 emitter + TD-5 hook（metric 名从 planning 期的 `novaic_messages_orphaned_total` 改为 `orphans_total`，label 从 `trigger_type` 改为 `severity`，以贴近实际的 warn/crit/permanent 三档分级）
  - [!] gauge `novaic_messages_pending_count` — 落地时由 `outbox_backlog_count` gauge + `orphans_total{severity}` counter 组合覆盖"多少条在排队 / 其中多少已超时"，不再单独新增
- 验收：`curl /metrics` 看得到 `orphans_total`、`outbox_lag_seconds`、`outbox_backlog_count`
- 承诺：R5

### P4-3  Orphan 可查视图 / CLI

- Status: `[x]` (PR-26 endpoint；CLI 条目落为 `[!]`)
- Scope: Business `/internal/messages/orphaned` + Entangled `/v1/orphans`
- 任务：
  - 列出所有 `lifecycle=pending AND age > threshold` 的消息（Business `GET /internal/messages/orphaned`，代理到 Entangled `/v1/orphans`）
  - [!] CLI：`novaic-cli orphans list` — endpoint + curl 已满足运维需求，CLI 未建亦未排期
- 验收：运维可一键列出
- 承诺：R5

### P4-4  Alert 出口

- Status: `[~]` (log marker 已落；正式告警通道待接)
- Scope: 先用 log marker + SSE；后接正式 alert
- 任务：
  - `orphaned_count > N` 打 `ALERT` 级别日志（PR-26：ERROR 级 `ORPHAN` / `PERMANENT_ORPHAN` 前缀 + WARN 级 `orphan_warn`，grep 友好）
  - TODO：接入正式告警通道（pagerduty / 飞书 / Slack …）— 当前依赖人工盯 log / metrics；系统上正式告警时再做
- 验收：阈值触发能被现有监控日志扫到
- 承诺：R5

### P4-5  Recovered re-dispatch（明确且独立）

- Status: `[x]` (PR-27)
- Scope: `novaic-agent-runtime/task_queue/workers/health_worker.py::_scan_and_recover_orphans`
- 任务：
  - 对 orphan 消息 re-dispatch 时 **必须** 用 `TriggerType.RECOVERED`
  - metric 标签 `trigger_type=recovered` 与主路径分开（`dispatch_total{trigger_type=recovered,...}`）
  - 次数上限（`permanent_failure` 标记后不再重试，`PERMANENT_ORPHAN` 告警）
- 验收：主路径 metric 不与 recovery metric 混淆
- 承诺：R1 + R5

---

## Phase 5 — 状态机化（R8，长期）

> **目标**：废除"多字段拼状态"反模式。分实体逐步推进。

### P5-1  `Subagent` 状态机

- Status: `[x]` (PR-28 + PR-31b)
- Scope: `novaic-business/business/internal/subagent_state.py` + Entangled schema
- 任务：
  - 定义 `SubagentStatus` transition 表（AWAKE / SLEEPING / COMPLETED / FAILED / CANCELLED）
  - 所有 `store.update("subagents", ..., {"status": ...})` 改走 `subagent_state.transition(...)`
  - `wake_at / need_rest / summary_lock` 归为 metadata，不再独立判断生命周期
- 验收：`rg 'subagents.*SET.*status'` 无散落 SQL；所有转移走单一入口
- 承诺：R8

### P5-2  `Scope` 状态机（Cortex 内）

- Status: `[x]` (PR-29)
- Scope: `novaic-cortex/novaic_cortex/scope_state.py`
- 任务：
  - `ScopeState`：`executing / compacting / archiving / archived / failed`（落地时合并 creating/active → executing，transition 表由 `scope_state.py` 权威定义）
  - meta.json `phase` 字段（meta 缺失直接 raise `InvalidScopeTransition`，fail-loud）
  - 所有 state 变更走唯一入口 `scope_state.transition(...)`
- 验收：同上
- 承诺：R8（与 Cortex invariants 协同）

### P5-3  转移日志

- Status: `[x]` (PR-31)
- Scope: 每个实体
- 任务：
  - 新增 `*_state_transitions` 表（entity event log 形式，见 PR-31）
  - 每次 transition 写一行 `(entity_id, from, to, reason, actor, timestamp)`
- 验收：事后能回放某实体的完整生命周期
- 承诺：R8

### P5-4  废弃旧字段

- Status: `[x]` (PR-30 + 2026-04-21 "历史数据清零" 决策)
- 条件：Phase 3-5 的 lifecycle / status 稳定运行至少 1 个 release
- 任务：
  - 删 `chat_messages.processed / claimed_by / claimed_at / status`（`read` 按 PR-30 决策保留供 UI 未读标记）
  - Schema push 版本号 +1；迁移脚本随 "历史数据全部删除" 决策废弃，直接以规范 `CREATE TABLE` 为准
- 承诺：R4 + R8

---

## Phase 6 — Wake continuity（R9，2026-04-21 事件后新增）

> **目标**：`sleeping → awake` 转换点不再有"短时记忆真空"。agent 醒来应能看到（a）自己睡前的交接；（b）上一次 scope 的尾部工具轨迹；（c）最近的 IM 对话。
>
> **触发**：2026-04-21 排查两个现象：
>
> 1. agent 每 ~5 分钟自动苏醒一次 — HealthWorker 把 `AGENT_REPLY pending` 误当 orphan RECOVERED（单独由 Phase 6 hotfix P6-1 / PR-41 解决）
> 2. 苏醒后 `context.jsonl` 只有 system prompt + recall summary，handoff_notes / historical_summary / 前序 scope step 全丢
>
> **DoD**：
>
> - `orphans_total{severity=crit}` 无周期性非零（在无真实卡消息时）
> - 新 scope `context.jsonl` 在非 spawn wake 路径上必含 `WAKE_CONTINUITY` 或 `PREV_SCOPE_TAIL` 或 `WAKE_IM_REPLAY` 至少一种
> - `wake_continuity_injected_total` / `prev_scope_tail_injected_total` / `wake_im_replay_total` 可观测

### P6-1  Hotfix：`AGENT_REPLY` 等非 trigger 消息不再进入 orphan 候选（止血）

- Status: `[x]` (PR-41, 2026-04-21 实施完成)
- Severity: High（自激循环，生产实锤）
- Scope: `Entangled/.../entity_store.py::append`（写入侧"出生即 consumed"）+ `Entangled/.../app/orphans.py::query_orphans`（读取侧按 type 过滤）+ `scripts/gateway/migrate_pr41_agent_reply_orphans.sh` + `scripts/ci/lint_outbox_trigger_sync.sh`
- 已完成：
  - `append` 对 `type NOT IN outbox_trigger_types` 且 caller 未显式传 `lifecycle` 的消息，INSERT 前把 `lifecycle='consumed' + lifecycle_updated_at=now_ms` 写进 row（不走 state machine transition；CHECK 约束允许 consumed 作为初始值）
  - `query_orphans` SQL 加 `AND m.type IN (?,?,?)`，模块常量 `ORPHAN_ELIGIBLE_TYPES`
  - 迁移脚本（allowlisted）：备份→计数→breakdown→事务 UPDATE→校验
  - CI 同步 check：drift 即 fail，接入 `.github/workflows/lint.yml`
  - 单测 8 cases（Entangled 侧），全量回归 114+74+101 passed
- 验收（部署后）：`queue-service.log` 无周期性 `caller=runtime-recovery`；`/orphaned?min_age_sec=30` count=0
- 承诺：R4 + R8（lifecycle × type 语义矩阵闭合）

### P6-2  Wake continuity 文字层 — handoff_notes / historical_summary 注入

- Status: `[x]` (PR-42, 2026-04-21 实施完成)
- Scope: `task_queue/sagas/subagent_wake.py::_build_session_init_payload` + `task_queue/handlers/runtime_handlers.py::handle_session_init`
- 已完成：
  - saga payload 透传 `handoff_notes` / `wake_reason`
  - `handle_session_init` 新增 `_build_wake_continuity_messages` / `_fetch_historical_summary` / `_build_continuity_block_for_wake` / `_continuity_kind_label` / `_cap_continuity_text`，对非 `spawn_subagent` 的 wake，从 `business_client.entity_get("subagents", ...)` 拉 `historical_summary`，拼 `<HANDOFF_NOTES>` / `<HISTORICAL_SUMMARY>` system message 注入 `initial_context`（顺序：SYSTEM_PROMPT → HANDOFF → HISTORICAL → recall）
  - 上限保护：`WAKE_CONTINUITY_MAX_BYTES=8KB` + UTF-8 字节前缀裁剪 + `[truncated]` 标记 + `wake_continuity_truncated_total` metric
  - `WAKE_CONTINUITY_ENABLED_TRIGGERS` positive-list：`spawn_subagent` 永远不注入（防父 agent handoff 泄漏到子）；未知 trigger fail-closed
  - Business 读失败软降级（仍注入 handoff，不 fail saga）
  - Metric `wake_continuity_injected_total{kind, trigger_type}` 每次 wake 一次计数（含 `kind=none`）
  - 单测 29 cases（`tests/test_wake_continuity_injection.py`），全量回归 101 passed
- 验收（部署后）：`wake_continuity_injected_total{kind=handoff|historical|both|none}` 非空；端到端 `rest(handoff_notes=...)` → wake → 新 scope context 含 HANDOFF_NOTES 段
- 承诺：**R9（新增）— Wake continuity 文字层**

### P6-3  Wake continuity 状态层 — Scope 续链 previous_scope_id

- Status: `[ ]` (PR-43)
- Scope: `common/wake/assembler.py`（resolve last_scope_id）+ `queue_service/session_repo.py`（透传）+ `task_queue/sagas/subagent_rest.py`（写 last_scope_id）+ `novaic-cortex/context_stack/engine.py`（assembly 读尾部）+ Entangled schema（`subagents.last_scope_id`）
- 任务：
  - Entangled schema: `subagents.last_scope_id` / `last_scope_archived_at`
  - `subagent_rest` saga: `cortex_scope_end` 成功后写 `last_scope_id`
  - Assembler: 对 "续接类 trigger" resolve subagent.last_scope_id → metadata
  - Cortex `create_scope` 接受 `previous_scope_id`，写入 meta.json
  - Cortex assembly: 新增 `read_scope_tail(max_steps, max_tokens)`；当前 scope 组装完后，若 budget 剩余 > 阈值 → 前置注入 PREV_SCOPE_TAIL
  - env 可配：`PREV_SCOPE_MAX_STEPS=20`, `PREV_SCOPE_MAX_TOKENS=8000`, `PREV_SCOPE_MIN_BUDGET=4000`, `WAKE_CONTINUITY_PREV_SCOPE=1`
- 验收：新 scope `meta.previous_scope_id` 链接到上一次 archived root；首轮 think 的 LLM input 含 `<PREV_SCOPE_TAIL scope=X from=TS>` wrapper
- 承诺：**R9 — 状态层**

### P6-4  Wake continuity IM 流层 — 首轮 chat_messages 回放

- Status: `[x]` (PR-44, 2026-04-21 完成)
- Scope: `task_queue/handlers/runtime_handlers.py::handle_session_init`（在 step 6 的 `update_session_meta` 里一次性写 `wake_replay_pending=bool(eligible)`）+ `task_queue/handlers/context_handlers.py::handle_context_read`（首次消费 flag 时 ephemeral 前置注入最近 K 条 chat_messages，**不落盘 context.jsonl**）
- 实施：
  - session.init 对 `trigger_type ∈ WAKE_IM_REPLAY_ENABLED_TRIGGERS` 且无 caller-provided `initial_context` 的 wake 置 `scope.meta.wake_replay_pending=True`；spawn / bootstrap 一律 `False`（literal bool，不是 None）
  - `handle_context_read` 在 `read_context()` 后、unread merge 前消费 flag：`isinstance(meta, dict)` + `meta.get("wake_replay_pending") is True` 双保险 → 按 type 分开拉 `USER_MESSAGE` + `AGENT_REPLY` 的 `read=1` 行 → 合并排序 → token 预算从新往旧累加 → 渲染为 `role=system` + `<CHAT_HISTORY>` 包装 + `_message_type="WAKE_IM_REPLAY"` → `context.extend(...)`（in-memory 只返回这一次）→ 清 flag
  - 去重：严格走"回放只读已读（read=1）、未读只拉未读（read=0）"的 SQL 等值隔离，LLM 不会看到同一条消息的两种表示（比 ticket 里预想的方案 B 更彻底）
  - 预算 / 时间上限：`WAKE_REPLAY_MESSAGE_COUNT=20`, `WAKE_REPLAY_MAX_AGE_SEC=86400`, `WAKE_REPLAY_MAX_TOKENS=6000`；全部 env 可调、带 `try/except ValueError` 容错
  - Kill switch：`WAKE_IM_REPLAY_ENABLED=0` 在函数入口短路，不读 meta、不调 Business、不改任何状态
  - 可观测：`wake_im_replay_total{result=injected|skipped_empty}` counter + `wake_im_replay_messages` / `wake_im_replay_tokens` histogram + `[wake_im_replay] scope=... agent=... messages=N tokens~T` log
  - 降级：`read_session_meta` 抛异常 / 返回非 dict / Business 500 / flag 清失败 全部软失败，unread 路径不受波及
  - 38 个新 case 覆盖（`tests/test_wake_im_replay.py`）+ 既有 48 个回归 case 全绿
- 验收（staging）：sleep 期间 N 条用户消息 → wake 首轮 LLM 看到 N 条 `WAKE_IM_REPLAY` 段；次轮不再重复（`?round=2` 预期 0 条）
- 承诺：**R9 — IM 流层**

### P6 组合预期

注入顺序（新 scope 首轮 context）：

```
1. SYSTEM_PROMPT                         (已有)
2. RECALL_MESSAGES                       (已有 — 跨 session 长期摘要)
3. WAKE_CONTINUITY                       (PR-42 — 文字)
4. PREV_SCOPE_TAIL                       (PR-43 — 工具轨迹)
5. WAKE_IM_REPLAY                        (PR-44 — 对话历史)
6. unread chat_messages (IM-rendered)    (已有 — PR-38)
```

三层互补；预算争抢时按优先级 compact（先驱逐 5 > 4 > 3 > 2）。**R9 完整形态写入** `docs/architecture/message-wake-principles.md` §承诺表。

### P6-5  Wake continuity producer→consumer 接线（PR-45）

- Status: `[~]` (PR-45 Wave 1A–E 已落，Wave 1F 线上验证进行中)
- 触发：2026-04-22 P6-2/P6-3/P6-4 上线后 user 报 "dfs scope 还是没加载"。静态排查发现 **producer 端从未写 `subagents.handoff_notes` / `historical_summary`** —— PR-42 的消费代码全部空跑。
- 已完成（Wave 1A–E）：
  - subagent_rest saga 的 `generate_simple_summary` 结果 → `handle_subagent_set_sleeping` → 持久化到 `subagents.historical_summary`（additive，None 不覆写）
  - DispatchSubscriber `_deliver_one_inner` 对 `USER_MESSAGE / SUBAGENT_SEND` trigger 从 `subagents` 读 continuity 并塞进 dispatch metadata（`setdefault`，不覆盖 caller 已提供的值）
  - HealthWorker `_maybe_recover` 对 `RECOVERED` trigger 同样注入
  - `handle_session_init` 消费 `handoff_notes` 后幂等清除（`WAKE_CONTINUITY_HANDOFF_CLEAR=1` 默认 ON）
  - Kill switches: `WAKE_CONTINUITY_TEXT=0` 一键关主路径；`WAKE_CONTINUITY_HANDOFF_CLEAR=0` 保留 handoff 不清
  - 单测 10 + 8 cases，全量回归绿
- Wave 1F 进行中：线上验证；2026-04-22 观察到 `subagents.handoff_notes` 仍为 NULL —— 因为 **LLM 根本没 rest** (P6-6) 也**根本没 `_exec_subagent_rest` executor** (P6-8)。
- 承诺：**R9 + R10（producer/consumer 合约）**

### P6-6  Turn Finalizer：chat_reply 之后强制关门（PR-48）

- Status: `[ ]` (PR-48)
- 触发：同 P6-5。根因 D — agent chat_reply 之后既不 subagent_rest 也不 skill_end，scope 永远 running，新消息走 buffered 分支，session.init 从不重新跑，**R9 全层注入路径集体空跑**。
- Scope: `task_queue/workers/saga_worker_sync.py`（think-loop 末尾加 `_should_finalize_turn` / `_finalize_turn` 兜底）
- 任务：
  - `_should_finalize_turn` 三路径：REPLY_NO_FOLLOWUP / NO_TOOL_LOOP / THINK_CAP
  - runtime 直接 enqueue `subagent_rest` saga（不走 LLM 工具层），actor=`runtime.turn_finalizer`
  - env: `MAX_THINK_ROUNDS_PER_DISPATCH=20`, `MAX_NO_TOOL_BEFORE_FINALIZE=3`
  - metric `turn_finalizer_total{reason}`
- 验收：`turn_finalizer_total{reason="REPLY_NO_FOLLOWUP"}` 近 1h ≥ 1；subagents 表 status='sleeping' 且 historical_summary 非空；紧随其后的 user_message 触发的新 scope session.init 命中 continuity 注入
- 承诺：**R8 + R9（scope 能关才能谈"上一次"）**

### P6-7  context.read 按 message_ids 精确装配（PR-46）

- Status: `[ ]` (PR-46)
- 触发：同 P6-5。根因 A — `handle_context_read` 用 `agent_id + read=0` 扫全部 unread，**不是**按 `payload.message_ids` 装配。结果：历史 11 条老 pending USER_MESSAGE 每轮被重注入；新消息在 race 窗口内反而漏掉。
- Scope: `task_queue/handlers/context_handlers.py::handle_context_read` + Business `/internal/entities/messages?ids=...` 透参 + 可能的 Entangled CRUD `ids=` 过滤补全 + CI lint（禁止 runtime 读 `read=0/1`）
- 任务：
  - runtime 改按 `payload.message_ids` 或 `scope.meta.input_message_ids` 取；都空 → fail-closed（不合并）
  - Business list endpoint 支持 `ids=` 参数
  - 保留写 `read=1`（UI 兼容），但不再读 `read`
  - CI lint 防倒退
- 验收：`event=context_read kind=by_ids count=N` 命中；新 scope context.jsonl 里 `role=user` 条数 = dispatch.message_ids 长度；日志不再出现 `kind=unread_scan`
- 承诺：**R2 + R4（消费端只信 dispatch 透传）**

### P6-8  `subagent_rest` tool executor（PR-49）

- Status: `[ ]` (PR-49，PR-45 Wave 1.5)
- 触发：同 P6-5。根因 C — LLM 可以调 `subagent_rest(handoff_notes=...)` 但 `TOOL_EXECUTORS` 里**根本没有**这个 key，LLM 手写便条直接掉地。
- Scope: `task_queue/handlers/tool_handlers.py`（加 `_exec_subagent_rest` + 注册）
- 任务：
  - executor 写 `subagents.handoff_notes` + 触发 `subagent_rest` saga
  - `actor="llm.tool.subagent_rest"` vs P6-6 的 `actor="runtime.turn_finalizer"` 分流
  - 幂等 key `rest:{scope_id}`
  - metric `subagent_rest_tool_invoked_total{source}` / `subagent_rest_handoff_persisted_total{result}`
- 验收：`<HANDOFF_NOTES>` 段在下次 wake 的 initial_context 里真的有内容（之前永远是空/null）
- 承诺：**R9 + R8（LLM 工具是 subagent 状态机的合法入口）**

### P6-9  老毒 USER_MESSAGE 清理 + recovery age cap（PR-47）

- Status: `[ ]` (PR-47)
- 触发：同 P6-5。根因 B — 11 条 04-17~04-21 的 USER_MESSAGE 卡 `lifecycle=pending`，HealthWorker 没年龄上限，每轮 recovery 再喂一次给 agent。
- Scope: `task_queue/workers/health_worker.py`（age cap 分支）+ `scripts/migrations/047_*.sql`（一次性迁移）+ `orphans_total{reason}` 维度补充
- 任务：
  - `MAX_RECOVERY_AGE_SEC=21600`（6h）：超限转 consumed(reason=age_cap)
  - 48h 迁移脚本清历史脏 pending
  - metric `orphans_total{severity,reason}`
- 验收：USER_MESSAGE pending 数从 11 → 0；`grep event=recovered_dispatch` 不再命中清理掉的 id
- 承诺：**R5 + R1（orphan 真正有界）**

### P6-10  IM 消息聚合 + CHAT_HISTORY 字节 cap（PR-50）

- Status: `[ ]` (PR-50)
- 触发：同 P6-5。根因 F — 用户连发 2 条消息触发 2 次 session.init；PR-44 CHAT_HISTORY 只有条数 cap 没字节 cap。
- Scope: `novaic-business/business/subscribers/dispatch_subscriber.py`（60s 合批）+ `task_queue/handlers/context_handlers.py`（字节 cap）
- 任务：
  - DispatchSubscriber 对 `USER_MESSAGE / SUBAGENT_SEND` trigger 做 60s 同 sender 合批（窗口内最多 10 条）
  - `IM_AGGREGATION_WINDOW_SEC=60` / `IM_AGGREGATION_MAX_BATCH=10`
  - `WAKE_IM_REPLAY_MAX_BYTES=16384` 双 cap，保留 `<TRUNCATED n_omitted=X>` 标记
  - metric `im_aggregated_total{count}` / `wake_im_replay_truncated_total{reason}`
- 验收：3 条连发消息触发 1 次 session.init；CHAT_HISTORY 长对话 agent 有 `reason="bytes"` 截断记录
- 承诺：**R9（IM 语义一致性）**

### P6-11~13  Phase 6 联合收官（计划中）

- P6-11: `[x]` 所有 P6 票部署完成后，补一张"事故复盘 + 新增 R-INV"承诺到 `docs/architecture/message-wake-principles.md`：runtime 消费端只信 dispatch 透传的 id 集合（由 PR-46 落地）。**已落：R9 (Wake Continuity) + R10 (Consumer SSOT) 正式升为架构承诺；§七 P6 事故复盘补齐**（2026-04-24）。
- P6-12: `[x]` 移除 `chat_messages.read` 字段的 runtime 读取约束，文档化为 "UI-only" 字段。**已落：P6-12 工单审计所有触点 + CI `lint_chat_messages_read.sh` 强制 R10 + 4 个僵尸 Business 路由贴弃用注释**（2026-04-24）。
- P6-13: `[x]` `docs/roadmap/tickets/reviews/PR-45-review.md` 补 Wave 1F 线上证据。**已落：2026-04-24 review 完成；状态机证据 + 单测链覆盖到 §3.4；PR-45.1 观测性补丁 + canary 脚本作为 §五 follow-ups 交接**。

---

## 观测与验收（全 Phase 贯穿）

这些不是单独 phase，而是每一步都要满足的基线：


| ID    | Status | Item                                                                                                                                            | 承诺      |
| ----- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| OBS-1 | `[x]`  | 所有跨服务 HTTP 调用带 `X-Internal-Service` — PR-05（`service_name=` 必填）+ PR-06（服务端消费 + lint）；违例 CI 拦截                                                   | R7      |
| OBS-2 | `[x]`  | 所有跨服务日志带 `scope_id` 绑定 — PR-24 LogContext contextvar + service-wide `install_service_logging`                                                   | R4      |
| OBS-3 | `[x]`  | metric：`dispatch_total{trigger_type, result}`、`outbox_lag_seconds`、`outbox_backlog_count`、`subscriber`_* 齐全（PR-32）；`orphans_total{severity=warn | crit    |
| OBS-4 | `[x]`  | runbook：`docs/runbooks/troubleshooting.md` 增加 "三条查路径"（`/trace` / orphan view / `/metrics` outbox lag），覆盖 PR-25/26/32                            | R4 + R5 |
| OBS-5 | `[x]`  | `docs/architecture/message-wake-principles.md` §五"对照表"补 metric / log 证据列                                                                        | 所有      |


---

## 里程碑 / Release gating


| 里程碑                 | 对应 Phase    | 完成标志                                                 |
| ------------------- | ----------- | ---------------------------------------------------- |
| **M1 — 合约对齐**（基础建设） | Phase 1     | 所有 dispatch 经 Assembler；internal auth 统一；resolver 可用 |
| **M2 — 主路径切换**      | Phase 2     | 消息写入驱动 dispatch；HealthWorker 不再做 dispatch            |
| **M3 — 可观测性**       | Phase 3 + 4 | scope_id 贯穿日志；orphan 告警生效；"消息去哪了" 一键查                |
| **M4 — 状态机化**       | Phase 5     | 所有一等实体单入口状态转移；旧字段清理                                  |


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
- `novaic-cortex/novaic_cortex/`*（P3-1 scope meta；P5-2 scope 状态机）

### 新建代码

- `novaic-common/novaic_common/wake/{assembler,trigger_types,errors}.py`（Phase 1）
- `novaic-common/novaic_common/agents/ownership.py`（P1-3）
- `novaic-common/novaic_common/logging/context.py`（P3-5）
- `novaic-business/business/subscribers/dispatch_subscriber.py`（P2-3）
- `novaic-entangled/*/message_outbox.`*（P2-2，方案 B）
- `novaic-agent-runtime/task_queue/workers/recovery_worker_sync.py`（原 HealthWorker 改名，P4-1）

### 文档

- `docs/architecture/message-wake-principles.md`（架构承诺，SSOT）
- `docs/roadmap/message-wake-refactor.md`（本页）
- `docs/roadmap/technical-debt.md`（索引）
- `docs/runbooks/troubleshooting.md`（OBS-4：SOP 追加）

---

## 附录 B — 触发点迁移矩阵（P1-6/7/8 对照表）


| 现有入口                                    | 当前做法                                                                                | 迁移后                                                                                                               |
| --------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `Business.subagent_send`                | `_dispatch_trigger(trigger_type="subagent_send", subagent_id=sub_id)`               | Phase 1：`Assembler.assemble(TriggerType.SUBAGENT_SEND, agent_id, subagent_id=...)` Phase 2：**删除**，由 subscriber 接管 |
| `Business.spawn_subagent`               | `_dispatch_trigger(trigger_type="spawn_subagent", ..., metadata={initial_context})` | 同上（initial_context 保留进 Assembler metadata）                                                                        |
| `HealthWorker._scan_unhandled_messages` | 直调 `/dispatch` with `user_id=""`                                                    | Phase 1：`Assembler`（自动解 user_id） Phase 2：**整段删除**                                                                 |
| `SchedulerWorker` 定时扫 `due-wake`        | 直调 `/dispatch` with `TriggerType.SCHEDULED_WAKE`                                    | Phase 1：改走 `Assembler`                                                                                            |
| **新**：USER_MESSAGE 写入                   | 无人主动 dispatch，靠兜底                                                                   | Phase 2：outbox subscriber → `Assembler`（`TriggerType.USER_MESSAGE`）                                               |


---

## 附录 C — 审视时间线

- 2026-04-17：`hihi` 事件发生，Phase 0 诊断完成
- Phase 1 / M1 预计完成：**（待排期）**
- Phase 2 / M2 预计完成：**（待排期）**
- Phase 3 + 4 / M3 预计完成：**（待排期）**
- Phase 5 / M4：长期

每 Phase 完成后在 `HANDOVER.md` 追加一条"最后更新"。