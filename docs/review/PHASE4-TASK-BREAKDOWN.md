# Phase 4 任务分工 — 4 名工程师

> 基于 `DESIGN-P2P-UNIFIED.md`。Phase 3 已实现 relay 兜底核心逻辑，Phase 4 做模块化、策略接入与 API 完善。

---

## 一、当前状态（Phase 4 已完成）

- ✅ `connect_via_relay`、`punch_or_relay`（在 relay.rs）
- ✅ CloudBridge 处理 `connect_relay`
- ✅ P2pClient::connect 直连失败时自动 relay 兜底
- ✅ novaic-quic-service（STUN + Relay）
- ✅ Gateway relay-request、validate-device

---

## 二、Phase 4 目标

| 工程师 | 模块 | 依赖 | 预估 |
|--------|------|------|------|
| **A** | p2p relay.rs 模块化 | - | 1–2 天 |
| **B** | ConnectStrategy 接入 | - | 1 天 |
| **C** | EndpointInfo::Relay 支持 | A | 1 天 |
| **D** | P2pClient::connect_via_relay 公开 API + 配置 | A | 1 天 |

---

## 三、工程师 A：p2p relay.rs 模块化

### 3.1 产出

- 新建 `p2p/src/relay.rs`
- 从 hole_punch.rs 迁出：`RelayRole`、`connect_via_relay`、`punch_or_relay`、`parse_relay_url`、`relay_client_tls`
- hole_punch.rs 保留：`listen_for_peer`、`connect_to_peer`、`punch_and_connect`

### 3.2 任务清单

1. 创建 `relay.rs`，迁移 Relay 相关类型与函数
2. hole_punch 中 `punch_or_relay` 改为调用 `relay::punch_or_relay`
3. lib.rs 增加 `pub mod relay`，导出 `RelayRole`、`connect_via_relay`、`punch_or_relay`

### 3.3 验收

- `cargo build -p p2p` 通过
- CloudBridge、client 等调用方无需改（通过 hole_punch 或 lib re-export）

---

## 四、工程师 B：ConnectStrategy 接入

### 4.1 产出

- P2pClient::connect 根据 `config.connect_strategy` 分支

### 4.2 任务清单

1. **DirectOnly**：discovery 返回 Some 时仅 `connect_via_descriptor`，失败即返回 Err，不走 relay
2. **DirectThenRelay**：当前行为（直连失败 → punch_or_relay）
3. **RelayOnly**：跳过 discovery 直连，直接 `punch_or_relay`（内部 punch 会失败，立即走 relay）

### 4.3 验收

- 设置 `connect_strategy: DirectOnly` 时，NAT 超时后不 relay
- 设置 `RelayOnly` 时，可跳过打洞直接 relay（用于调试/强制 relay）

---

## 五、工程师 C：EndpointInfo::Relay 支持

### 5.1 产出

- `connect_via_descriptor` 收到 `EndpointInfo::Relay { relay_url, session_id }` 时调用 `connect_via_relay`

### 5.2 任务清单

1. `connect_via_descriptor` 增加 `gateway_url`、`token` 参数（Relay 分支需要 JWT）
2. 实现 `EndpointInfo::Relay` 分支：`relay::connect_via_relay(relay_url, token, session_id, RelayRole::Mobile { target_device_id })`
3. `connect()` 调用 `connect_via_descriptor` 时传入 `gateway_url`、`token`

### 5.3 验收

- 未来若 Discovery 返回 Relay 描述（如 relay-request 后构造），可正确连接

---

## 六、工程师 D：P2pClient::connect_via_relay + 配置

### 6.1 产出

- `P2pClient::connect_via_relay(relay_url, jwt, session_id, role)` 公开方法
- CloudBridge 改为调用 `P2pClient::connect_via_relay`（可选，当前直接调 hole_punch 也可）
- `NOVAIC_RELAY_URL` 环境变量支持（可选，relay_url 现由 relay-request 返回）

### 6.2 任务清单

1. 在 P2pClient 上实现 `connect_via_relay`，内部委托 `relay::connect_via_relay` ✅
2. CloudBridge 继续使用 `p2p::relay::connect_via_relay`（vmcontrol 无 P2pClient 实例）
3. `NOVAIC_RELAY_URL`：P2pClientConfig::default() 读取该环境变量填充 relay_url；punch_or_relay 接受 relay_url_override，覆盖 relay_request 返回的 relay_url ✅

### 6.3 验收

- `P2pClient::connect_via_relay` 可被外部调用
- CloudBridge 可选用统一入口（若架构允许）

---

## 七、实施顺序

```
Day 1: A（relay.rs 模块化）完成
       B（ConnectStrategy）可与 A 并行

Day 2: C（EndpointInfo::Relay）依赖 A
       D（connect_via_relay API）依赖 A
```

---

## 八、接口约定

### 8.1 relay 模块

```rust
pub enum RelayRole { Pc { device_id }, Mobile { target_device_id } }
pub async fn connect_via_relay(relay_url, jwt, session_id, role) -> Result<Connection>
pub async fn punch_or_relay(gateway_url, jwt, target_device_id, local_port, timeout, relay_url_override: Option<&str>) -> Result<Connection>
```

### 8.2 ConnectStrategy

| 策略 | 行为 |
|------|------|
| DirectOnly | 直连失败即报错，不走 relay |
| DirectThenRelay | 直连失败 → punch_or_relay |
| RelayOnly | 直接 punch_or_relay（punch 快速失败后走 relay）|
