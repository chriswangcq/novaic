# 技术债与待办

> 对应原 `**HANDOVER.md` §十六**。「已落地」为历史审计记录；**未勾选**为仍待规划/验证项（随迭代变化，以代码与 issue 为准）。

## 近期已落地（摘要，2026-03 前后）

- Entangled：`store.py` 游标与 `_cf`/`_rid`；`ws_handler` 背压与心跳；`cache.rs` TTL；**EntityStore** 与 Protocol 统一；自动级联已移除（一次写入 = 一次通知）；`entangled_sync_versions` 持久化。
- 前端：删除旧 `@entangled/react` 大包；`**entangled_method_optimistic`**；Path C `**nav_changed**`；Slot **NavState v2**；**Schema Codegen**；**HTTP→Entangled** 迁移（`api.ts` 减负）。
- 其它：AppWS **syncContractVersion**；invalidate 自愈进 Rust；Cortex **DFS** 与存储 ACL；等。

详述见 `**docs/architecture/`** 各篇（`app-ui.md`、`entangled-store-and-app-ws.md`、`agent-pipeline.md`）。

## 进行中的系统性重构

- **Message → Wake 主干重构**（2026-04-17 `hihi` 事件触发，涉 R1–R8 共 8 条架构承诺）
  - 承诺文档（SSOT）：[architecture/message-wake-principles.md](../architecture/message-wake-principles.md)
  - 实施清单（Phase 1–5 + checklist）：[message-wake-refactor.md](message-wake-refactor.md)
  - 状态：Phase 0 诊断完成，待排期进入 Phase 1（合约对齐）
  - 影响：Entangled / Business / Queue Service / Agent Runtime / Cortex 全链路

## 待办清单（HANDOVER 原文意图）

- iOS 键盘输入框：`**--keyboard-height**` 真机充分验证  
- 服务端数据自动清理（runtime context、queue、logrotate）  
- **Watchdog v2**：Per-Agent 轮询，防重复 Runtime  
- WebRTC 多客户端操控冲突  
- Gateway DB 访问异步化（同步 SQLite 在 async 中阻塞风险）  
- **Skill 商店 / ClawHub**  
- **原生视频渲染**（各端硬解路径）  
- WS 断开前端 toast  
- `prefsRepo` / IndexedDB 彻底移除（selectedAgent → Entangled 等）  
- **Model 实体规范化**（见 [model-entity-refactor.md](model-entity-refactor.md)）
- ~~**内部 Key 未统一**：PR-05 调研期发现。~~
  **✗ 归档为"明确不做"（2026-04-18 PR-20 规划期复盘）**：每服务独立 key 提供**横向移动隔离**——Business 被打穿时，攻击者拿到的 key 只能认 Queue，不能直连 Cortex。我们的服务拓扑只有 5-6 个节点，多填几个 env 的"认知成本"远低于失去隔离的安全成本。PR-20（env 收窄）不改变这一设计，secrets 保留为 env 第一类。（PR-33 Phase 4 已彻底删除 `common/http/clients.py` 里作废的 `NOVAIC_INTERNAL_KEY is not set` WARNING——那只是个指错门的面包屑，不影响本条的"不统一 key"决定。）
- ~~**重复的 Access Log**：Queue Service 等服务自带的 uvicorn `access_log=True` 和 `CallerLoggingMiddleware` 在同一请求上会各打一行日志（不冲突，但啰嗦），后续可统一关闭 uvicorn access log（PR-06 引入，待清理）。~~
  **✓ 已还清（TD-1，2026-04-20）**：`novaic-agent-runtime/queue_service/main.py` 把 `uvicorn.run(..., access_log=False)` 显式关掉，`CallerLoggingMiddleware` 独占访问日志。
- ~~**`internal_client` 命名陷阱**：在 `common.http.clients` 中，`internal_client` 只是 `internal_sync_client` 的 alias。这极易导致 asyncio 消费方误用（如在 PR-10 `DispatchAssembler` 中错误引用，导致 `await _client.post` 报 TypeError）。由于该 alias 散布于数十处代码，我们暂时不全局替换，但后续（或 PR-19 cleanup 时）应强制要求显式导入 `internal_sync_client` / `internal_async_client` 并删除此含糊不清的 alias。~~
  **✓ 已还清（TD-2，2026-04-20）**：删除 `common.http.clients.internal_client` / `external_client` alias，全仓改用显式 `internal_sync_client` / `internal_async_client`（agent-runtime / business / gateway 共 12 处调用点迁移完毕）。测试 `test_internal_client.py::test_internal_client_alias_removed` / `..._from_package_export` 作为不变量护栏，阻止 alias 重新引入。
- **Silent Dispatch Failure 不可观测 (PR-11)**：Business 中调用 `DispatchAssembler` 发送消息采用了 Fire-and-Forget 语义。如果网络异常或 Queue 报错，虽然会打出 `logger.error`，但外部毫无感知（用户依然收到 HTTP 200）。这会导致严重的“消息孤儿”假象。目前已在 `PR-32` 中规划加入 `dispatch_failed_total{caller=business}` 计数器作为底线监控。
- ~~**DispatchSubscriber 静默死在 FastAPI lifespan (PR-17 / PR-34 前哨)**：DispatchSubscriber 原先作为 `asyncio.create_task` 挂在 Business 的 FastAPI lifespan 里，任何未捕获异常都会被 task 机制吞掉 → `message_outbox` 停止排空 → 没有告警、没有崩溃、只有一张越来越老的表。PR-17 Canary 靠 buffered-streak 日志打补丁，但"挂在 lifespan 里"这个形状没变。~~
  **✓ 已还清（PR-34 34d/34e，2026-04-20）**：
  1. **34d Subscriber 抽离**：`business/subscribers/dispatch_subscriber.py` 从 `async def run` + `asyncio.Event` + `httpx.AsyncClient` 改为 `threading.Event` + `time.sleep` + `httpx.Client`，调 `assembler.assemble_sync` / `dispatch_sync`。新增 `novaic-business/main_subscriber.py` 作为独立子进程入口（`argparse` 四个 URL、文件日志 `subscriber-YYYYMMDD.log`、`SIGTERM`/`SIGINT` → `subscriber.stop()`），`main_business.py` lifespan 彻底删掉 `asyncio.create_task(subscriber.run())` 块。`scripts/start.sh` 读 `ServiceConfig.SUBSCRIBER_ENABLED` 拉起子进程，`--stop` 路径 `SIGTERM → 等 5s → SIGKILL` graceful 回收。效果：subscriber 崩溃现在会让 `ps aux | grep main_subscriber` 直接看得到（进程没了），退出码非零，不再有"Business API 还活着但 outbox 不动"的静默模式。
  2. **34e async 清零**：`common/wake/assembler.py` 删 `async assemble` / `async dispatch` / `async assemble_and_dispatch` 和 `httpx.AsyncClient`，`common/agents/ownership.py` 删 `async resolve` 与 `asyncio.Lock` 字典（连 `import asyncio` 都删），`_sync` 后缀在 module docstring 里改称"唯一面"。旧测试 `tests/test_assembler.py` 删除，`test_assembler_sync.py` / `test_ownership.py` 补 `test_assembler_has_no_async_methods` / `test_resolver_has_no_async_methods` / `test_module_does_not_import_asyncio` 三条反向不变量。
  3. **34e CI 守门**：`scripts/ci/check_no_internal_async.py` 用显式 `GUARDED` 列表（assembler / ownership / dispatch_subscriber / main_subscriber / health_worker / scheduler_worker / saga_worker_sync / task_worker_sync）检测 `async def` / `import asyncio` / `httpx.AsyncClient` / `await`，`.github/workflows/lint.yml` 接线（顺带把原先漏掉的 `submodules: recursive` 补上——前版 `lint_dispatch.sh` / `lint_httpx.sh` 因此对 submodule 内容一直是 no-op）。`lint_dispatch.sh` / `lint_httpx.sh` 把 `main_subscriber.py` 加进 allowlist（前者 CLI help 字符串、后者合法的 `httpx.Client`）。
  4. **34e 文档**：`docs/architecture/agent-pipeline.md` 新增 §12.7 Sync-by-default 表，列清每个组件的运行形态 + 为什么内部全部同步的故事。
- ~~**`AgentOwnershipResolver._locks` 内存无界增长**：`AgentOwnershipResolver` 为了防止缓存击穿（thundering herd），通过 `setdefault(agent_id, asyncio.Lock())` 给每个 agent 创建了一个锁，但该字典未实现淘汰机制（如 LRU 或随 TTL 清理）。如果是长期存活的服务处理大量不重复的 agent_id，会导致 `_locks` 字典持续膨胀。后续在整理缓存机制或重构为多级缓存时，可引入 `asyncache` 或手动周期性清理超时的 lock，或者只保存"正在请求中"的 Future。~~
  **✓ 已还清（TD-3，2026-04-20）**：`_cache` 改为 `OrderedDict`（上限 `_MAX_CACHE_ENTRIES = 10_000` 的 FIFO 淘汰），`_locks` / `_sync_locks` 只保留"正在请求中"的锁，成功写缓存后在 `finally` 里 `pop`。`invalidate()` 同时清 cache 和 lock。测试 `test_ownership_locks_dropped_after_successful_resolve` / `..._cache_fifo_eviction_over_limit` / `..._invalidate_clears_lock` 和同步路径的 `test_ownership_sync_locks_dropped_after_successful_resolve`。
- ~~**`wake_triggers[].type` 与 `TriggerType` 枚举不对齐**：当前 `definitions.py` 的 LLM schema 中 `wake_triggers[].type` 包含 `["user_message", "timer", "event"]`，而主流程中的 `TriggerType` 枚举包含 `user_message`, `subagent_send`, `spawn_subagent` 等 6 个值。它们本质上是两个独立的枚举，却混用在一个语义下。由于目前它们只共享了 `user_message` 且互不干扰，我们在 PR-09 仅修正了漂移的 `user_response`。后续需要单独开 PR，理清 schema 定义与调度器触发类型枚举的关系。~~
  **✓ 已还清（TD-4，2026-04-20）**：新建 `common/wake/wake_condition.py::WakeCondition` 枚举（`user_message` / `timer` / `event`），与 LLM schema `subagent_rest.wake_triggers[].type` 的 enum 字符串绑定；`TriggerType` docstring 写清"只代表 dispatch 原因"并警告不要混用。`business/internal/subagent.py` 与 `subagent_utils.py` 两处 `wake_triggers` 默认值从 `TriggerType.USER_MESSAGE.value` 改为 `WakeCondition.USER_MESSAGE.value`（顺便修掉 `subagent.py` 没导入 `TriggerType` 的潜在 `NameError`）。测试 `test_wake_condition.py` 断言枚举值与 LLM schema 保持 lockstep，且 TriggerType 的非用户触发（SUBAGENT_SEND / SPAWN_SUBAGENT / SCHEDULED_WAKE / SYSTEM_WAKE / RECOVERED）在 WakeCondition 中不存在。
- ~~**`DispatchResult` 缺 `action` enum (PR-13)**：当前 `DispatchResult` 只有 `buffered: bool` 字段，无法清晰区分 `saga_started` 与 `deduped`（调度器触发时依赖区分是否排重）。在 PR-13 中我们临时取了 `result.raw.get("action")`，后续（可能伴随 PR-15/16）应在 `DispatchResult` 正式引入结构化的 `action` 字段。~~
  **✓ 已还清（PR-17 Canary 调试期）**：`DispatchResult` 现已对齐 Queue Service 的响应 schema — `action: str` (saga_started / buffered / deduped)、`saga_id: str | None`、`scope_id: str | None`，`buffered` 与 `deduped` 改为从 `action` 派生的 property。详见 `novaic-common/common/wake/assembler.py` 与 `novaic-common/tests/test_assembler.py` 的 `test_dispatch_saga_started` / `_buffered` / `_deduped` 三个分支用例。顺便修掉了 PR-17 Phase 2 的一个生产阻塞性 bug：Queue 实际返回 `{"action": ..., "saga_id": ...}` 但旧 schema 读 `body["session_id"]` 抛 `KeyError`，导致 canary 流量 500。
- ~~**`scheduler_worker_sync.py` 命名已过时 (PR-13)**：在 PR-13 中我们将调度轮询主体从 `time.sleep` 改造为了 `async def run()` + `asyncio.sleep()` 以支撑 Assembler 协程，这让 `_sync` 后缀名不副实。~~
  **✓ 已还清（PR-34 34e，2026-04-20）**：PR-34 34c 先把 SchedulerWorker 重新改回 `threading.Event` + `time.sleep` 的纯同步模型（调用 `assembler.dispatch_sync`），34e 再把 `scheduler_worker_sync.py` → `scheduler_worker.py`、`health_worker_sync.py` → `health_worker.py`，同步更新 `main_novaic.py` / `task_queue/workers/__init__.py` / 测试 import 路径。`SagaWorkerSync` / `TaskWorkerSync` 的文件名保留 `_sync` 仅因暂未重命名（行为已经是 sync-by-default），后续 PR 可一并扫尾。
- **HealthWorker 空 user_id 导致静默失败的隐患 (PR-12已修复)**：历史上的 `HealthWorker` 在 fallback 发送时写死了 `user_id=""`，由于 Queue 的 `/dispatch` 端点会 400 拒绝空 user_id，导致该 fallback 一年多来从未真正成功过。PR-12 接入 `DispatchAssembler` 后，由于 `AgentOwnershipResolver` 会自动查出真实 `user_id`，该预存 bug 被附带修复。为了防止修复后历史挤压的 orphan messages 瞬间被打出洪峰，PR-12 中加入了 `MAX_FALLBACK_PER_TICK = 50` 保护。
- **Entangled `message_outbox` 无版本化迁移工具 (PR-14)**：`message_outbox` 表通过 `CREATE TABLE IF NOT EXISTS` 创建，没有 Alembic 式的版本化迁移系统。后续如需加列只能靠 `ALTER TABLE ADD COLUMN`（SQLite 支持但受限：不能删列、不能改列类型）。这是当前阶段可接受的代价，但如果 outbox schema 未来频繁演进，应考虑引入轻量迁移框架。
- **`mark_failed` 用 999999 哨兵烧毁真实 attempts 计数 (PR-16)**：`mark_failed` 遇到 permanent 错误时使用了 999999 作为哨兵值来避免死循环，但这会导致真实 attempts 计数丢失。等 PR-26 orphan emitter 依赖 attempts 区分事故类型（"一次即死" vs "重试耗尽"）时必须先返工 outbox schema（加 `status` 列或允许客户端传实际 attempts）。
- ~~**HealthWorker 遗留观察项 (PR-19 追踪)**：PR-17 Canary Phase 1/2 观察期在生产日志里发现两个 HealthWorker 的预存问题……~~
  **✓ 已还清（PR-19，2026-04-18）**，实际落地范围：
  1. **`X-Internal-Key` 注入（B.1）**：`task_queue/workers/health_worker_sync.py::_get_client` 从 `ServiceConfig.QUEUE_SERVICE_INTERNAL_KEY` 读取并显式附加到 `internal_async_client(headers=…)`，和 `DispatchAssembler.__init__` 保持同一模式。验证：prod 重启后 `/api/queue/recover/all` 自 `22:40:30` 起 0 条 401（重启前每日 827 条）。
  2. **同模式 spot fix（B.5）**：`novaic-business/business/internal/message.py::interrupt_agent` 调 `/api/queue/recover/cancel-all` 时也缺 `X-Internal-Key`，在 B.1 同一 commit 内顺手修掉，用例不单独新增测试（逻辑与 B.1 相同）。
  3. **`queue_400` / `no_owner` 降噪（B.2）**：PR-19 Discovery `§F.2` 证实 `400 user_id is required` 已被 PR-12 的 `DispatchError` 过滤掉，历史孤儿数据**没有**再产生新错误（grep 结果 12:55 UTC 起归零），因此取消 `cleanup-orphan-schedules.py` 脚本。PR-19 仅把 `logger.error("Skip waking agent=…")` 改为 `logger.info("event=health_skip agent=… reason=<kind>")`，并新增 `HealthWorkerMetrics.fallback_skipped` 计数器，测试：`tests/test_health_dispatch.py::test_health_worker_skip_logs_as_info_and_increments_skipped`。
  4. **Buffered-streak 限流（F.6 Optional α）**：2026-04-18 PR-17 收尾时发现 `canary_a_1` 因 `model_id=canary` 无真实 LLM 消费 saga，导致 108 条未读消息被 HealthWorker 每 5s 重发（1183 次 `action=buffered`，日志刷屏）。已手工把 `chat_messages` 标 `read=1, processed=1` 止血；PR-19 新增 `HealthWorkerSync._buffered_streak` 表 + `_BUFFERED_STREAK_LOG_EVERY=10` 的 rate-limited 日志，和一行 `event=health_fallback_streak_cleared prior_streak=N action=<非buffered>` 的转场标记。测试：`test_health_worker_buffered_streak_rate_limited` / `test_health_worker_buffered_streak_cleared_on_non_buffered`。
  5. **`internal_client` 命名陷阱（F.7）**：PR-19 保留 `from common.http.clients import internal_async_client` 显式命名，全局 alias 删除留待独立 common PR。
- ~~**Subscriber `_claim_batch` 无异常退避 (PR-16)**：当 Entangled 发生长时间故障时，`_claim_batch` 的 `logger.exception` 会每 0.5s 触发一次，导致海量日志刷屏。后续需要加上 error backoff 或者 rate-limited logging 机制。~~
  **✓ 已还清（PR-17 Canary 尾声）**：`_claim_batch` 现在返回 `Optional[list[dict]]`（`None` = 失败、`[]` = 正常空队列），失败触发 `run()` 侧指数退避（base 1s，cap 30s）。日志侧：首次失败打完整 traceback，之后每 30s 最多一条 `WARNING` 摘要（带 streak 计数与异常类型），恢复后打一行 `recovered after N consecutive failures`。回归测试：`novaic-business/tests/test_dispatch_subscriber.py::test_subscriber_claim_backoff_rate_limited_logging`。
- **Subscriber `idempotency_key` 未传 (PR-17 Canary 尾声修复)**：PR-15/PR-16 的 subscriber 调 `assembler.assemble()` 时没传 `idempotency_key`，于是双发场景下由 Queue 的**同 agent session 协调器**去重（`action=buffered`），而不是**幂等台账**（`action=deduped`）。业务效果正确但与 runbook `§E` 跟踪的 `action=deduped` 信号不吻合。PR-17 观察阶段已修：subscriber 使用 `f"msg:{row['message_id']}"` 作为 key，与 inline 路径 (`business/message_actions.py::_dispatch_trigger`) 对齐。测试：`test_subscriber_passes_idempotency_key`。
- ~~**env 膨胀 / canary 静默失败风险 (PR-33 立项)**：`DISPATCH_SUBSCRIBER_ENABLED` / `NOVAIC_ENABLE_SUBSCRIBER` / `NOVAIC_HEALTH_CHECK_INTERVAL` 三处 env 在 Business main、start.sh、deploy-business.sh 之间穿行；`common/http/clients.py` 对一个已作废的 `NOVAIC_INTERNAL_KEY` 每次建 client 都打 WARN；`common/agents/ownership.py::get_resolver` 用 `os.getenv("BUSINESS_INTERNAL_URL", "http://localhost:8200")` 三层 fallback；`novaic-agent-runtime/.../assembler_factory.py` 用 `getattr(ServiceConfig, "BUSINESS_URL", os.environ.get(..., "http://127.0.0.1:19998"))` 三层 fallback。PR-17 bake 已经在这类形状上被烧过——字段拼错/env 未设都静默退回 localhost，每个 wake 打进虚空排查两天。~~
  **✓ 已还清（PR-33，2026-04-20，六阶段）**：
  1. **P1** — `services.json` 新增 `runtime_switches`（`subscriber_enabled` / `health_check_interval_seconds` / `scheduler_poll_interval_seconds` / `fallback_max_per_tick`），`ServiceConfig` 暴露四个常量 + `log_startup_snapshot(logger)` 类方法。`strict_config.py` 的 AST 校验自动覆盖新 key，缺键启动即 `ConfigError`。
  2. **P2** — `main_business.py` 删 `--enable-subscriber` argparse + `DISPATCH_SUBSCRIBER_ENABLED` env，`SUBSCRIBER_ENABLED = ServiceConfig.SUBSCRIBER_ENABLED`，lifespan 头部调用 `log_startup_snapshot`。
  3. **P3** — `scripts/start.sh` 删 `NOVAIC_ENABLE_SUBSCRIBER` / `NOVAIC_HEALTH_CHECK_INTERVAL` 桥，`scripts/deploy-business.sh` 的 `unset NOVAIC_*` 段改为 services.json 编辑流程。`main_novaic.py health|scheduler` 子命令删 `--check-interval`，改读 `ServiceConfig.HEALTH_CHECK_INTERVAL_SECONDS` / `SCHEDULER_POLL_INTERVAL_SECONDS`。每个 worker 启动头部也调 `log_startup_snapshot`。
  4. **P4** — `common/http/clients.py` 删 `NOVAIC_INTERNAL_KEY is not set` WARN（历史遗留）。测试 `test_internal_sync_client_is_silent_without_novaic_internal_key` 锁定该字符串永不再出现。
  5. **P5** — `ownership.py::get_resolver` / `agent-runtime/.../assembler_factory.py::get_assembler` 删 env fallback，`ServiceConfig.BUSINESS_URL` / `QUEUE_SERVICE_URL` 作为唯一来源；缺键由 `strict_config` 在启动时大声炸。`ownership.py` 连 `import os` 都删掉，`test_ownership_module_does_not_import_os` 作为反向护栏。
  6. **P6** — `docs/runbooks/subscriber-canary.md` 的 Canary Phase 2 / fast rollback / troubleshooting 全部改写为 services.json + 重启流程；本节 TD-1..TD-4 + PR-33 全部归档。
  一句话：原来翻 canary 要在 3 个 shell 文件 / 2 个 python main 文件 / 1 个 env + 1 个 CLI 之间协调，任一漏一处就静默走另一个默认值；现在只剩"编辑 services.json + 重启"一条路，`grep "runtime_switches=" business.log | head -1` 就能一眼看出"这个进程自认正在跑什么开关"。

## 路线 A：Entangled 引擎内置乐观写（未来演进）

> **触发条件**：以下任一成立时启动规划  
>
> - Entangled 作为独立开源产品，需服务多种 UI 框架（React / Flutter / SwiftUI）  
> - NovAIC 需要 offline-first（断线队列 + 重连同步）  
> - 出现远程 Entangled 部署（延迟 > 100ms，需掩盖网络往返）  
> - 出现多端同时编辑同一实体的并发写场景

**当前状态**：采用路线 B（Pessimistic-first + TanStack Query 内存乐观展示）。写操作悲观走 WS action，UI 层用 `onMutate/onError/onSettled` 做纯内存假数据注入与自动回滚。

**路线 A 核心思路**：

- **Tentative Write**：Rust `entangled-client` 收到 mutation 后，立即写入本地 `entity_items`（标记 tentative version），同时发 WS action  
- **Server Ack → Confirm**：Server delta sync 回来后，tentative 升级为 confirmed，version 对齐  
- **Server Reject → Rollback**：Server 拒绝时，引擎自动 re-sync snapshot 回滚本地状态  
- **Offline Queue**：WS 断线时 mutation 入队，重连后按序重放  
- **冲突检测**：Version vector 或 last-writer-wins 策略，处理多端并发写  
- **UI 层零感知**：读 `entity_list` 即包含 tentative 数据，无需 React 层 `onMutate`

**预估工程量**：2-3 周纯 Rust 工程（`entangled-client` crate 改造 + 协议扩展 + 测试）

Skills 领域调查报告：[historical-doc-links.md](../historical-doc-links.md)。