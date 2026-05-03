# Entangled Store 与 App WS 当前边界

> 当前主路径：Entangled 负责实体同步，Gateway App WS 负责 push/signaling/endpoint discovery。两者不要混成一条业务数据通道。

## 1. App 数据面

```text
App startup
  → Gateway /api/app/ws
  ← entangledWsUrl

App Entangled Rust client
  ↔ Entangled /entangled/v1/sync
  → local Rust SQLite cache
  → entities_changed
  → React Query / UI
```

App 不再维护 IndexedDB 业务主存；实体 read-model 来自 Entangled Rust cache。

## 2. 服务端写入面

```text
App action
  → Entangled action
  → Business action handler
  → Entangled entity write / Environment / Device orchestration
```

Business 是服务端产品写入方。Gateway 不写产品实体，不代理产品 entity CRUD。

## 3. Gateway App WS

Gateway App WS 保留：

- client connection registry；
- Entangled sync endpoint discovery；
- server-to-app push；
- WebRTC signaling relay。

它不负责：

- Entangled schema 首帧；
- entity sync 数据；
- `messages.send` 等产品 action；
- Device/VM 业务编排。

## 4. 一次写入 = 一次通知

Entangled 不做隐式级联订阅。Business 按产品语义显式写所需 entity；客户端订阅自己需要的 entity/read-model。

## 5. 相关

- [app-ui.md](app-ui.md)
- [service-topology.md](service-topology.md)
- [../entangled/client-ws-strategy.md](../entangled/client-ws-strategy.md)
- [../entangled/gateway-integration.md](../entangled/gateway-integration.md)

