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