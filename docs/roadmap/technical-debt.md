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
- **内部 Key 未统一**：`QUEUE_SERVICE_INTERNAL_KEY` / `CORTEX_INTERNAL_KEY` / 其他服务 Key 各自独立。
  后续 PR 统一为 `NOVAIC_INTERNAL_KEY` + 服务端 auth 兼容灰度。
  （PR-05 调研期发现，刻意延后。见 reviews/PR-05-preflight-review.md §2。）
- **重复的 Access Log**：Queue Service 等服务自带的 uvicorn `access_log=True` 和 `CallerLoggingMiddleware` 在同一请求上会各打一行日志（不冲突，但啰嗦），后续可统一关闭 uvicorn access log（PR-06 引入，待清理）。
- **`internal_client` 命名陷阱**：在 `common.http.clients` 中，`internal_client` 只是 `internal_sync_client` 的 alias。这极易导致 asyncio 消费方误用（如在 PR-10 `DispatchAssembler` 中错误引用，导致 `await _client.post` 报 TypeError）。由于该 alias 散布于数十处代码，我们暂时不全局替换，但后续（或 PR-19 cleanup 时）应强制要求显式导入 `internal_sync_client` / `internal_async_client` 并删除此含糊不清的 alias。
- **Silent Dispatch Failure 不可观测 (PR-11)**：Business 中调用 `DispatchAssembler` 发送消息采用了 Fire-and-Forget 语义。如果网络异常或 Queue 报错，虽然会打出 `logger.error`，但外部毫无感知（用户依然收到 HTTP 200）。这会导致严重的“消息孤儿”假象。目前已在 `PR-32` 中规划加入 `dispatch_failed_total{caller=business}` 计数器作为底线监控。
- **`AgentOwnershipResolver._locks` 内存无界增长**：`AgentOwnershipResolver` 为了防止缓存击穿（thundering herd），通过 `setdefault(agent_id, asyncio.Lock())` 给每个 agent 创建了一个锁，但该字典未实现淘汰机制（如 LRU 或随 TTL 清理）。如果是长期存活的服务处理大量不重复的 agent_id，会导致 `_locks` 字典持续膨胀。后续在整理缓存机制或重构为多级缓存时，可引入 `asyncache` 或手动周期性清理超时的 lock，或者只保存"正在请求中"的 Future。
- **`wake_triggers[].type` 与 `TriggerType` 枚举不对齐**：当前 `definitions.py` 的 LLM schema 中 `wake_triggers[].type` 包含 `["user_message", "timer", "event"]`，而主流程中的 `TriggerType` 枚举包含 `user_message`, `subagent_send`, `spawn_subagent` 等 6 个值。它们本质上是两个独立的枚举，却混用在一个语义下。由于目前它们只共享了 `user_message` 且互不干扰，我们在 PR-09 仅修正了漂移的 `user_response`。后续需要单独开 PR，理清 schema 定义与调度器触发类型枚举的关系。
- **`DispatchResult` 缺 `action` enum (PR-13)**：当前 `DispatchResult` 只有 `buffered: bool` 字段，无法清晰区分 `saga_started` 与 `deduped`（调度器触发时依赖区分是否排重）。在 PR-13 中我们临时取了 `result.raw.get("action")`，后续（可能伴随 PR-15/16）应在 `DispatchResult` 正式引入结构化的 `action` 字段。
- **`scheduler_worker_sync.py` 命名已过时 (PR-13)**：在 PR-13 中我们将调度轮询主体从 `time.sleep` 改造为了 `async def run()` + `asyncio.sleep()` 以支撑 Assembler 协程，这让 `_sync` 后缀名不副实。为了防止本 PR scope 与 diff 爆炸，我们在 PR-13 暂不重命名，留待 PR-18 移除 legacy 薄壳时一并更名为 `scheduler_worker.py`。
- **HealthWorker 空 user_id 导致静默失败的隐患 (PR-12已修复)**：历史上的 `HealthWorker` 在 fallback 发送时写死了 `user_id=""`，由于 Queue 的 `/dispatch` 端点会 400 拒绝空 user_id，导致该 fallback 一年多来从未真正成功过。PR-12 接入 `DispatchAssembler` 后，由于 `AgentOwnershipResolver` 会自动查出真实 `user_id`，该预存 bug 被附带修复。为了防止修复后历史挤压的 orphan messages 瞬间被打出洪峰，PR-12 中加入了 `MAX_FALLBACK_PER_TICK = 50` 保护。

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