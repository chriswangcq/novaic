# 桌面 / Web 客户端：实体同步 WebSocket 策略

> 后端实现与字段见 `gateway/api/app_client.py`、`gateway/infra/entangled_ws.py`、`GET /api/entangled/schema`。**`novaic-app` 实现细节在客户端仓库**；本文约定行为，便于前后端对齐。

## 1. 两种连法

| 模式 | URL | 适用 |
|------|-----|------|
| **仅 Gateway** | `wss://<gateway>/app/ws` | 统一入口：实体同步 + WebRTC 信令；实体写经 Business Service `/internal/entities/*` proxy 时，sync 由 Gateway 推送。 |
| **直连 Entangled（可选）** | `entangledWsUrl`（如 `ws(s)://<host>:19900/v1/sync`） | 减轻 Gateway WS 负载或内网分流；需携带与 Gateway 相同的 JWT（`Authorization` 或 `?token=`）。 |

`entangledWsUrl` 在 **有独立 Entangled HTTP**（`ENTANGLED_URL`）时由 schema / WS 首帧下发；仅嵌入模式时可为空。

## 2. Worker 经 Business Service 写实体时的 UI

> **⚠️ 2026-04-16 更新**：Workers（Agent Runtime）不再直连 Entangled HTTP，统一经 **Business Service `/internal/entities/*`** 代理写入。

Workers 通过 `BusinessClient.entity_*` 方法调用 Business Service 的 entity proxy 端点。Business 作为唯一 Entangled HTTP 消费者负责写入并触发 sync-notify，确保只连 **`/app/ws`** 的客户端能收到一致的 sync 帧。

## 3. 协议与首帧

- Gateway `/app/ws` 与独立 **`/v1/sync`** 的 **schema 首帧**形状一致：`type: "push"`、`event: "schema"`、`data.entities` / `hash` / `syncContractVersion`。
- 入站 **`{"type":"ping"}`** 应用层心跳；服务端可能下发 **`type: "heartbeat"`**（独立 Entangled `/v1/sync` 与 Gateway 行为对齐，见 `Entangled` 包 `ws_handler` / `app/ws.py`）。

## 4. 前端落地（checklist）

- [ ] 从 schema 读取 `entangledWsUrl`，决定单连 Gateway 或 **双连**（Gateway 信令 + Entangled sync，或仅其一）。
- [ ] 重连、generation、卸载时取消订阅（与现有 `entangled` Rust/React 层一致）。
- [ ] 与 **`syncContractVersion`** 变更时的全量刷新策略（若有）。
