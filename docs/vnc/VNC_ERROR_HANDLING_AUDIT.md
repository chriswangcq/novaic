# VNC Error Handling and Timeout Audit

**Scope:** novaic-app VNC proxy, bridge, frontend, and P2P setup  
**Date:** 2026-03-12

---

## 1. WebSocket Upgrade Timeout

**Question:** Does axum/axum-websocket have an upgrade timeout?

**Finding:** **No built-in upgrade timeout.**

- Axum's `WebSocketUpgrade` has no timeout configuration. It exposes buffer/message size options (`read_buffer_size`, `max_message_size`, etc.) but no timeout.
- The upgrade flow: `ws.on_upgrade(move |socket| async move { route_vnc(...) })` — the upgrade completes when the HTTP handshake finishes; the async handler then runs without any timeout.
- **Gap:** If `route_vnc` hangs (e.g. P2P connect, QUIC stream open, or Unix connect never completes), the WebSocket stays in a half-open state indefinitely. The client may have its own timeout (e.g. `WS_CONFIG.CONNECTION_TIMEOUT` 15s in frontend), but the server never times out.

**Recommendation:** Wrap the upgrade handler with `tokio::time::timeout(Duration::from_secs(30), route_vnc(...))` and send a Close frame on timeout.

---

## 2. QUIC Stream Open Timeout (`open_vnc_stream`)

**Question:** Does `open_vnc_stream` have a timeout?

**Finding:** **No timeout.**

- `p2p::tunnel::open_vnc_stream` (and `open_scrcpy_stream`) in `p2p/src/tunnel.rs`:
  ```rust
  let (mut send, recv) = conn.open_bi().await?;
  write_stream_header(&mut send, StreamType::Vnc as u8, vm_id).await?;
  ```
- `conn.open_bi()` is awaited with no timeout. Quinn's `open_bi()` has no built-in timeout; it can block until the connection is closed or the peer accepts the stream.
- **Gap:** If the tunnel server (VmControl) is slow or stuck (e.g. Unix socket connect hangs), `open_bi` + header write can hang indefinitely.

**Recommendation:** Wrap with `tokio::time::timeout(Duration::from_secs(15), open_vnc_stream(...))` at the call site in `vnc_proxy.rs`.

---

## 3. Unix Socket Connect Timeout (VncProxy → QEMU)

**Question:** Is there a timeout when connecting to the QEMU VNC Unix socket?

**Finding:** **No timeout.**

- The Unix socket connect happens in the **tunnel server** (VmControl), not in VncProxy. Flow:
  - VncProxy (client) → QUIC → VmControl (tunnel server) → `handle_incoming_stream` → `find_vnc_target` → `UnixStream::connect(&socket_path)`.
- In `p2p/src/tunnel.rs`:
  ```rust
  let unix = UnixStream::connect(&socket_path).await
      .map_err(|e| anyhow::anyhow!("VNC Unix connect to {} failed: {}", socket_path, e))?;
  ```
- `UnixStream::connect` has no timeout. If the socket exists but QEMU is unresponsive, the connect can hang.
- Same for `TcpStream::connect` (TigerVNC multi-user path) and `tokio_tungstenite::connect_async` (scrcpy WS path).

**Recommendation:** Use `tokio::time::timeout(Duration::from_secs(5), UnixStream::connect(...))` (and equivalent for TCP/WS) in the tunnel server.

---

## 4. `bridge_ws_quic` — QUIC Stream Error and WS Close

**Question:** What happens on QUIC stream error? Does the WebSocket get closed cleanly?

**Finding:** **Partial clean close; race on error path.**

- On QUIC stream error (e.g. `quic_recv.read` returns `Err`, or `quic_send.write_all` fails):
  - `bridge_ws_quic` returns `Err` via `tokio::select!`.
  - The caller (`serve_local_vnc`, `serve_remote_vnc`, etc.) does not catch it; the error propagates to the handler, which returns `Err`.
  - The WebSocket is dropped. `WsWriteCloseGuard` wraps `ws_write`; on drop it spawns `sink.close().await` in a new task.
- **Gap:** The guard's drop is fire-and-forget. The handler returns immediately; the close frame may not be sent before the TCP connection is torn down. The client can see "connection reset" instead of a clean WebSocket Close.
- **Gap:** When `quic_to_ws` breaks (e.g. QUIC reset), `ws_to_quic` may still be running. The `select!` cancels the other branch, but `quic_send.finish()` might not run, and the WS close is only via the guard's drop.

**Recommendation:** On error, explicitly `send(Message::Close(None))` and `flush` before returning, or use a synchronous close path instead of spawning in drop.

---

## 5. Frontend — WebSocket `onerror` / `onclose` and User-Visible Messages

**Question:** Does the frontend show useful messages on WebSocket error/close?

**Finding:** **Limited; RFB hides low-level WebSocket details.**

| Component | WebSocket handling | User-visible message |
|-----------|--------------------|----------------------|
| **VNCView** (useVNCConnection + RFB) | RFB creates WebSocket internally. No direct `onerror`/`onclose`. RFB fires `disconnect` with `e.detail?.clean`. | `disconnect`: only logs "clean"/"unclean"; no backend error text. `securityfailure`: logs reason. |
| **vncStream.ts** | Same: RFB internal. `disconnect` → status `error`/`disconnected`; `notifySubscribers(state, 'error', ...)` but no message from backend. | Generic "Connection lost" or status change; no specific error. |
| **VmUserVNCView** | RFB `disconnect`: `setErrorMsg('Connection lost')` if not clean. | "Connection lost" — generic. |
| **ScrcpyStream** | Raw WebSocket: `onerror` logs; `onclose` sets status. Backend can send `{ type: 'error', message }` in `onmessage`. | Scrcpy shows `message.message` when backend sends error. VNC has no equivalent. |
| **useVNCConnection** | `checkWebSocket` uses `ws.onerror` → reject with `'ws error'`; timeout → `'timeout'`. | Only for pre-RFB probe; not for live VNC. |

**Gaps:**
- VNC backend never sends a structured error message over the WebSocket (unlike scrcpy's `{ type: 'error', message }`). Errors are either connection reset or a Close frame with no reason.
- RFB `disconnect` does not expose the Close code/reason. The frontend cannot show "P2P connect failed" or "VNC socket not found" from the backend.
- `testWebSocket` in vncStream and `checkWebSocket` in useVNCConnection use `WS_CONFIG.CONNECTION_TIMEOUT` (15s) for the probe; the live RFB connection has no explicit timeout.

**Recommendation:** (1) Send a Close frame with a reason code and reason string from the backend when failing before/during bridge. (2) Use RFB's close event if it exposes code/reason, or add a custom "error" message before closing. (3) Surface the reason in the UI.

---

## 6. `p2p_setup_error` — When Set and Blocking Behavior

**Question:** When is it set? Does it block all remote VNC?

**Finding:** **Set only on desktop P2P server failure; blocks only when `device_id` matches.**

- **When set:** In `vmcontrol/src/lib.rs` when `p2p_server.start()` returns `Err`:
  ```rust
  Err(e) => {
      if let Some(ref shared) = p2p_setup_error {
          *shared.write().await = Some((identity.id.clone(), e.to_string()));
      }
  }
  ```
  `identity.id` is the local machine's Ed25519 device_id. So `p2p_setup_error` is set only when the **local** P2P QUIC server fails to start (desktop, with `data_dir`).

- **On mobile:** No `data_dir` → no P2P server start → `p2p_setup_error` is never set.

- **Routing logic** (`vnc_proxy.rs`):
  ```rust
  if local_id == device_id { serve_local_vnc(...) }
  else if let Some((failed_did, err)) = p2p_setup_error {
      if failed_did == device_id {
          anyhow::bail!("P2P setup failed: {}. Please check NOVAIC_P2P_PORT and firewall.", err);
      }
      serve_remote_vnc(...)  // try anyway
  } else {
      serve_remote_vnc(...)
  }
  ```
  - Block: `failed_did == device_id` (request targets the device that had P2P setup failure).
  - No block: `failed_did != device_id` → `serve_remote_vnc` is attempted.

- **Behavior:** Only blocks attempts to the **same** device that failed P2P setup. Other remote devices are still tried. On desktop, `failed_did` is the local machine; blocking typically happens when the user tries to connect to the local machine via a path that hits this branch (e.g. `local_vmcontrol` not ready yet).

**Gap:** `device_id` in the frontend vs `failed_did` (Ed25519 hex) can differ. Docs note: "p2p_setup_error 的 device_id 与前端可能不一致" — frontend may use UUID from cloud `my-devices`, backend uses Ed25519. This can cause incorrect block or incorrect allow.

**Recommendation:** Ensure consistent device_id handling between frontend and backend when checking `p2p_setup_error`.

---

## Summary: Gaps and Recommendations

| Area | Gap | Recommendation |
|------|-----|----------------|
| WebSocket upgrade | No server-side timeout | Wrap handler with `tokio::time::timeout(Duration::from_secs(30), ...)` |
| QUIC stream open | No timeout on `open_vnc_stream` | Add `tokio::time::timeout(15s, ...)` at call site |
| Unix socket connect | No timeout in tunnel server | Add `tokio::time::timeout(5s, UnixStream::connect(...))` |
| TCP/WS connect (tunnel) | No timeout for TigerVNC/scrcpy | Add `tokio::time::timeout(5s, ...)` for connect |
| bridge_ws_quic | WS close on error is fire-and-forget | Explicitly send Close frame before returning |

| bridge_ws_quic | QUIC error → WS may reset abruptly | Await close before returning on error |
| Frontend VNC | No backend error message over WS | Send Close reason or custom error message before close |
| Frontend VNC | RFB hides WS details | Use Close reason if available; show in UI |
| p2p_setup_error | device_id mismatch (UUID vs Ed25519) | Align frontend/backend device_id semantics |

---

## Files Referenced

| File | Relevance |
|------|-----------|
| `novaic-app/src-tauri/src/vnc_proxy.rs` | route_vnc, bridge_ws_quic, send_ws_close, p2p_setup_error routing |
| `novaic-app/src-tauri/p2p/src/tunnel.rs` | open_vnc_stream, open_scrcpy_stream, UnixStream::connect, proxy_quic_to_unix |
| `novaic-app/src-tauri/vmcontrol/src/lib.rs` | p2p_setup_error write on P2P start failure |
| `novaic-app/src/services/vncStream.ts` | RFB, testWebSocket, disconnect handling |
| `novaic-app/src/components/Visual/VNCView.tsx` | RFB disconnect, no error message |
| `novaic-app/src/components/Visual/useVNCConnection.ts` | checkWebSocket, CONNECTION_TIMEOUT |
| `novaic-app/src/services/scrcpyStream.ts` | Raw WS onerror/onclose, backend error message |
| `novaic-app/src/config/index.ts` | WS_CONFIG.CONNECTION_TIMEOUT (15000) |
