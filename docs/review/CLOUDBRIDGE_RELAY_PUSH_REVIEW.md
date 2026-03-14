# CloudBridge & Gateway Push Flow Review: connect_relay

> Focus: Mobile VNC intermittent "连接被对方重置" (connection reset by peer)
> Review date: 2026-03-11

---

## Executive Summary

The "连接被对方重置" error occurs when the VNC WebSocket is dropped after `connect_via_relay` fails. Root causes span five areas: **relay-request push timing**, **DeviceRegistry connection state**, **send_push delivery semantics**, **CloudBridge reconnect/JWT handling**, and **JWT expiration**. Several issues can cause intermittent failures.

---

## 1. Gateway relay-request API — When does it push connect_relay to PC?

### Flow (p2p.py:214–258)

```
relay-request(req) →
  1. Validate P2P registry (entry exists, user_id, not stale)
  2. Generate session_id
  3. registry.get_device(target_device_id)
  4. if not device.is_connected → 503
  5. await send_push_to_device(device, "connect_relay", {...})
  6. return RelayRequestResponse(relay_url, session_id)
```

### Is it async?

- **Yes, but blocking**: `await send_push_to_device(...)` blocks until the send completes.
- If `send_push` raises, the handler catches and returns HTTP 503.
- The HTTP response is only sent **after** the push is sent (or fails).

### Could the push fail silently?

| Scenario | Behavior |
|----------|----------|
| `device.ws` is None | `send_push` raises `ConnectionError` → 503 to phone |
| `ws.send_json()` raises | Exception propagates → 503 to phone |
| `ws.send_json()` succeeds, PC disconnects before receiving | **Silent loss**: TCP buffers the send; Gateway sees success; PC never gets the message |

**Conclusion**: Push can be **lost silently** when the PC disconnects (or is about to disconnect) right after the Gateway sends. The Gateway treats success as "send didn't throw", not "PC received".

---

## 2. DeviceRegistry.is_connected — When is PC considered "connected"?

### Definition (pc_client.py:46–47)

```python
@property
def is_connected(self) -> bool:
    return self.ws is not None
```

### When does `ws` become None?

- In `disconnect(ws, device_id)`: when the WebSocket receive loop exits (`WebSocketDisconnect` or exception), `registry.disconnect()` sets `device.ws = None`.

### Could CloudBridge disconnect briefly?

**Yes.** CloudBridge disconnects in these cases:

| Trigger | Location | Effect |
|---------|----------|--------|
| Read timeout 90s | cloud_bridge.rs:211–214 | No message in 90s → return → reconnect after 5s |
| Server close | cloud_bridge.rs:224 | `Message::Close` → return |
| WebSocket error | cloud_bridge.rs:226 | Network error → return |
| Stream end | cloud_bridge.rs:217 | `Ok(None)` → return |

**Reconnect sequence**:

1. `connect_and_run` returns.
2. Main loop sleeps 5 seconds.
3. New `connect_and_run` with fresh token.
4. During steps 1–3, the old WebSocket is closed → Gateway `receive_json()` raises → `disconnect()` → `device.ws = None`.

So for **at least 5 seconds** after a disconnect, `is_connected` is False. Any `relay-request` in that window gets 503.

**Reconnect race (same device_id)**:

- When PC reconnects, `registry.connect()` runs:
  - Closes old `device.ws` (if any).
  - Sets `device.ws = new_ws`.
- If the old connection’s `disconnect()` runs later, it checks `device.ws is old_ws`. If `device.ws` is already the new socket, it does nothing (correct).
- Brief window: between closing the old WS and setting `device.ws = new_ws`, `is_connected` could be False. This is inside a single `connect()` call, so the window is very short.

**Conclusion**: CloudBridge can disconnect for 5+ seconds on timeout/error. During that time, `relay-request` returns 503. There is no brief "flicker" of disconnect during a normal reconnect of the same device.

---

## 3. send_push_to_device — How does it work? Could push be lost?

### Implementation (pc_client.py:214–229)

```python
async def send_push_to_device(device, msg_type, payload) -> None:
    ws = device.ws
    if ws is None:
        raise ConnectionError(...)
    message = {"type": msg_type, **payload}
    async with device._send_lock:
        await ws.send_json(message)
    logger.debug(...)
```

### Behavior

- **Fire-and-forget**: No ack, no retry.
- **Lock**: Shares `_send_lock` with `forward_to_device` and `send_control_to_device`.
- **Success**: `ws.send_json()` returns without error.

### Could push be lost?

| Case | Result |
|------|--------|
| PC disconnects before send | `ws.send_json()` may raise → 503 to phone |
| PC disconnects right after send | Data may be buffered in TCP; send "succeeds"; PC never receives → **silent loss** |
| Long `forward_to_device` holds `_send_lock` | `send_push` blocks until lock free; push delayed but not lost |
| `send_json` succeeds, connection dies before delivery | **Silent loss** |

**Conclusion**: Push can be lost when the connection is flaky or the PC disconnects around the send. There is no delivery guarantee or retry.

---

## 4. CloudBridge WebSocket — connect_relay handling

### Flow (cloud_bridge.rs:260–285)

```rust
IncomingMessage::ConnectRelay { relay_url, session_id } => {
    let jwt = token.to_string();   // ← token from connect_and_run parameter
    let did = device_id.to_string();
    let base = vmcontrol_base_url.to_string();
    tokio::spawn(async move {
        match p2p::relay::connect_via_relay(&relay_url, &jwt, &session_id, ...).await {
            Ok(conn) => ...
            Err(e) => tracing::warn!("[CloudBridge] connect_via_relay failed: {}", e);
        }
    });
    continue;
}
```

### Token source

- `token` is the argument to `connect_and_run(..., token, ...)`.
- It is set once at connection start (line 137): `let current_token = config.cloud_token.read().await.clone()`.
- It is **not** updated when handling `connect_relay`.

### Reconnect race

- On disconnect, `connect_and_run` returns.
- After 5s sleep, a new connection is established with a fresh token.
- During reconnect, there is no WebSocket connection, so no `connect_relay` can be received.

### Race when reconnect completes

- **Scenario**: CloudBridge disconnects, reconnects, and receives `connect_relay` shortly after.
- **Issue**: The new connection uses a fresh token at connect time, but the token is passed by value into `connect_and_run`. For long-lived connections, the token is never refreshed inside the loop.
- **Conclusion**: No race specific to reconnect; the main issue is **stale token** during long sessions.

---

## 5. JWT Token — Could token expire during long CloudBridge session?

### Current behavior

- CloudBridge uses the token passed at connect time for the entire session.
- `connect_relay` uses `token.to_string()` — the same snapshot.
- `cloud_token` is refreshed every 45s by the frontend (per `CloudBridgeConfig`), but CloudBridge does not re-read it when handling `connect_relay`.

### When does it matter?

- Clerk JWT expiry: typically short (e.g. 60s).
- If the CloudBridge connection stays up for hours, the token used for `connect_relay` can be expired.
- Relay validates JWT via `auth::validate_jwt_and_device`; if it fails, the relay returns `"Invalid JWT"` and closes the stream.

### Effect on relay

- PC sends `RegisterPc { device_id, jwt, session_id }`.
- Relay calls `validate_jwt_and_device(gateway_url, jwt, device_id)`.
- If JWT is expired → `send_response(..., ConnectResponse::failure("Invalid JWT"))` → PC’s `connect_via_relay` fails.
- Mobile sees `"PC offline or session expired"` or similar when it connects later.

**Conclusion**: Yes, expired JWT can cause relay failures and contribute to "连接被对方重置".

---

## 6. Root Cause Summary for "连接被对方重置"

| # | Cause | Likelihood | Notes |
|---|--------|------------|-------|
| 1 | **PC–mobile relay race** | High | Mobile connects before PC registers; relay returns "PC offline or session expired". Mitigated by 2s delay + retries 2s/4s/8s, but still possible under load. |
| 2 | **JWT expired** | Medium | Long CloudBridge sessions use stale token; relay rejects RegisterPc. |
| 3 | **Push lost** | Medium | Gateway sends push; PC disconnects or network blip; message never received. |
| 4 | **CloudBridge disconnected** | Low | 5s reconnect window; relay-request returns 503, not silent. |
| 5 | **Session expired** | Low | Relay SESSION_TTL 120s; PC must register within 2 minutes. |

---

## 7. Recommended Fixes

### High priority

1. **CloudBridge: use fresh token for connect_relay**  
   `connect_and_run` needs access to `CloudBridgeConfig` (or at least `cloud_token`). When handling `ConnectRelay`, read `config.cloud_token.read().await.clone()` instead of using the `token` parameter.

2. **Relay race: increase initial delay or retries**  
   If 2s + 3 retries is still insufficient, consider:
   - Increasing `INITIAL_DELAY_SECS` (e.g. 3s).
   - Adding one more retry.

### Medium priority

3. **Push delivery guarantee**  
   - Option A: Add acknowledgment: `connect_relay_ack` from PC to Gateway; Gateway only returns relay_url/session_id to phone after ack (or timeout).
   - Option B: Retry push if Gateway does not receive ack within N seconds.

4. **Logging**  
   - Gateway: log when `send_push` succeeds; consider a separate log when PC disconnects shortly after.
   - CloudBridge: log token age or JWT expiry when `connect_via_relay` fails.

### Low priority

5. **Session TTL**  
   - If 120s is too short for slow networks, consider increasing `SESSION_TTL`.

---

## 8. File Reference

| File | Purpose |
|------|---------|
| `novaic-gateway/gateway/api/p2p.py` | relay-request, send_push_to_device call |
| `novaic-gateway/gateway/api/internal/pc_client.py` | DeviceRegistry, send_push_to_device, is_connected |
| `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | connect_relay handling, token usage |
| `novaic-app/src-tauri/p2p/src/relay.rs` | punch_or_relay, connect_via_relay, retry logic |
| `novaic-quic-service/src/relay.rs` | RegisterPc, ConnectRequest, JWT validation |
