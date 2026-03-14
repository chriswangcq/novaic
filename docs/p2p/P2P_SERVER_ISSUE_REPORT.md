# P2P Server 无法提供连接 — 诊断报告

**诊断时间**: 2026-03-12  
**参与**: 4 名 subagent（relay、vnc_proxy、tunnel、rendezvous）

---

## 一、高优先级问题

### 1.1 【最可能根因】relay.rs 中 session 错误匹配过宽

| 项目 | 说明 |
|------|------|
| **位置** | `p2p/src/relay.rs:223-226` |
| **问题** | `err_lower.contains("invalid")` 会匹配 `"Invalid JWT"`、`"Invalid handshake"` |
| **影响** | 这些并非 session 过期，但会触发 `relay_request` 刷新 session；新 session 无法解决 JWT/握手问题，导致反复刷新、浪费 session、可能触发 Gateway/relay 限流或异常 |
| **证据** | novaic-quic-service 返回 `"Invalid JWT"`（JWT 失败）、`"Invalid handshake"`（JSON 格式错误） |

### 1.2 serve_remote_vnc 仍用 spawn 移除坏连接

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_proxy.rs:317-322` |
| **问题** | `serve_remote_vnc` 用 `spawn` 异步移除坏 conn，`serve_remote_scrcpy` 已改为同步移除 |
| **影响** | 坏连接在移除前可能被并发请求复用，导致连续失败 |

### 1.3 remote_conns 锁持有时间过长

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_proxy.rs:434-472` |
| **问题** | `get_or_create_remote_conn` 在持有 `remote_conns` 锁期间执行完整 P2P connect（10–30s） |
| **影响** | 其他 VNC/Scrcpy 请求全部阻塞，易超时、级联失败 |

### 1.4 device_id 与 vmcontrol_device_id 混用

| 项目 | 说明 |
|------|------|
| **位置** | `vnc_urls.rs`, `vnc_proxy.rs` |
| **问题** | 若 URL 使用 `agent_id`（UUID）而非 `vmcontrol_device_id`（Ed25519 hex），locate/relay_request 会失败 |
| **影响** | Gateway P2P 注册表按 device_id 查找，错误 ID 导致 `online=false` 或 503 |

---

## 二、中优先级问题

### 2.1 PC 端 relay 重试使用同一 session_id

| 项目 | 说明 |
|------|------|
| **位置** | `cloud_bridge.rs:286-317` |
| **问题** | PC 收到 connect_relay 后，3 次重试都用同一个 `session_id` |
| **影响** | session 过期时重试无效，仅增加延迟 |

### 2.2 relay_request 的 body 读取失败不重试

| 项目 | 说明 |
|------|------|
| **位置** | `rendezvous.rs:269, 313` |
| **问题** | 请求返回 200 但 `resp.text().await` 失败时不会重试 |
| **影响** | 偶发网络问题可能导致拿不到 session |

### 2.3 P2P 注册表与 CloudBridge device_id 不一致

| 项目 | 说明 |
|------|------|
| **位置** | `novaic-gateway p2p.py:256-262` |
| **问题** | heartbeat 与 CloudBridge 若使用不同 device_id，`get_device` 可能为 None |
| **影响** | 503 "target device CloudBridge not connected" |

---

## 三、低优先级问题

| # | 问题 | 位置 |
|---|------|------|
| 1 | find_vnc_target 重试窗口过短（约 400ms） | tunnel.rs |
| 2 | 5s connect 超时可能偏短 | tunnel.rs |
| 3 | 15s open_bi 超时在弱网可能偏短 | tunnel.rs |
| 4 | relay 握手 open_bi 无超时 | relay.rs:98 |

---

## 四、建议修复顺序

1. **立即**：收紧 relay session 错误匹配，排除 "Invalid JWT"、"Invalid handshake"
2. **短期**：`serve_remote_vnc` 改为同步移除坏连接
3. **中期**：`get_or_create_remote_conn` 持锁优化，缩短锁持有时间
4. **验证**：确认 device_id 在 URL 与 Gateway 中一致
