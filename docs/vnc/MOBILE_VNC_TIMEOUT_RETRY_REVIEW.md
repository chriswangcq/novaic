# Mobile VNC Timeout & Retry Logic Review

**Focus**: Intermittent failures "连接被对方重置" (connection reset by peer) on mobile VNC.

---

## 1. P2pClient Connect Timeout — 15s for Punch

| Location | Value | Notes |
|----------|-------|-------|
| `p2p/config.rs` | `punch_timeout_secs: 15` (default) | Used for hole punch QUIC connect |
| `hole_punch.rs:136-141` | 15s if `timeout_secs == 0` | `connect_to_peer` wraps QUIC handshake |
| `relay.rs:162-165` | 15s default in `punch_or_relay` | When `punch_timeout_secs == 0` |

**Assessment**:
- **15s may be tight** for mobile 4G / weak signal. NAT traversal + QUIC handshake can take 10–20s on poor networks.
- **Recommendation**: Consider 20–25s for punch timeout on mobile, or make it configurable via `NOVAIC_PUNCH_TIMEOUT_SECS`.
- **Does it give up too early?** Yes on slow networks. Punch failure → relay fallback is correct, but relay path has its own timing risks (see below).

---

## 2. Relay Handshake Timeout — 15s in `connect_via_relay` vs Relay Server 15s

| Component | Timeout | Scope |
|-----------|---------|-------|
| **Client** `relay.rs:84-95` | 30s | QUIC connect + handshake |
| **Client** `relay.rs:119-121` | **15s per byte** | Reading handshake response (loop over `read_exact(&mut buf)`) |
| **Relay server** `novaic-quic-service/relay.rs:140-142` | **15s per byte** | Reading RegisterPc / ConnectRequest (same loop) |

**Conflict / Risk**:
- Both sides use 15s **per read_exact() call** (per byte in the loop). A full JSON line (~200–500 bytes) could theoretically take 15s × N if network is extremely slow.
- In practice, each `read_exact` usually returns quickly; the 15s is a guard against hung connections.
- **No direct conflict** — both are "max wait per read". But if mobile 4G is very slow, the client could hit 15s on a single byte read before the server responds.
- **Recommendation**: 15s per byte is reasonable. Consider 20–25s for slow networks if needed. The relay server’s 15s is independent; no need to change unless you see relay-side timeouts in logs.

---

## 3. `get_or_create_remote_conn` — No Retry at VncProxy Level

| Location | Behavior |
|----------|----------|
| `vnc_proxy.rs:352-393` | Single attempt: `p2p_client.connect(...)`. On failure → error propagates → WebSocket handler fails → "connection reset" to frontend |

**Assessment**:
- **No retry** at VncProxy. One failed `connect` (punch or relay) immediately fails the WebSocket.
- `punch_or_relay` internally retries relay connect (4 attempts with 2/4/8s backoff), but **punch has no retry** — single 15s attempt.
- **Recommendation**: Add 1–2 retries at `get_or_create_remote_conn` for transient failures (e.g. "connection reset", timeout). Use short backoff (1–2s) to avoid long waits.

---

## 4. WebSocket — Frontend Connection Timeout

| Component | Timeout | Notes |
|-----------|---------|-------|
| `config/index.ts:118` | `CONNECTION_TIMEOUT: 15000` (15s) | Used by vncStream, useDeviceVNCConnection |
| `scrcpyStream.ts:396` | `CONNECT_TIMEOUT_MS = 15000` | Hardcoded 15s for Scrcpy WS |
| `vncStream.ts:241-244` | `WS_CONFIG.CONNECTION_TIMEOUT` | testWebSocket probe |
| `useDeviceVNCConnection.ts:58` | `WS_CONFIG.CONNECTION_TIMEOUT` | checkWebSocket probe |

**Assessment**:
- Frontend and backend both use **15s** as the effective connection window.
- Backend chain: punch (15s) + relay_request (~1–5s) + 2s initial delay + connect_via_relay (up to 30s QUIC + 15s handshake per attempt, 4 attempts with backoff). **Worst case** relay path can exceed 15s easily.
- **Risk**: Frontend can give up at 15s while backend is still in relay connect (e.g. waiting for PC to register, or retrying).
- **Recommendation**: Increase frontend `CONNECTION_TIMEOUT` to **25–30s** for mobile VNC/Scrcpy to align with relay fallback. Or make it configurable (e.g. `VITE_VNC_CONNECTION_TIMEOUT_MS`).

---

## 5. Gateway relay-request — 30s Timeout, Connect 15s

| Component | Timeout | Notes |
|-----------|---------|-------|
| `rendezvous.rs:251-254` | 30s total, 15s connect | `relay_request` HTTP client |
| Gateway `p2p_relay_request` | No explicit timeout | Returns 200 after `send_push_to_device` |
| `send_push_to_device` | No timeout | `await ws.send_json(message)` — fire-and-forget |

**Assessment**:
- **Mobile gets 200 quickly** — relay-request returns as soon as Gateway pushes `connect_relay` to PC. Push is async; Gateway does not wait for PC to act.
- **PC may not receive push in time** if:
  - CloudBridge WebSocket is slow/buffered
  - PC is under load
  - Network delay between Gateway and PC
- **Race**: Mobile gets 200 → waits 2s → starts `connect_via_relay`. PC might still be processing the push. The 2s `INITIAL_DELAY_SECS` helps, but on slow networks 2s may be insufficient.
- **Recommendation**: Consider 3–4s initial delay for mobile, or make it configurable. The 30s/15s HTTP timeouts for relay-request are fine; the bottleneck is PC processing the push.

---

## 6. Timeouts Too Short for Slow Networks (Mobile 4G)

| Timeout | Current | Suggested for slow networks |
|---------|---------|-----------------------------|
| Punch | 15s | 20–25s |
| Frontend WS connect | 15s | 25–30s |
| Relay initial delay | 2s | 3–4s |
| Relay handshake (per read) | 15s | 20s (optional) |
| STUN (rendezvous) | 5s | 8–10s (UDP, often blocked on mobile) |

**Other observations**:
- `relay_request` and `locate` use 30s total / 15s connect — acceptable.
- QUIC connect in `connect_via_relay`: 30s — acceptable.
- Relay server SESSION_TTL: 120s — fine.

---

## Summary Table

| # | Component | Current | Issue | Recommendation |
|---|-----------|---------|-------|----------------|
| 1 | P2P punch timeout | 15s | May be too short on 4G | 20–25s or configurable |
| 2 | Relay handshake (client/server) | 15s/read | Unlikely conflict | Keep; optionally 20s for slow networks |
| 3 | VncProxy `get_or_create_remote_conn` | Single attempt | No retry on transient failure | Add 1–2 retries with backoff |
| 4 | Frontend WS timeout | 15s | Can give up before backend finishes relay | 25–30s for mobile VNC/Scrcpy |
| 5 | relay-request / push | 200 immediate | PC may receive push late | Increase INITIAL_DELAY to 3–4s |
| 6 | STUN | 5s | Mobile UDP often blocked | 8–10s if needed |

---

## Root Cause of "连接被对方重置"

From `novaic-app/docs/IOS_VNC_WEBSOCKET_ERROR_ANALYSIS.md`:
- **Primary cause (fixed)**: `device_id` vs `agent_id` mismatch — mobile used agent UUID for P2P locate instead of VmControl Ed25519 `device_id`. Locate failed → punch failed → WebSocket dropped → "connection reset".
- **Ongoing causes** (timeout-related):
  1. Frontend 15s timeout closing WS while backend still connecting.
  2. Punch 15s too short on slow mobile networks.
  3. No retry at VncProxy — single failure propagates immediately.
  4. Relay path: 2s initial delay may be insufficient if PC receives push late.

---

## Suggested Code Changes (Priority)

1. **Frontend**: Increase `CONNECTION_TIMEOUT` to 25000–30000 for VNC/Scrcpy.
2. **P2P config**: Add `NOVAIC_PUNCH_TIMEOUT_SECS` (default 20) for mobile.
3. **VncProxy**: Wrap `get_or_create_remote_conn` in 1–2 retries for errors containing "timeout", "reset", "connection refused".
4. **Relay**: Increase `INITIAL_DELAY_SECS` from 2 to 3 or 4 for mobile.
