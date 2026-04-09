# 实时推送、App WS 与 Entangled 同步

> 对应 `**HANDOVER.md` §10**。代码以 `novaic-gateway`、`novaic-app`、`Entangled` 子模块为准。

## 通道划分

- **前端不再使用 SSE** 拉聊天/日志流；实时事件走 **AppBridge WebSocket** → Rust `gateway_push` Tauri 事件。
- Gateway 内 **Worker 侧 SSE**（`gateway/sse/broadcaster.py` 等）用于 **Gateway→Worker**，不是浏览器通道。

## WS Push 事件（用户维度）


| event            | 说明                                                         |
| ---------------- | ---------------------------------------------------------- |
| `chat_message`   | 聊天消息                                                       |
| `logs_updated`   | 日志更新提示（详情多由前端再 GET）                                        |
| `config_updated` | 配置变更（`settings` / `default_model` / `agent_model` 等 scope） |


## 多端配置同步（概念）

客户端 A 改设置 → Gateway 写库 + `push_to_user("config_updated")` → 客户端 B `SyncService` 去抖 reload → Zustand 更新。

## App ↔ Gateway 请求（WS）

操作类（`chat_send`、`interrupt`、`webrtc_stop` 等）走 WS **request/response**，不回落 HTTP：

```json
→ {"type":"request","request_id":"...","action":"...","data":{...}}
← {"type":"response","request_id":"...","data":{...},"error":null}
```

## `/api/app/ws` 要点

- **认证**：须 `Authorization: Bearer <access_token>`，`user_id` 仅来自 JWT `sub`；`X-User-ID` 若存在须与 `sub` 一致。
- **Schema 首包**：含 `**syncContractVersion`**，与 REST `/api/entangled/schema`、Entangled `ws_handler` 对齐（桌面 `app_bridge` / TS 合约版本）。

## Entangled 与单 Store（摘要）

- NovAIC `**EntityStore**` 作为 Entangled 的 store；`entangled_bridge` 负责 SyncRegistry、关系展开、`set_entangled_store`。
- **subscription_cascade** 在服务端 `handle_subscribe` 展开，客户端可只 subscribe 根实体。
- 前端数据写优先 `**entangledMethod` / `entangled_method_optimistic`**；`api.ts` 仍保留的 HTTP 多为文件上传、健康检查、设备枚举、部分 WebRTC 信令等（见 HANDOVER §11.7 表）。

## Sync Contract 长文

规范全文在历史树中，见 `**[historical-doc-links.md](../historical-doc-links.md)**`（`SYNC_CONTRACT` 等）。

## 稳定性提示（排障索引）

Ping/Pong JSON 格式、协议层 **Ping/Pong**、`store.py` 游标 `**rowid`** 别名（`_cf`/`_rid`）、AppWS 崩溃查 `[AppWS] Message loop crashed` — 详见 `**[runbooks/troubleshooting.md](../runbooks/troubleshooting.md)**`。