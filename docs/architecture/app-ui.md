# 客户端前端架构要点

> 对应 `**HANDOVER.md` §11**。完整分层说明见子模块 `**novaic-app/FRONTEND_ARCHITECTURE.md`**。

## 三层（Render / Business / DB）

- **DB 事实源**：Entangled；IndexedDB 业务主存已移除。数据流：Subscribe → 同步 → Rust SQLite 缓存 → `entities_changed` → React。
- **登录**：`auth.ts` → `pushToken` → `update_cloud_token` → `agentService.initialize()`。
- **登出**：`getSyncService().disconnect()` + `resetServices()`。

## Headless / Path C（动词）

- **读**：`useList` / `useForm` / `useStream`，由 `entities_changed` 驱动。
- **写**：`dispatch` → `entangled_method_optimistic` 或 `entangled_method`。
- **路由**：`navChanged(route, params)` → Rust `nav_changed` → 路由表订阅。

### 路由与实体（主槽，摘要）


| 路由             | 订阅实体（摘要）                                                     |
| -------------- | ------------------------------------------------------------ |
| `home`         | agents, models, devices                                      |
| `conversation` | 上述 + messages、execution-logs、agent-tools、**agent-binding** 等 |
| `settings`     | agents, models, api-keys, skills、**agent-binding** …         |


**Slot**：除默认 `main` 外，可用 `slot: vm-${deviceId}` 等隔离订阅（`nav_release_slot`）。

## Schema Codegen

```bash
python scripts/generate_entity_types.py
python scripts/generate_entity_types.py --check
```

生成 `novaic-app/src/data/entities/__generated__.ts`。

## 关键文件速查（novaic-app）


| 需求             | 文件                                                           |
| -------------- | ------------------------------------------------------------ |
| 远程桌面           | `useWebRtc.ts`、`WebRtcScrcpyView.tsx`                        |
| 操控台            | `DeviceConsole.tsx`、`ConsoleToolbar.tsx`、`useRemoteInput.ts` |
| 聊天发送           | `ChatInput.tsx`、`messagesStore` / `useMessages`              |
| 导航 / Entangled | `src/data/entangled/nav.ts`、`dispatch.ts`、`hooks.tsx`        |
| Rust 导航        | `src-tauri/src/commands/nav.rs`                              |


## Skills 调查报告（历史）

OpenClaw 对照与五子领域报告见 `[historical-doc-links.md](../historical-doc-links.md)`。