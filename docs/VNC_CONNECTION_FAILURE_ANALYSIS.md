# VNC Connection Flow — Failure Points Analysis

Complete trace of the VNC connection flow from frontend to backend, with identified failure points, race conditions, and error propagation gaps.

---

## 1. Flow Overview

```
Frontend (invoke get_vnc_proxy_url) 
  → VncProxy WebSocket (ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id})
  → vnc_handler → route_vnc → serve_local_vnc | serve_remote_vnc
  → get_or_create_local_conn | get_or_create_remote_conn
  → p2p::tunnel::open_vnc_stream
  → QUIC stream → PC tunnel server (run_tunnel_server)
  → handle_incoming_stream → find_vnc_target → UnixStream::connect(novaic-vnc-{agent_id}.sock)
```

---

## 2. Failure Points by Severity

### HIGH

| # | Location | Issue | Severity |
|---|----------|-------|----------|
| 1 | `vnc_proxy.rs:243-245` | **`send_ws_close` sends `Message::Close(None)`** — no reason code or message. Frontend receives generic "connection closed" (code 1005) and cannot show the actual error (e.g. "Device offline", "VNC socket not found"). | **HIGH** |
| 2 | `scrcpyStream.ts:371-373` | **`getScrcpyProxyUrl().then(wsUrl => ...)` has no `.catch()`** — if `invoke` fails (proxy not started, no online device, network error), the rejection is unhandled. Connection never starts; user sees no feedback. Same pattern likely for VNC if it uses similar invoke. | **HIGH** |
| 3 | `vnc_proxy.rs:119-123` | **Bind failure: `port_tx.send` never called** — if `TcpListener::bind` fails, the spawn returns early. `port_rx.await` in setup.rs times out after 3s. `proxy.port` stays 0. `get_vnc_proxy_url` returns "VNC proxy not started yet" but the real cause (e.g. port in use, permission denied) is only logged to stderr. | **HIGH** |
| 4 | `vnc_urls.rs:36-55` | **`get_vnc_proxy_url` mobile: `my-devices` returns first online device** — if user has multiple PCs, the wrong `device_id` may be used. No way to target a specific device. | **HIGH** (mobile multi-device) |
| 5 | `tunnel.rs:86-102` | **`find_vnc_target` → `UnixStream::connect`** — TOCTOU: `Path::exists()` then `connect()`. VM could shut down between check and connect. Socket may not exist yet when stream arrives (VM just started). No retry. | **HIGH** |

### MEDIUM

| # | Location | Issue | Severity |
|---|----------|-------|----------|
| 6 | `vnc_proxy.rs:398-436` | **`get_or_create_remote_conn` holds `remote_conns` lock during full P2P connect** — connect can take 15s+ (punch) or 30s+ (relay). Other VNC requests for the same device block. Concurrent requests for different devices are serialized by HashMap lock. | **MEDIUM** |
| 7 | `vnc_proxy.rs:333-345` | **`get_or_create_local_conn` race** — Between releasing `local_conn` lock (after cache miss) and re-acquiring, another task could create the connection. The double-check is correct, but `local_vmcontrol.read().await` can change between retries. If VmControl restarts mid-retry, we might connect to stale info. | **MEDIUM** |
| 8 | `vnc_proxy.rs:206-212` | **`p2p_setup_error` check: wrong device_id semantics** — `failed_did` is the local device that failed P2P setup. On mobile, `local_vmcontrol` is None, so we always go to `serve_remote_vnc`. The `failed_did == device_id` check would only apply if connecting to the device that had setup failure — but on mobile we're connecting to remote PC. Logic is correct for desktop; on mobile this branch is never hit for the intended case. Minor: if `p2p_setup_error` is set for a different device, we still attempt `serve_remote_vnc` which may fail with a different error. | **MEDIUM** |
| 9 | `relay.rs:84-95` | **Relay connect: 30s timeout** — `connect_via_relay` has 30s timeout. `punch_or_relay` uses `punch_timeout_secs` (default 15s) for punch, then relay. Total can exceed 15+30+retries (2+4+8s) = 59s+ for first success. Frontend `CONNECT_TIMEOUT_MS=15000` may fire before backend completes. | **MEDIUM** |
| 10 | `vnc_urls.rs:40` | **`gateway_get_impl` errors** — If Gateway returns 401/403/500 or network fails, error propagates as `Err(String)`. But `get_vnc_proxy_url` returns `Result<String, String>` — the string may be generic ("request failed") and not user-friendly. | **MEDIUM** |
| 11 | `tunnel.rs:90-91` | **VNC TCP connect: no timeout** — `TcpStream::connect(&addr)` has no explicit timeout. If VmControl is hung, connect can block indefinitely. | **MEDIUM** |
| 12 | `tunnel.rs:96-97` | **VNC Unix connect: no timeout** — `UnixStream::connect(&socket_path)` has no explicit timeout. | **MEDIUM** |

### LOW

| # | Location | Issue | Severity |
|---|----------|-------|----------|
| 13 | `setup.rs:89-95` | **Port assignment timeout: generic message** — "Failed to get assigned port" doesn't distinguish bind failure from spawn delay. | **LOW** |
| 14 | `vnc_proxy.rs:172-176` | **Error only logged** — `route_vnc` errors are logged with `tracing::error!` but the WebSocket is already closed. No structured error reporting to a central place. | **LOW** |
| 15 | `tunnel.rs:100-102` | **`VncTarget::NotFound` message** — Good error message, but `anyhow::bail!` propagates to `handle_incoming_stream` → `warn!` only. QUIC stream gets dropped; client sees connection reset. Error not sent as WebSocket Close reason. | **LOW** |
| 16 | `hole_punch.rs:184-189` | **`peer_ext_addr` loopback/unspecified** — Correctly rejected with clear message. | **LOW** (handled) |
| 17 | `vnc_proxy.rs:322-324` | **`open_vnc_stream` failure: remote_conn removed from cache** — Correct. But if the failure was transient (e.g. VM restarting), next request will re-connect. Connection might be fine; we removed it. Could keep conn and only remove on `close_reason().is_some()`. | **LOW** |

---

## 3. Timeout Gaps

| Stage | Timeout | Location | Gap |
|-------|---------|----------|-----|
| Frontend WebSocket connect | 15s | `scrcpyStream.ts:397` | VNC (if same) may use same 15s. P2P+relay can take 15–60s. |
| Punch | 15s (configurable) | `config.rs:73`, `hole_punch.rs:138-143` | Default 15s. |
| Relay connect | 30s | `relay.rs:84-95` | Fixed. |
| Relay handshake response | 15s | `relay.rs:118` | Per-byte read timeout. |
| VncProxy port assignment | 3s | `setup.rs:89` | If bind fails, port_tx never sent; 3s timeout then "Failed to get assigned port". |
| get_or_create_local_conn retry | 3 × 500ms | `vnc_proxy.rs:334-345` | 1.5s max wait for local_vmcontrol. |
| Rendezvous locate | 30s HTTP timeout | `rendezvous.rs:284` | 3 retries with 500ms/1s backoff. |
| Tunnel Unix/TCP connect | None | `tunnel.rs:90,96` | Can block indefinitely. |

---

## 4. Race Conditions

| # | Description | Location |
|---|-------------|----------|
| 1 | **local_vmcontrol vs. VNC click** — User clicks VNC before `local_vmcontrol` is written (VmControl P2P not ready). `get_or_create_local_conn` retries 3×500ms then bails. Mitigated but message "VmControl P2P not ready yet" may be confusing. | `vnc_proxy.rs:334-345` |
| 2 | **Concurrent remote connects for same device** — `get_or_create_remote_conn` holds lock during full connect. First request connects; others wait. If first fails after long wait, others retry. No connection coalescing. | `vnc_proxy.rs:404-436` |
| 3 | **VM socket creation vs. stream** — `find_vnc_target` checks `Path::exists()`. VM may create socket milliseconds later. No retry in tunnel. | `tunnel.rs:136-171` |
| 4 | **port vs. proxy.port** — `start()` sends port via oneshot. `setup.rs` spawns task that awaits port_rx and then sets `proxy.port`. `get_vnc_proxy_url` reads `proxy.port` under lock. If frontend calls before port is set, port is still 0. Small window. | `setup.rs:88-96`, `vnc_urls.rs:20-22` |

---

## 5. Silent Failures / Missing Error Propagation

| # | Issue | Location |
|---|-------|----------|
| 1 | **Close frame has no reason** — Client cannot display specific error. | `vnc_proxy.rs:244` |
| 2 | **getScrcpyProxyUrl rejection unhandled** — Promise rejection not caught. | `scrcpyStream.ts:371` |
| 3 | **Bind failure only to stderr** — No structured error to app. | `vnc_proxy.rs:122` |
| 4 | **CloudBridge connect_via_relay failure** — Only `tracing::warn!`; no retry, no user notification. | `cloud_bridge.rs:298-300` |
| 5 | **handle_incoming_stream error** — `warn!` in spawn; stream dropped. Client sees reset. | `tunnel.rs:52-54` |

---

## 6. Wrong / Misleading Error Messages

| # | Location | Issue |
|---|----------|-------|
| 1 | `vnc_proxy.rs:210` | "P2P setup failed" — On mobile, `p2p_setup_error` is for local device. Message may confuse when connecting to remote. |
| 2 | `hole_punch.rs:169-173` | "Device {} is offline" — Correct. But if locate returns online with bad ext_addr, we get "Device has no registered ext_addr" — different from offline. |
| 3 | `vnc_urls.rs:51` | "No online VmControl device found" — Assumes my-devices. If Gateway returns empty array, we get "my-devices response has no devices array" (line 45) or "No online...". Inconsistent. |
| 4 | `vnc_urls.rs:45` | "my-devices response has no devices array" — Technical. User might see "or_else(|| resp.as_array())" handling — if Gateway returns `[]` we get "No online VmControl device found" which is better. |

---

## 7. Edge Cases — Connection Fails Without Clear Feedback

1. **Mobile, no login** — `get_vnc_proxy_url` needs token for my-devices. If token empty, `gateway_get_impl` may fail with 401. Error string may be generic.
2. **Mobile, Gateway down** — `gateway_get_impl` fails. Error propagates. But if frontend doesn't catch invoke rejection, user sees nothing.
3. **Desktop, VmControl not started** — `local_vmcontrol` is None. `get_vnc_proxy_url` uses local_vmcontrol first; if None, falls through to my-devices. On desktop with no VmControl, we'd use my-devices (wrong — we're the desktop). Actually: `or_else(|| None)` — so we go to my-devices. That's for mobile. On desktop, local_vmcontrol should be set when VmControl starts. If user opens VNC before VmControl ready, local_vmcontrol is None → my-devices. Could return wrong device on multi-PC desktop. Edge case.
4. **VM just started** — Socket not created yet. Tunnel gets "No VNC socket found". Client sees connection reset.
5. **Relay session expired** — PC registered with relay, then session expires. Mobile connects via relay; relay may reject. "Relay rejected" — good. But if relay drops connection mid-stream, client sees reset.
6. **QUIC connection closed mid-bridge** — `bridge_ws_quic` uses `tokio::select!` on ws_to_quic and quic_to_ws. When one returns (e.g. stream closed), we return. No explicit Close to client in some paths. `WsWriteCloseGuard` sends Close on drop — good.

---

## 8. Recommendations (Summary)

1. **Send Close reason** — Use `Message::Close(Some(CloseFrame { code, reason }))` with error code and message.
2. **Handle invoke rejections** — Add `.catch()` to `getScrcpyProxyUrl` / `get_vnc_proxy_url` and surface errors to UI.
3. **Propagate bind failure** — Send error via channel or set state when bind fails so setup can report it.
4. **Add connect timeouts** — For `TcpStream::connect` and `UnixStream::connect` in tunnel.
5. **Retry socket connect** — In `find_vnc_target` / `handle_incoming_stream`, retry Unix connect a few times for "VM just started".
6. **Align timeouts** — Frontend 15s vs backend 15–60s for P2P+relay. Consider increasing frontend or showing "Connecting…" longer.
7. **Optional device_id for mobile** — Allow frontend to pass target device_id for multi-device scenarios.
