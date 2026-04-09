# 多端同步与本地缓存 — 实现要点

本文汇总 **novaic-app** 中与同步、缓存相关的代码入口，与 `multi_device_sync_caching.md` 配套。架构总览：`docs/backend-architecture.md`、`docs/architecture-verification-2026-04.md`；订阅契约：`docs/SYNC_CONTRACT.md`。

## 本地存储

- **`novaic-app/src/db/index.ts`**：`clearLocalDb` = 清 prefs + `entity_cache_clear`；IndexedDB 未使用。
- **`novaic-app/src/db/prefsRepo.ts`**：`localStorage` 存用户偏好（选中 Agent、布局等）。

## 业务数据与列表

- **`novaic-app/src/data/entities/`**：如 `agents.ts`、`devices.ts`，**`createListStore`** + `staleTime` / `gcTime`。
- **`application/agentService.ts`**：initialize、选 Agent、CRUD；读写经 **`entangledMethod`**。

## 同步与生命周期

- **`application/syncService.ts`** + **`gateway/pushManager.ts`**：AppBridge 连接/断开事件与重连逻辑。
- **`data/entangled/bootstrap.ts` / `entangledBootstrap.ts`**、**`data/entangled/nav.ts`**、**`src-tauri/src/commands/nav.rs`**：订阅与路由。

## Settings TTL

- **`components/hooks/useSettings.ts`**：工具分类与 builtin skills 的 **15 分钟**模块级缓存。

## 相关文档

| 文档 | 内容 |
|------|------|
| `docs/SYNC_CONTRACT.md` | 订阅集合、nav 串行、`syncContractVersion` |
| `docs/sync-contract-execution-checklist.md` | 落地 checklist |
| `docs/sync_design/multi_device_sync_caching.md` | 用户向说明（表格式） |
