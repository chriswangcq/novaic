# Entangled 与 Gateway 的当前边界

Gateway 现在不是 Entangled 的宿主、HTTP client、schema authority 或 action owner。

## 当前职责

```text
App → Gateway /api/app/ws
    ← entangledWsUrl

App ↔ Entangled /entangled/v1/sync

Business → Entangled HTTP/schema/action writes
Entangled → Business action hook callbacks
```

| 组件 | Entangled 相关职责 |
|---|---|
| **Gateway** | 只负责把客户端应该连接的 `entangledWsUrl` 下发给 App |
| **Business** | 服务端 entity/action 写入方，schema push 方，action hook 处理方 |
| **Entangled** | 实体存储、schema/action 注册、direct sync WS |
| **App** | 通过 Entangled Rust client 订阅实体并使用本地 SQLite cache |

## 明确禁止的旧理解

- Gateway 不拥有任何产品实体 store。
- Gateway 不拥有 `EntangledServiceClient`。
- Gateway 不代理产品 entity CRUD。
- Gateway App WS 不承载 entity sync 或 schema 首帧。

历史上 Gateway 曾承担过 Entangled 胶水职责；这些路径已经退役，不应作为当前设计依据。
