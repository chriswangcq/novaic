# 桌面 / Web 客户端：实体同步 WebSocket 策略

> 后端实现与字段见 `gateway/api/app_client.py`、`gateway/infra/entangled_ws.py` 和 Entangled `/v1/sync` schema 首帧。**`novaic-app` 实现细节在客户端仓库**；本文约定行为，便于前后端对齐。

## 1. 两种连法

| 模式 | URL | 适用 |
|------|-----|------|
| **Gateway AppWS** | `wss://<gateway>/app/ws` | 信令入口：WebRTC、业务 request/response、Entangled endpoint discovery。 |
| **直连 Entangled** | `entangledWsUrl`（如 `ws(s)://<host>:19900/v1/sync`） | 实体同步入口；schema 首帧与 sync/action/load_more 均走这里，需携带与 Gateway 相同的 JWT（`Authorization` 或 `?token=`）。 |

`entangledWsUrl` 由 Gateway AppWS 的 `event=entangled_endpoint` 下发；schema 不经过 Gateway。

## 2. Worker 经 Business Service 写实体时的 UI

> **⚠️ 2026-04-16 更新**：Workers（Agent Runtime）不再直连 Entangled HTTP，统一经 **Business Service `/internal/entities/*`** 代理写入。

Workers 通过 `BusinessClient.entity_*` 方法调用 Business Service 的 entity proxy 端点。Business 作为唯一 Entangled HTTP 消费者负责写入并触发 Entangled notifier，直连 **`/v1/sync`** 的客户端收到一致 sync 帧。

## 3. 协议与首帧

- Gateway `/app/ws` 只下发 endpoint：`type: "push"`、`event: "entangled_endpoint"`、`data.entangledWsUrl`。
- 独立 **`/v1/sync`** 下发 schema 首帧：`type: "push"`、`event: "schema"`、`data.entities` / `hash` / `syncContractVersion`。
- 入站 **`{"type":"ping"}`** 应用层心跳；服务端可能下发 **`type: "heartbeat"`**（独立 Entangled `/v1/sync` 与 Gateway 行为对齐，见 `Entangled` 包 `ws_handler` / `app/ws.py`）。

## 4. 前端落地（checklist）

- [ ] 从 Gateway endpoint event 读取 `entangledWsUrl`，再由 Entangled WS schema 首帧注册 schema。
- [ ] 重连、generation、卸载时取消订阅（与现有 `entangled` Rust/React 层一致）。
- [ ] 与 Entangled **`syncContractVersion`** 变更时的全量刷新策略（若有）。
