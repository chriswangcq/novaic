# connect_relay 端到端流程调研（中层）

> 第二轮调研：Cloud Bridge connect_relay 流程
> 调研日期：2026-03-12

---

## 1. Gateway 如何推送 connect_relay 到 PC

### 1.1 触发入口

手机侧 VNC 请求时，`P2pClient::connect` 调用 `relay::connect_via_relay_only`，内部先执行 `rendezvous::relay_request`：

```
VncProxy → P2pClient::connect → relay::connect_via_relay_only
    → rendezvous::relay_request(gateway_url, jwt, target_device_id)
```

### 1.2 relay-request API 流程（p2p.py:232-280）

| 步骤 | 代码位置 | 行为 |
|-----|----------|------|
| 1 | p2p.py:241-246 | 校验 P2P registry：`target_device_id` 存在、归属 `user_id`、非 stale |
| 2 | p2p.py:248-254 | 生成 `session_id`，读取 `RELAY_URL` |
| 3 | p2p.py:256-263 | `registry.get_device(target_device_id)`，若 `not device.is_connected` → 503 |
| 4 | p2p.py:265-272 | `await send_push_to_device(device, "connect_relay", {relay_url, session_id})` |
| 5 | p2p.py:274-278 | 写入 `_pending_relay_sessions[session_id]`，返回 `{relay_url, session_id}` |

### 1.3 send_push_to_device 实现（pc_client.py:245-261）

```python
async def send_push_to_device(device, msg_type, payload) -> None:
    ws = device.ws
    if ws is None:
        raise ConnectionError(...)
    message = {"type": msg_type, **payload}
    async with device._send_lock:
        await ws.send_json(message)
```

- **通道**：`device.ws` 即 PC 的 CloudBridge 与 Gateway 建立的 WebSocket（`/internal/pc/ws`）
- **消息格式**：`{"type": "connect_relay", "relay_url": "...", "session_id": "uuid"}`
- **语义**：单向推送，不等待响应；`send_json` 成功表示写入 WebSocket 缓冲区，不保证 PC 已收到

### 1.4 推送路径小结

```
relay-request (HTTP POST)
    → p2p_relay_request
    → get_device_registry().get_device(target_device_id)
    → send_push_to_device(device, "connect_relay", {...})
    → device.ws.send_json({"type":"connect_relay", "relay_url":..., "session_id":...})
    → WebSocket 帧发往 PC CloudBridge
```

---

## 2. cloud_bridge.rs 收到消息后的处理

### 2.1 消息解析（cloud_bridge.rs:250-259）

WebSocket 收到 Text 帧后，反序列化为 `IncomingMessage`：

```rust
#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum IncomingMessage {
    ConnectRelay { relay_url: String, session_id: String },
    // ...
}
```

### 2.2 ConnectRelay 分支（cloud_bridge.rs:279-323）

```rust
IncomingMessage::ConnectRelay { relay_url, session_id } => {
    // 使用最新 token（长连接下 JWT 可能已刷新）
    let jwt = cloud_token.read().await.clone();
    let did = device_id.to_string();
    let base = vmcontrol_base_url.to_string();
    tokio::spawn(async move {
        let mut last_err = None;
        for attempt in 1..=3 {
            match p2p::relay::connect_via_relay(
                &relay_url, &jwt, &session_id,
                p2p::relay::RelayRole::Pc { device_id: did.clone() },
            ).await {
                Ok(conn) => {
                    p2p::tunnel::run_tunnel_server(conn, base).await;
                    return;
                }
                Err(e) => {
                    last_err = Some(e.to_string());
                    if attempt < 3 {
                        tokio::time::sleep(Duration::from_millis(500 * attempt)).await;
                        // retry
                    }
                }
            }
        }
        tracing::warn!("connect_via_relay failed after 3 attempts: ...");
    });
    continue;
}
```

### 2.3 处理要点

| 项目 | 说明 |
|------|------|
| **JWT** | 从 `cloud_token.read().await` 读取最新 token，避免长连接下 JWT 过期 |
| **异步** | `tokio::spawn` 立即返回，不阻塞主消息循环 |
| **重试** | 失败时 500ms、1000ms 间隔重试，共 3 次 |
| **成功路径** | `connect_via_relay` 成功 → `run_tunnel_server(conn, vmcontrol_base_url)` 处理后续 stream |

---

## 3. relay_request 与 relay 建立的时序

### 3.1 整体时序图

```
时间轴    手机 (Mobile)                    Gateway                         PC (CloudBridge)              Relay
─────────────────────────────────────────────────────────────────────────────────────────────────────────────
T0       POST /api/p2p/relay-request ────>
T0                                         校验 P2P registry
T0                                         生成 session_id
T0                                         get_device(target_device_id)
T0                                         send_push(connect_relay) ─────────────────────────────────────>
T0       <──── 200 {relay_url, session_id}
T0+δ                                                                     收到 WS 消息
T0+δ                                                                     spawn connect_via_relay
T0+δ                                                                     QUIC connect ─────────────────────────>
T0+δ                                                                     open_bi, 发 RegisterPc JSON
T0+δ                                                                     <───────────────────────── 200 OK
T0+δ                                                                     RegisterPc 完成，pc_registry[session_id]=conn

T0+ε     connect_via_relay_only 内部：
         (首次尝试无固定延迟，relay_request 返回后立即 connect_via_relay)
T0+ε     connect_via_relay ─────────────────────────────────────────────────────────────────────────────>
T0+ε     (ConnectRequest: target_device_id, jwt, session_id)
T0+ε                                                                      Relay: validate session
T0+ε                                                                      Relay: 轮询 pc_registry 取 PC conn
T0+ε                                                                      (最多等 10s, 300ms 轮询)
T0+ε     <──────────────────────────────────────────────────────────────────────────── 200 OK
T0+ε     forward_streams: 手机 ↔ PC 双向转发
```

### 3.2 关键时序

| 事件 | 顺序 | 说明 |
|------|------|------|
| relay-request 返回 | 1 | Gateway 在 `send_push` 成功后才返回；手机拿到 session_id |
| PC 收到 connect_relay | 2 | WebSocket 推送，通常 0–500ms 延迟 |
| PC RegisterPc | 3 | 需完成：DNS、QUIC 握手、open_bi、发 JSON、收响应 |
| 手机 connect_via_relay | 4 | `connect_via_relay_only` 无固定延迟，可立即连；失败时 2s/4s/8s 重试 |

### 3.3 Relay 端配对逻辑（novaic-quic-service/relay.rs）

- **RegisterPc**（PC 先到）：写入 `pc_registry[session_id] = PcEntry { conn, registered_at }`，SESSION_TTL=10s
- **ConnectRequest**（手机后到）：轮询 `pc_registry.remove(session_id)`，最多等 10s、300ms 轮询；取到则配对，取不到则返回 "PC offline or session expired"

### 3.4 竞态与缓解

- **竞态**：手机可能在 PC RegisterPc 完成前发起 ConnectRequest
- **缓解**：Relay 端「长等待」10s；手机端 4 次尝试、2/4/8s 退避；PC 端 3 次重试、500ms×attempt

---

## 4. connect_relay 端到端流程（汇总）

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. 手机发起 relay                                                                                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
   VncProxy
      │
      ▼
   P2pClient::connect(gateway_url, token, target_device_id)
      │
      ▼
   relay::connect_via_relay_only
      │
      ├─► rendezvous::relay_request(gateway_url, jwt, target_device_id)
      │       │
      │       ▼
      │   POST /api/p2p/relay-request  { target_device_id }
      │       │
      │       ▼
      │   ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
      │   │ 2. Gateway 处理 relay-request                                                                 │
      │   └─────────────────────────────────────────────────────────────────────────────────────────────┘
      │       p2p.py: p2p_relay_request
      │         • 校验 P2P registry
      │         • session_id = uuid4()
      │         • device = registry.get_device(target_device_id)
      │         • if not device.is_connected → 503
      │         • await send_push_to_device(device, "connect_relay", {relay_url, session_id})
      │         • _pending_relay_sessions[session_id] = ...
      │         • return { relay_url, session_id }
      │       │
      │       ▼
      │   pc_client.py: send_push_to_device
      │         • message = {"type":"connect_relay", "relay_url":..., "session_id":...}
      │         • await device.ws.send_json(message)
      │       │
      │       ▼
      │   WebSocket 帧 → PC CloudBridge
      │
      ◄── { relay_url, session_id }
      │
      ▼
   connect_via_relay(relay_url, jwt, session_id, RelayRole::Mobile)
      │   (失败时 2s/4s/8s 重试，最多 4 次)
      │
      ▼
   Relay 服务：ConnectRequest → 配对 PC → forward_streams

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. PC 收到 connect_relay                                                                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
   CloudBridge WebSocket 主循环 (cloud_bridge.rs)
      │
      ▼
   IncomingMessage::ConnectRelay { relay_url, session_id }
      │
      ▼
   tokio::spawn(async {
       jwt = cloud_token.read().await.clone();
       for attempt in 1..=3 {
           conn = connect_via_relay(relay_url, jwt, session_id, RelayRole::Pc { device_id });
           if Ok(conn) => run_tunnel_server(conn, vmcontrol_base_url);
       }
   })
      │
      ▼
   p2p::relay::connect_via_relay
      • QUIC connect(relay host:443)
      • open_bi()
      • 发送 RegisterPc { device_id, jwt, session_id } + "\n"
      • 读取 ConnectResponse
      │
      ▼
   Relay 服务：RegisterPc → pc_registry[session_id] = conn
      │
      ▼
   run_tunnel_server(conn, base)
      • 循环 accept_bi，处理 VNC/scrcpy stream
```

---

## 5. 文件索引

| 组件 | 文件 | 职责 |
|------|------|------|
| Gateway relay-request | `novaic-gateway/gateway/api/p2p.py` | 校验、推送、返回 session |
| Gateway 推送实现 | `novaic-gateway/gateway/api/internal/pc_client.py` | send_push_to_device, DeviceRegistry |
| CloudBridge | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | 解析 ConnectRelay，spawn connect_via_relay |
| PC relay 建连 | `novaic-app/src-tauri/p2p/src/relay.rs` | connect_via_relay(RelayRole::Pc) |
| 手机 relay 建连 | `novaic-app/src-tauri/p2p/src/relay.rs` | connect_via_relay_only → relay_request + connect_via_relay(Mobile) |
| relay_request HTTP | `novaic-app/src-tauri/p2p/src/rendezvous.rs` | relay_request() |
| Relay 服务 | `novaic-quic-service/src/relay.rs` | RegisterPc、ConnectRequest、配对、forward_streams |
