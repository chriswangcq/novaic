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

- **身份**：须 `**Authorization: Bearer <access_token>`**，`user_id` **仅**来自 JWT `sub`。不得仅凭 `X-User-ID` 连接；若同时带 `X-User-ID`，须与 `sub` 一致，否则 **4003**。
- **桌面 Tauri**：`**devices.grouped`** 经 Entangled `**entangledMethod` / AppBridge WS**，**不设 HTTP 回退**；断连时应等待重连。
- **实现**：`compute_grouped_devices` 与 `DeviceRegistry.get_user_devices`、`grouped_action` 共用逻辑。

## Entangled 单 Store 与 schema push（2026-03）

**后端**：NovAIC `**EntityStore`** 直接作为 Entangled 的 store；引入 `**EntityStoreProtocol(ABC)**`。

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
- Sync Contract 长文：[historical-doc-links.md](../historical-doc-links.md)

