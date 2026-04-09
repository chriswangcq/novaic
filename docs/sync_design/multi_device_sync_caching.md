# Tauri 客户端：多端同步与本地缓存

本文描述 **novaic-app** 中多端同步与本地缓存的**现行**做法。更细的订阅与契约见 `docs/SYNC_CONTRACT.md`；架构总览见 `docs/backend-architecture.md`、`docs/architecture-verification-2026-04.md`。

## 1. 本地持久化层

| 机制 | 位置 | 说明 |
|------|------|------|
| **用户偏好** | `novaic-app/src/db/prefsRepo.ts` | `localStorage`，前缀 `novaic:{userId}:*`（如选中 Agent 等） |
| **全局清缓存** | `novaic-app/src/db/index.ts` `clearLocalDb` | 清 prefs + `invoke('entity_cache_clear')`（Rust 侧 Entangled SQLite 缓存） |
| **IndexedDB** | — | 未使用；`getDb`/`resetDb` 为 no-op |

列表型业务数据由 **Entangled 同步** 与 **TanStack Query 列表 store** 提供，不写入 Dexie。

## 2. 实体列表与缓存策略

| 实体 | Store | 策略（摘自 `createListStore`） |
|------|--------|--------------------------------|
| Agents | `data/entities/agents.ts` | `staleTime: 30_000`，`gcTime: 5 * 60_000` |
| Devices | `data/entities/devices.ts` | 同上 |
| Skills 等 | `data/entities/*.ts` | 同类模式，见各文件 |

`AgentService`（`application/agentService.ts`）负责 **initialize / selectAgent / CRUD**；列表通过 entangled 与 `entangledMethod` 读取。

## 3. 长连接与同步：AppBridge 与 Entangled

前端 **`SyncService`**（`application/syncService.ts`）与 **`PushManager`**（`gateway/pushManager.ts`）处理：

- Tauri 事件 **`app_bridge_connected` / `app_bridge_disconnected`**（AppBridge WebSocket 生命周期）
- 重连退避（`SSE_CONFIG`）与 **重连回调**；重连后由 Rust **`resubscribe_all`** → Entangled **delta 同步**

实体变更由 **Entangled WebSocket 协议**（如 `entities_changed`）驱动，约定见 `SYNC_CONTRACT.md`。

## 4. 启动与订阅：nav + bootstrap

| 步骤 | 代码入口 |
|------|-----------|
| 拉 schema | `entangledBootstrap.ts` → `loadEntangledSubscriptionSchema()` → `GET /api/entangled/schema` |
| 首次导航 | `bootstrapEntangledEntities()` → **`navChanged('home', {})`**（须通过封装，勿裸 `invoke('nav_changed')`，见文件头注释） |
| Rust 侧订阅表 | `novaic-app/src-tauri/src/commands/nav.rs` `route_subscriptions` |

## 5. Settings 与 TTL

`useSettings.ts` 对 **`getToolCategories`** 与 **`getSkills(true)`**（含 builtin）使用 **模块级 TTL 15 分钟**（`_toolsCache` / `_builtinSkillsCache`），减少弹窗重复拉取。其余多通过 **Entangled actions**（`skillsService` / `entangledMethod`），见该文件头注释。

## 6. 体验与边界

- **并行请求**：复杂设置面板可能并发多个 entangled 调用；以 **`SettingsModal` / `AgentToolsTab`** 当前实现为准。
- **离线**：可用性取决于 **Entangled 本地缓存是否已填充** 与 **Gateway 可达性**。

## 7. 相关文档

| 文档 | 内容 |
|------|------|
| `docs/SYNC_CONTRACT.md` | 订阅集合、nav 串行、`syncContractVersion` |
| `docs/sync-contract-execution-checklist.md` | 落地 checklist |
| `docs/sync_design/implementation_plan.md` | 与本文配套的实现要点索引 |
