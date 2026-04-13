# 实时推送、App WS 与 Entangled 同步

> 通道级概览；深度实现见 **[entangled-store-and-app-ws.md](entangled-store-and-app-ws.md)**。代码以 `**novaic-gateway`**、`**novaic-app**`、`**Entangled**` 为准。

## 通道划分

- **前端不使用 SSE** 拉聊天/日志流；实时事件走 **AppBridge WebSocket** → Rust `gateway_push` Tauri 事件。
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

操作类（`chat_send`、`interrupt`、`webrtc_stop` 等）走 WS **request/response**，不回落 HTTP（JSON 形状见 **entangled-store-and-app-ws.md**）。

## `/api/app/ws` 要点

- **认证**：须 `Authorization: Bearer <access_token>`，`user_id` 仅来自 JWT `sub`。
- **Schema 首包**：含 `**syncContractVersion`**，与 REST `/api/entangled/schema`、Entangled `ws_handler` 对齐。

## Entangled 单 Store（摘要）

- `**EntityStore**` 作为 Entangled store；一次写入 = 一次通知，无自动级联。
- 详稿：**[entangled-store-and-app-ws.md](entangled-store-and-app-ws.md)**。

## Sync Contract 长文

历史树：[historical-doc-links.md](../historical-doc-links.md)（`SYNC_CONTRACT` 等）。

## 排障

**[runbooks/troubleshooting.md](../runbooks/troubleshooting.md)**；AppWS / `rowid` / store 游标见 **entangled-store-and-app-ws.md**。