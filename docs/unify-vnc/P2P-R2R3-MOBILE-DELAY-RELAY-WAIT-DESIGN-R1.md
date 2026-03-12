# P2P 竞态修复 Round 1 设计：R2/R3 手机立即 connect vs PC 建连耗时、Relay 10s 不足

**设计轮次**: Round 1  
**范围**: R2（手机立即连接 vs PC 建连耗时）、R3（Relay 等待 PC 时间窗不足）  
**参考**: `P2P-RACE-DESIGN-CONVENTIONS.md`、`P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md`

---

## 1. 问题陈述

### 1.1 时序竞态

```
Mobile (VNC)                    Gateway                     PC (CloudBridge)              Relay
     |                              |                              |                        |
     |  POST /relay-request         |                              |                        |
     |  ───────────────────────────>|                              |                        |
     |                              |  send_push(connect_relay)     |                        |
     |                              |  ───────────────────────────>|                        |
     |  {relay_url, session_id}     |  (await 完成 = 写入 WS 缓冲)   |  spawn connect_via_relay|
     |  <───────────────────────────|                              |  QUIC + RegisterPc     |
     |                              |                              |  ─────────────────────>|
     |  connect_via_relay           |                              |                        |
     |  (ConnectRequest) 立即发起     |                              |                        |
     |  ─────────────────────────────────────────────────────────────────────────────────>|
     |                              |                              |                        |
     |  RACE: PC 未 RegisterPc 时手机已 ConnectRequest → "PC offline or session expired"
```

### 1.2 根因

| 竞态点 | 说明 |
|--------|------|
| **R2** | 手机 `relay_request` 返回后**立即** `connect_via_relay`，无固定延迟。PC 需完成：收推送 → 解析 → spawn → DNS → QUIC 握手(30s) → RegisterPc。慢网下 5–15s 常见。 |
| **R3** | Relay 对 ConnectRequest 轮询等待 PC 最多 **10s**（`WAIT_FOR_PC_TIMEOUT`）。若 PC 建连超过 10s，返回 "PC offline or session expired"。 |

### 1.3 当前配置

| 组件 | 常量 | 当前值 | 文件 |
|------|------|--------|------|
| Relay | `WAIT_FOR_PC_TIMEOUT` | 10s | `novaic-quic-service/src/relay.rs:223` |
| Relay | `SESSION_TTL` | 10s | `novaic-quic-service/src/relay.rs:25` |
| Gateway | `_PENDING_SESSION_TTL_SECS` | 10s | `novaic-gateway/gateway/api/p2p.py:70` |
| 手机 | 首次 connect 延迟 | 0s（立即） | `novaic-app/src-tauri/p2p/src/relay.rs:181` |
| 手机 | `HANDSHAKE_READ_TIMEOUT_SECS` | 40s | `novaic-app/src-tauri/p2p/src/relay.rs:117` |

### 1.4 缺口

- PC 建连慢网 5–15s，Relay 仅等 10s → 易失败
- Gateway / Relay session TTL 均为 10s，与 WAIT_FOR_PC_TIMEOUT 一致，但 PC 建连若超过 10s，session 已失效
- 手机无首包延迟，依赖 Relay 10s 等待；若 PC 建连 12s，手机 T+0 即 ConnectRequest，Relay 等 10s 后 PC 仍未到 → 失败

---

## 2. 方案设计

### 2.1 手机侧短延迟

**目标**：给 PC 更多时间收推送、spawn、完成 QUIC 握手，减少「手机先到、PC 未到」的概率。

**改动**：`novaic-app/src-tauri/p2p/src/relay.rs` 中 `connect_via_relay_only`，在 `relay_request` 返回后、首次 `connect_via_relay` 调用前增加固定延迟。

```rust
// relay.rs connect_via_relay_only 内，relay_request 返回后
const INITIAL_DELAY_SECS: u64 = 2;  // 新增：给 PC 收推送 + spawn 的缓冲
// ...
let relay_resp = crate::rendezvous::relay_request(...).await?;
// ...
tokio::time::sleep(Duration::from_secs(INITIAL_DELAY_SECS)).await;  // 首次尝试前延迟
for attempt in 1..=4 {
    match connect_via_relay(...).await { ... }
}
```

**取值**：2s。理由：推送通常 0.5–2s 内到达，2s 可覆盖大部分正常网络；过长会拉高用户感知延迟。

### 2.2 Relay WAIT_FOR_PC_TIMEOUT 调整

**目标**：覆盖慢网下 PC 建连 5–15s 的典型耗时。

**改动**：`novaic-quic-service/src/relay.rs`

```rust
// 原
const WAIT_FOR_PC_TIMEOUT: Duration = Duration::from_secs(10);

// 改
const WAIT_FOR_PC_TIMEOUT: Duration = Duration::from_secs(20);
```

**取值**：20s。理由：慢网 5–15s + 手机 2s 延迟后，20s 可覆盖绝大多数场景；QUIC 连接超时 30s，20s 仍在合理范围内。

### 2.3 Session TTL 对齐

**目标**：Gateway、Relay 的 session 有效期 ≥ WAIT_FOR_PC_TIMEOUT，避免「PC 建连成功但 session 已过期」。

**改动 1**：`novaic-gateway/gateway/api/p2p.py`

```python
# 原
_PENDING_SESSION_TTL_SECS = 10

# 改
_PENDING_SESSION_TTL_SECS = 20
```

**改动 2**：`novaic-quic-service/src/relay.rs`

```rust
// 原
const SESSION_TTL: Duration = Duration::from_secs(10);

// 改
const SESSION_TTL: Duration = Duration::from_secs(20);
```

**对齐原则**：三者保持一致：`WAIT_FOR_PC_TIMEOUT == SESSION_TTL (Relay) == _PENDING_SESSION_TTL_SECS (Gateway) == 20s`。

### 2.4 手机 HANDSHAKE_READ_TIMEOUT 校验

**现状**：`HANDSHAKE_READ_TIMEOUT_SECS = 40`，覆盖 `INITIAL_DELAY(2) + QUIC(30) + WAIT_FOR_PC(20)` 仍有余量。

**结论**：无需修改。

---

## 3. 接口变更

**无**。所有改动为内部常量与逻辑，不涉及：

- HTTP API（`/api/p2p/relay-request` 等）
- WebSocket 消息格式（`connect_relay`）
- Relay QUIC 握手协议（RegisterPc / ConnectRequest JSON）

---

## 4. 风险与回退

### 4.1 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| 手机 2s 延迟增加用户等待 | 用户点击 VNC 后多等 2s | 2s 为可接受 UX；失败重试时无此延迟（重试间隔 2/4/8s 已存在） |
| Relay 20s 等待增加资源占用 | 每个 ConnectRequest 最多持有一个 pending 连接 20s | 单 session 单连接，影响有限；可后续监控 |
| Gateway session 20s 增加内存 | `_pending_relay_sessions` 条目存活更久 | 条目数量 = 并发 relay_request 数，通常很小 |

### 4.2 回退策略

- 所有改动均为常量，回退只需还原数值：
  - `INITIAL_DELAY_SECS`: 2 → 0（或移除该 sleep）
  - `WAIT_FOR_PC_TIMEOUT`: 20 → 10
  - `SESSION_TTL` (Relay): 20 → 10
  - `_PENDING_SESSION_TTL_SECS`: 20 → 10
- 建议通过 feature flag 或环境变量控制 `INITIAL_DELAY_SECS`，便于 A/B 或快速关闭。

### 4.3 兼容性

- 新旧版本混跑：Gateway 20s TTL 与 Relay 20s 一致，旧手机（无延迟）连接新 Relay 仍可工作；新手机 2s 延迟仅改善成功率。
- 部署顺序：建议 Gateway → Relay → 手机 App 依次发布，或同时发布（无强依赖）。

---

## 5. 实施顺序

| 步骤 | 任务 | 依赖 | 预估 |
|------|------|------|------|
| 1 | Gateway `_PENDING_SESSION_TTL_SECS` 10→20 | 无 | 5min |
| 2 | novaic-quic-service `WAIT_FOR_PC_TIMEOUT`、`SESSION_TTL` 10→20 | 无 | 5min |
| 3 | novaic-app `connect_via_relay_only` 增加 `INITIAL_DELAY_SECS=2` | 1、2 部署后效果更佳，但非强依赖 | 10min |

**建议**：1、2 可并行；3 在 1、2 合并后实施。全部完成后做慢网模拟测试（如 tc 限速）验证。

---

## 附录：相关代码位置

| 组件 | 文件 | 关键行 |
|------|------|--------|
| 手机 relay 连接 + 重试 | `novaic-app/src-tauri/p2p/src/relay.rs` | 155–239 |
| Relay 服务端 | `novaic-quic-service/src/relay.rs` | 25, 222–239 |
| Gateway relay session | `novaic-gateway/gateway/api/p2p.py` | 70, 274–279, 283–304 |
