# P2P Relay Connection Race Analysis

**Issue**: Mobile VNC WebSocket to `ws://127.0.0.1:58545/vnc/{device_id}/{agent_id}` fails with "连接被对方重置" (connection reset by peer). Success rate very low ("随机能连上 几率很低").

## Executive Summary

The relay flow has a **critical race condition**: the mobile gets `session_id` immediately from the HTTP response, while the PC receives `connect_relay` via WebSocket push. The mobile waits only **2 seconds** before its first `connect_via_relay` attempt. The PC often needs **5–15+ seconds** to complete QUIC connect + RegisterPc (DNS, TLS handshake, network latency). When the mobile connects before the PC has registered, the relay returns "PC offline or session expired" and closes the connection → user sees "连接被对方重置".

---

## 1. Flow Overview

```
Mobile (VNC request)                    Gateway                     PC (CloudBridge)
        |                                    |                              |
        |  punch_and_connect (15s timeout)   |                              |
        |  ─────────────────────────────────>|                              |
        |  (fails)                           |                              |
        |                                    |                              |
        |  POST /api/p2p/relay-request       |                              |
        |  ─────────────────────────────────>|                              |
        |                                    |  send_push(connect_relay)    |
        |                                    |  ───────────────────────────>|
        |  {relay_url, session_id}          |                              |  spawn connect_via_relay
        |  <─────────────────────────────────|                              |  (QUIC + RegisterPc)
        |                                    |                              |
        |  sleep 2s                          |                              |
        |  connect_via_relay (ConnectRequest) |                              |
        |  ──────────────────────────────────────────────────────────────> Relay
        |                                    |                              |
        |  RACE: If PC not yet registered → "PC offline" → connection reset
```

---

## 2. Code Analysis

### 2.1 `punch_or_relay` (p2p/src/relay.rs)

```rust:199:234:novaic-app/src-tauri/p2p/src/relay.rs
    // 竞态：手机先拿到 session_id，PC 收到 connect_relay 推送后需时间 RegisterPc。
    // 首次尝试前等待 2s，给 Gateway 推送 + PC 建连时间；失败时再重试（2s/4s/8s 指数退避）。
    const INITIAL_DELAY_SECS: u64 = 2;
    const RETRY_DELAYS: [u64; 3] = [2, 4, 8]; // 3 次重试，共 4 次尝试
```

**Problem**: 2 seconds is insufficient. PC must:
1. Receive WebSocket push (network latency)
2. Parse ConnectRelay
3. Spawn `connect_via_relay` task
4. DNS resolve relay host
5. QUIC connect (30s timeout in relay.rs:85)
6. `open_bi()`, send RegisterPc JSON, read response (15s handshake timeout)

On mobile/slow networks, steps 4–6 alone can take 5–15 seconds.

### 2.2 `connect_via_relay` Handshake (relay.rs:49–150)

- **QUIC connect timeout**: 30s (line 85)
- **Handshake response timeout**: 15s (line 119) — reading response byte-by-byte
- **Response parsing**: Expects `{"ok":true}` or `{"ok":false,"error":"..."}`

When relay returns `{"ok":false,"error":"PC offline or session expired"}`, the handler then returns and drops the connection. The client may see "connection reset" if the QUIC connection is closed before the response is fully processed.

### 2.3 `relay_request` vs `connect_relay` Ordering (Gateway)

**Gateway** (`novaic-gateway/gateway/api/p2p.py:246–258`):

```python
await send_push_to_device(device, "connect_relay", {"relay_url": relay_url, "session_id": session_id})
return RelayRequestResponse(relay_url=relay_url, session_id=session_id)
```

- Gateway **awaits** `send_push_to_device` before returning.
- `send_push_to_device` = `await ws.send_json(message)` — completes when message is **written to the WebSocket buffer**, not when PC has received/processed it.
- So: mobile gets `session_id` only after push is sent, but PC may not have received or processed it yet.

### 2.4 novaic-quic-service Relay Handler (relay.rs)

**Strict ordering**: PC must RegisterPc **before** mobile ConnectRequest.

```rust:193:206:novaic-quic-service/src/relay.rs
        let pc_conn = pc_registry.write().await.remove(&req.session_id);
        let pc_conn = match pc_conn {
            Some(entry) => { ... }
            None => {
                send_response(&mut send, &ConnectResponse::failure("PC offline or session expired")).await?;
                return Ok(());
            }
        };
```

- If `session_id` not in registry → failure response, handler returns, connection dropped.
- No "wait for PC" logic — mobile gets immediate rejection.

### 2.5 CloudBridge ConnectRelay Handling (cloud_bridge.rs:260–285)

```rust
IncomingMessage::ConnectRelay { relay_url, session_id } => {
    let jwt = token.to_string();  // ⚠️ Uses token snapshot — may be stale (JWT expiry)
    tokio::spawn(async move {
        match p2p::relay::connect_via_relay(...).await {
            Ok(conn) => { run_tunnel_server(conn, base).await; }
            Err(e) => { tracing::warn!("[CloudBridge] connect_via_relay failed: {}", e); }
        }
    });
    continue;
}
```

- **Fire-and-forget spawn**: No back-pressure, no urgency.
- **Token**: Uses `token` from `connect_and_run` — long-lived connections may have expired JWT (see P2P-SUBAGENT-FIX-LIST).

---

## 3. Identified Issues

| # | Issue | Location | Severity |
|---|-------|----------|----------|
| 1 | **Initial delay too short** | relay.rs:201 `INITIAL_DELAY_SECS=2` | **High** |
| 2 | **PC connect_via_relay not prioritized** | CloudBridge spawns async, no urgency | Medium |
| 3 | **Relay has no "wait for PC"** | novaic-quic-service: immediate reject if PC not registered | Medium |
| 4 | **Gateway returns before PC acks** | Push "sent" ≠ PC received/processed | Medium |
| 5 | **JWT may be stale in ConnectRelay** | cloud_bridge uses token snapshot | Low |
| 6 | **Response parsing on connection close** | Mobile may get reset before reading full JSON | Low |

---

## 4. Recommendations

### 4.1 Immediate: Increase Initial Delay (High Impact)

**File**: `novaic-app/src-tauri/p2p/src/relay.rs`

```rust
// Change from 2 to 5–8 seconds
const INITIAL_DELAY_SECS: u64 = 6;  // or 8 for very slow networks
```

Rationale: Gives PC time for DNS + QUIC handshake + RegisterPc on typical networks.

### 4.2 Extend Retry Schedule (Medium Impact)

```rust
// More attempts, longer delays
const RETRY_DELAYS: [u64; 5] = [3, 5, 8, 12, 20];  // 6 total attempts, ~48s total
```

### 4.3 CloudBridge: Use Fresh Token (Low–Medium)

**File**: `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs`

Pass `cloud_token: Arc<RwLock<String>>` into `connect_and_run` and read fresh token in ConnectRelay branch:

```rust
let token = config.cloud_token.read().await.clone();
```

### 4.4 Relay: Optional "Wait for PC" (Design Change)

Allow relay to hold a ConnectRequest and wait (e.g. 30s) for RegisterPc before rejecting. Requires protocol/relay changes.

### 4.5 Gateway: Consider Delaying Response (Complex)

Only return `relay_url`/`session_id` after PC has acknowledged connect_relay. Would need new message type and PC→Gateway ack.

---

## 5. Timeline (Typical Failure Case)

| Time | Mobile | PC |
|------|--------|-----|
| T+0 | relay_request returns, gets session_id | — |
| T+0 | — | Receives WebSocket push (0–500ms latency) |
| T+0.5 | — | Spawns connect_via_relay |
| T+2 | First connect_via_relay attempt | Still in QUIC connect / handshake |
| T+2 | Relay: session_id not found → "PC offline" | — |
| T+2 | Connection reset / failure | — |
| T+5 | — | RegisterPc completes (too late) |

---

## 6. Files Reference

| Component | File |
|-----------|------|
| punch_or_relay, connect_via_relay | `novaic-app/src-tauri/p2p/src/relay.rs` |
| relay_request | `novaic-app/src-tauri/p2p/src/rendezvous.rs` |
| Gateway relay-request, send_push | `novaic-gateway/gateway/api/p2p.py`, `internal/pc_client.py` |
| Relay handler (RegisterPc, ConnectRequest) | `novaic-quic-service/src/relay.rs` |
| CloudBridge ConnectRelay | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` |
| VncProxy get_or_create_remote_conn | `novaic-app/src-tauri/src/vnc_proxy.rs` |
