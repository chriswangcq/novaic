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

## Entity Routing Split（`RemoteEntityStore`，2026-04）

`LOCAL_ONLY_ENTITIES = {users, refresh-tokens, api-keys, vm-users, models, api-key-models}` 留 `gateway.db`，其余（`devices` 等同步实体）代理到 Entangled HTTP。

- **`_local_store`** 注册**所有** entity 定义（含 remote），但只对 LOCAL 建表。这样 `_scope_where` 的 parent 查找（如 `vm-users.parent = devices`）不会 KeyError。
- **CRUD 路由**：每个方法检查 `_is_local(entity)` → 走 `_local_store` 或 `EntangledServiceClient`。
- **Pre-delete hook**：`devices` entity 删除前调 `_cleanup_device_on_pc_client`，向 PC Client 发 `vm_delete`（Linux）/ `avd_delete`（Android）/ `host_desktop_stop`。
- **`vm_status_report`**：只 update 已有设备的 `pc_client_id` + `status`，**不再 auto-create** 防止用户删后重建。

## Worker 直写 Entangled 与 Gateway `/app/ws`（2026-04）

当 **`ENTANGLED_URL`** 启用、Runtime **直连 Entangled HTTP** 写库时，须 **`X-Notify: false`** 并 **`POST /internal/entangled/sync-notify`**（或由 **`GatewayBusinessClient`** 自动完成），否则仅连 Gateway `/app/ws` 的客户端收不到与进程内 store 相同的 sync 帧。直连 **`/v1/sync`** 的客户端仍由 Entangled 进程内 notifier 投递。

## Entangled 单 Store 与 schema push（2026-03）

**后端**：NovAIC `**EntityStore`** 直接作为 Entangled 的 store；引入 `**EntityStoreProtocol(ABC)**`。（独立 Entangled 模式下 Gateway 仍注册同一 store 实例供 notifier，见 `entangled_bridge.py`。）

`**gateway/entity/store.py` — `EntityDef` 字段示例**：

```python
sync_type: property   # STREAM → "stream"，其他 → "list"
sync_limit: int      # stream head_n 窗口（bridge init 常设为 50）
op_log_size: int     # 每 (entity, params) op-log 条数上限（默认 1000）
relations: List       # EntityRelation；bridge 从 parent 元组构建
```

`EntityStore` 提供 `get_all_defs()`（供 notifier `set_store()`）。

`**gateway/entity/entangled_bridge.py`（三件核心事）**：

1. `SyncRegistry` 初始化、版本从 DB hydrate、mutation 持久化
2. `_build_relations()`：扫描 `EntityDef.parent` → 写入 `EntityRelation`
3. `set_entangled_store(gw_store)`：注册给 Entangled notifier

`**gateway/api/app_client.py`**：`handle_subscribe` / `handle_load_more` / `handle_unsubscribe` 统一 `get_entity_store()`；连接建立后首包 `**{ entities, hash, syncContractVersion }**`（版本来自 `gateway.entity.sync_contract`，与 REST `/api/entangled/schema`、Entangled `ws_handler` 对齐）。

**subscription_cascade**：客户端只 `subscribe A`，服务端按 `subscription_cascade` 展开并推送级联实体初始 sync。

**前端**：以 Rust `**entangled_method_optimistic`** 为主闭环；`hooks.tsx` 工厂化；已移除历史 `**@entangled/react**` 大包。

**能力协商**：`EntityStoreProtocol`；`ws_handler` duck-type `exists_before()` / `list_stream()`；WS 打通时下发实体 **capabilities**；精简 `_dispatch_entity_crud` 与冗余 notifier 代理。

## 相关

- [realtime-sync.md](realtime-sync.md) — 通道总览  
- [app-ui.md](app-ui.md) — 前端 Path C  
- 客户端 WS 策略（契约）：[client-ws-strategy.md](../entangled/client-ws-strategy.md)  
- Sync Contract 长文：[historical-doc-links.md](../historical-doc-links.md)

