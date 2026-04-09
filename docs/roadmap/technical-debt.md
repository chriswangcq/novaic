# 技术债与待办

> 对应原 **`HANDOVER.md` §十六**。「已落地」为历史审计记录；**未勾选**为仍待规划/验证项（随迭代变化，以代码与 issue 为准）。

## 近期已落地（摘要，2026-03 前后）

- Entangled：`store.py` 游标与 `_cf`/`_rid`；`ws_handler` 背压与心跳；`cache.rs` TTL；**EntityStore** 与 Protocol 统一；`subscription_cascade` 服务端化；`entangled_sync_versions` 持久化。
- 前端：删除旧 `@entangled/react` 大包；**`entangled_method_optimistic`**；Path C **`nav_changed`**；Slot **NavState v2**；**Schema Codegen**；**HTTP→Entangled** 迁移（`api.ts` 减负）。
- 其它：AppWS **syncContractVersion**；invalidate 自愈进 Rust；Cortex **DFS** 与存储 ACL；等。

详述见 **`docs/architecture/`** 各篇（`app-ui.md`、`entangled-store-and-app-ws.md`、`agent-pipeline.md`）。

## 待办清单（HANDOVER 原文意图）

- [ ] iOS 键盘输入框：**`--keyboard-height`** 真机充分验证  
- [ ] 服务端数据自动清理（runtime context、queue、logrotate）  
- [ ] **Watchdog v2**：Per-Agent 轮询，防重复 Runtime  
- [ ] WebRTC 多客户端操控冲突  
- [ ] Gateway DB 访问异步化（同步 SQLite 在 async 中阻塞风险）  
- [ ] **Skill 商店 / ClawHub**  
- [ ] **原生视频渲染**（各端硬解路径）  
- [ ] WS 断开前端 toast  
- [ ] `prefsRepo` / IndexedDB 彻底移除（selectedAgent → Entangled 等）  
- [ ] **Model 实体规范化**（见 [model-entity-refactor.md](model-entity-refactor.md)）  

Skills 领域调查报告：[historical-doc-links.md](../historical-doc-links.md)。
