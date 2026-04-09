# 端上数据与缓存（现行）

> **文档状态（2026-04）**：本文描述 **`novaic-app` 侧**持久化与同步的**现行**做法。更细的协议与订阅见 `docs/SYNC_CONTRACT.md`；总览见 `docs/backend-architecture.md`、`docs/architecture-verification-2026-04.md`。用户向说明见 `docs/sync_design/multi_device_sync_caching.md`。

## 分层概览

| 层次 | 实现 | 说明 |
|------|------|------|
| **用户偏好** | `src/db/prefsRepo.ts` | `localStorage`，前缀 `novaic:{userId}:*` |
| **实体与列表** | `data/entities/*`、`createListStore` | TanStack Query；数据经 **Entangled** 与 Rust 侧缓存，**不**使用 Dexie/IndexedDB 业务表 |
| **清缓存** | `src/db/index.ts` `clearLocalDb` | 清 prefs + `invoke('entity_cache_clear')`（Rust `entangled_cache` 等） |
| **IndexedDB** | `src/db/index.ts` | 未作为同步/列表主存；`getDb`/`resetDb` 为兼容占位 |

消息、执行日志、对话等**具体管线**以 **`novaic-app` 源码**及 **`docs/backend-architecture.md`** 为准；不要按旧稿中的 `messageRepo` / `logRepo` 路径在仓库中机械查找（若仍存在，以调用关系与 Entangled 为准）。

## 长连接与增量

- 前端 **`SyncService`** / **`PushManager`** 处理 AppBridge 连接生命周期（如 `app_bridge_connected` / `app_bridge_disconnected`），与 **Entangled WebSocket** 增量配合；约定见 `docs/SYNC_CONTRACT.md`。

## 相关入口

| 主题 | 文档或路径 |
|------|------------|
| 多端同步与 TTL | `docs/sync_design/multi_device_sync_caching.md` |
| 实现索引 | `docs/sync_design/implementation_plan.md` |
| 协议 | `docs/SYNC_CONTRACT.md` |
