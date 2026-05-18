# 协议层：PubSub、协商验证与 Headless WebSocket

> 路径参考：`Entangled/packages/server-python/entangled/server/`

## 1. 层级定位
`entangled.server` 作为核心协议层，它是严谨的心智基石。它**不关心底层通过什么存储**（内存、SQL 还是 NoSQL），只定义通信法则。

## 2. 核心抽象（`EntityStoreProtocol`）
采用鸭子类型抽象的 `EntityStoreProtocol(ABC)` 提供 6 项泛型约定：
- `list(entity_type, user_id, ...)`
- `get(entity_type, user_id, entity_id)`
- `create(entity_type, user_id, params)`
- `update(...)`
- `upsert(...)` — create-or-update 语义，用于首次可能不存在的固定形态实体（如 agent-binding）
- `delete(...)`

所有的业务类必须满足协议要求，`gw_store` 会继承这些规则。由于实现了高维度的依赖反转，`entangled.server.notifier` 完全不知道下面跑的是数据库逻辑，只要能调用即可进行全局广播。

## 3. WS Handler 与 协商准则 (`ws_handler.py`)
WebSocket 连接时不仅仅只是发数据，它包含完整的**协商**阶段：
- **`SYNC_CONTRACT_VERSION`**：一个标志整数，用于网关向客户端（Tauri）声明“我能支持的 Entangled 同步行为基线”。当客户端判定过低时，强制 fallback 或记录日志 `metric=sync_frame_missing_id_field_v2`。
- **Capabilities (能力暴露)**：协议层会在服务端主动下发可信数据类型，告知 Rust Client 这台服务器能否支持如 `listStream` 或带事务条件的 `upsert`，避免端侧发瞎包。
- Duck-Typing 解析：服务端 `ws_handler` 有一个极妙的反射：如果它测出传入的 Store 上下文有 `exists_before()` 等方法，那么这层协议就能毫无侵入地打通“从某偏移量追赶聊天流水”的复杂历史回放。
