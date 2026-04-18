# Entangled 单 Store、App WS 与稳定性

> 与当前 Gateway / Entangled 实现一致；对应原 `**HANDOVER.md` §10.4–§10.7**。

## WS 稳定性修复（要点）

1. **Ping/Pong 格式**：Rust 发 `{"type":"ping"}`（非仅协议层 Ping 帧），Gateway 重置 90s 超时。
2. **协议层 WebSocket Ping**：Tauri `**app_bridge`** 对 `**Message::Ping**` 回复 `**Message::Pong**`；读循环 `**select!**` 优先处理入站，避免心跳饿死读。
3. **推送线程**：`create_task()` 在非 async 上下文抛错时改为可观测的 WARNING。
4. **USER_MESSAGE 去重**：`onAgentReply` + `findTempByContent()` 等，防乐观更新与推回重复。
5. `**subscribe` 崩溃 → 客户端 RST**：若见 `Connection reset without closing handshake`，查 Gateway `**[AppWS] Message loop crashed`**；根因之一：`store.py` 游标 `**rowid**` 键不稳定 → `**KeyError: 'rowid'**`，修复为别名 `**_cf` / `_rid**`。
6. **Rust 可观测性**：`app_bridge.rs` 记 `**conn_seq`**、结束原因；Entity CRUD 直连 Entangled Service。
7. **Entangled React**：`syncListener` / 重连、卸载 `**stopSyncListener`**、generation 与 Strict Mode。

## App→Gateway WS Request/Response

操作型（`chat_send`、`interrupt`、`webrtc_stop`）全走 WS：

```json
→ {"type":"request","request_id":"uuid","action":"chat_send","data":{...}}
← {"type":"response","request_id":"uuid","data":{...},"error":null}
```

Gateway `_dispatch_request` 进程内调用，零 HTTP 中转。

## `/api/app/ws` 认证与设备分组

- **身份（优先级）**：① `Authorization: Bearer <jwt>` → ② `?token=<jwt>` query param → ③ `X-User-ID` header（Nginx `auth_request` 注入）。Rust 桌面客户端用 ②，浏览器用 ①，Nginx 兜底注入 ③。
- **`/api/ws` alias**：`@router.websocket("/ws")` 是 `/api/app/ws` 的别名，Tauri 桌面端连此路径。Nginx 需为 `/api/ws` 配置独立的 WebSocket upgrade + `auth_request` location。
- **桌面 Tauri**：`**devices.grouped`** 经 Entangled `**entangledMethod` / AppBridge WS**，**不设 HTTP 回退**；断连时应等待重连。
- **实现**：`compute_grouped_devices` 与 `DeviceRegistry.get_user_devices`、`grouped_action` 共用逻辑。

## Entity Routing Split（`AuthEntityStore` + `GatewayBusinessEntityClient`，2026-04）

Gateway 现在采用 **`AuthEntityStore`**（本地 SQLite）+ **`GatewayBusinessEntityClient`**（HTTP 代理到 Business）的双层架构，取代了旧的 `RemoteEntityStore`。

- **`AuthEntityStore`**：仅管理认证相关实体（`users`、`refresh-tokens` 等），本地 SQLite（`gateway.db`）。Gateway **不再**继承 `SqlEntityStore` 为 `GatewayEntityStore`。
- **`GatewayBusinessEntityClient`**：所有非本地实体（`devices`、`messages` 等）的 CRUD 通过 HTTP 代理到 **Business Service** `/internal/entities/*`，由 Business 直连 Entangled HTTP。
- **设备生命周期管理**：由 Business Service 的 `DeviceOrchestrator` 负责，Gateway 不再直接调用 PC Client。
- **`vm_status_report`**：只 update 已有设备的 `pc_client_id` + `status`，**不再 auto-create** 防止用户删后重建。

## Worker 经 Business 写 Entangled（2026-04）

Workers **不再直连 Entangled HTTP**。所有 entity 写操作通过 **`BusinessClient.entity_*`** → Business `/internal/entities/*` → Entangled HTTP。Business Service 统一负责 `X-Notify: false` 与同步帧推送。直连 **`/v1/sync`** 的客户端仍由 Entangled 进程内 notifier 投递。

## Entangled 单 Store 与 schema push（2026-03）

**后端**：**Business Service** 直连 Entangled HTTP，是唯一与 Entangled 交互的服务；引入 `**EntityStoreProtocol(ABC)**`。Gateway 仅保留 `AuthEntityStore`（本地认证实体），不再注册为 Entangled store。

`**EntityDef` 字段示例**：

```python
sync_type: property   # STREAM → "stream"，其他 → "list"
sync_limit: int      # stream head_n 窗口（bridge init 常设为 50）
op_log_size: int     # 每 (entity, params) op-log 条数上限（默认 1000）
```

`EntityStore` 提供 `get_all_defs()`（供 notifier `set_store()`）。

**一次写入 = 一次通知**：Entangled 不存在自动级联。Gateway 按需写入所需实体，客户端渲染层自行决定联动更新策略。

**前端**：以 Rust `**entangled_method_optimistic`** 为主闭环；`hooks.tsx` 工厂化；已移除历史 `**@entangled/react**` 大包。

**能力协商**：`EntityStoreProtocol`；`ws_handler` duck-type `exists_before()` / `list_stream()`；WS 打通时下发实体 **capabilities**；精简 `_dispatch_entity_crud` 与冗余 notifier 代理。

## 相关

- [realtime-sync.md](realtime-sync.md) — 通道总览  
- [app-ui.md](app-ui.md) — 前端 Path C  
- 客户端 WS 策略（契约）：[client-ws-strategy.md](../entangled/client-ws-strategy.md)  
- Sync Contract 长文：[historical-doc-links.md](../historical-doc-links.md)

