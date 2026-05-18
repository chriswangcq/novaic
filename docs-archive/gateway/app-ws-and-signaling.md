# App WS 与 WebRTC 信令

> 路径参考：`novaic-gateway/gateway/api/app_client.py`

## 1. 当前定位

`/api/app/ws` 是 Gateway 保留的用户边缘长连接。它不是业务实体同步通道，也不是 schema source。

App 的实体数据同步走独立 Entangled sync WebSocket：

```text
App → Gateway /api/app/ws
    ← entangledWsUrl endpoint discovery

App ↔ Entangled /entangled/v1/sync
```

Gateway App WS 只做三件事：

- **连接管理**：按 `user_id` 维护 App 在线连接，用于后端定向 push。
- **Endpoint discovery**：下发客户端应该连接的 Entangled sync WS URL。
- **WebRTC signaling relay**：转发 offer / answer / ICE。

## 2. WebRTC 信令链路

```text
App
  → Gateway /api/app/ws
  → Business /internal/signaling
  → Device
  → CloudBridge
  → VmControl

VmControl
  → CloudBridge
  → Device
  → Business
  → Gateway /api/app/push
  → App WS
```

Gateway 只承担 App 侧中继和 TURN 凭证注入，不拥有 Device、CloudBridge、VmControl 或业务状态。

## 3. 明确不属于 App WS 的事情

- 不承载 Entangled entity sync 数据。
- 不下发 Entangled schema。
- 不处理 `messages.send`、agents、skills、devices 等产品 action。
- 不写业务实体数据库。

这些能力分别属于：

- Entangled sync WS；
- Business action hooks；
- Business/Device 内部 API；
- Blob Service 字节基础设施。
