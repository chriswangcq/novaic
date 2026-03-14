# VNC Proxy QUIC Connection Pool Audit

**Scope**: `novaic-app/src-tauri/src/vnc_proxy.rs`, `setup.rs`, `commands/vnc_urls.rs`  
**Focus**: Connection caching, stale state, races causing "often fails"

---

## 1. `local_conn`, `remote_conns` — When Are They Cleared?

### `local_conn` (lines 68, 114–115, 322–366)

| When cleared | Location |
|-------------|----------|
| On `close_reason().is_some()` | `get_or_create_local_conn` L347–351: `*guard = None` |
| **Never** on logout, config change, or shutdown | — |

**Bug**: Only cleared when a closed connection is detected. No proactive invalidation.

### `remote_conns` (lines 70, 116, 398–439)

| When cleared | Location |
|-------------|----------|
| On `close_reason().is_some()` | `get_or_create_remote_conn` L306–308, 404–407 |
| On `open_vnc_stream` / `open_scrcpy_stream` error | L311–314, 385–388: spawns task `conns.lock().await.remove(&did)` |
| **Never** on logout, device disconnect, or shutdown | — |

**Bug**: Stale entries stay until an error path removes them. No periodic or event-driven cleanup.

---

## 2. Connection Health — Validation Before Reuse?

**Current check**: `conn.close_reason().is_none()` (L327, 349, 405)

- Only checks local close state.
- Does not verify remote peer is still reachable.
- No ping/keepalive or stream probe before reuse.

**Effect**:

- Idle connections can be dead (NAT timeout, peer sleep, network partition).
- Remote QUIC idle timeout may have closed the connection.
- First use after idle returns cached connection → `open_vnc_stream` fails → error path removes entry → next request retries connect.
- This explains “often fails” on first attempt after idle.

**Recommendation**: Add a lightweight probe (e.g. `open_uni()` or small `open_bi()` write) before reuse, or use a short TTL and refresh.

---

## 3. Mutex Contention — `get_or_create_remote_conn` Holds Lock During Full P2P Connect

**Bug**: Lock held for the entire P2P connect.

```rust
// vnc_proxy.rs L398–439
async fn get_or_create_remote_conn(device_id, state) -> Result<Connection> {
    let mut guard = state.remote_conns.lock().await;  // LOCK ACQUIRED
    if let Some(conn) = guard.get(device_id) { ... }
    // ...
    let conn = state.p2p_client.connect(...).await;   // HOLDS LOCK DURING:
    //   - discovery.lookup (HTTP)
    //   - punch_or_relay (UDP hole punch + optional relay)
    //   - relay timeout up to 30s (relay.rs L85)
    guard.insert(device_id.to_string(), conn.clone()); // LOCK RELEASED
    Ok(conn)
}
```

**Impact**:

- All other `remote_conns` access (including different `device_id`s) is blocked.
- P2P connect can take seconds (relay timeout 30s).
- Concurrent VNC/Scrcpy to different devices serialize unnecessarily.

**Contrast**: `get_or_create_local_conn` (L322–366) uses a short lock for the cache check, releases before `connect_direct`, then re-acquires only for the insert.

**Recommendation**: Use the same pattern as `get_or_create_local_conn`: short lock for cache check, release before `connect`, re-acquire only for insert. Optionally use per-device locks to avoid blocking different devices.

---

## 4. Stale Port — VncProxy Port 0 vs Actual, Race at Startup

**Flow**:

1. `VncProxyServer::new()` sets `port: 0` (L90).
2. `start()` spawns task: `bind("127.0.0.1:0")` → `port_tx.send(actual_port)` (L118–124).
3. `setup_shared` spawns task: `port_rx.await` (3s timeout) → `proxy_clone.lock().await.port = port` (setup.rs L89–95).
4. `get_vnc_proxy_url` / `get_scrcpy_proxy_url` check `if p.port == 0` → `Err("VNC proxy not started yet")` (vnc_urls.rs L21, 74).

**Race**:

- Frontend can call `get_vnc_proxy_url` before the async task sets `port`.
- User sees “VNC proxy not started yet” with no retry.
- `ws_url` uses `self.port`; if `port == 0`, URL is `ws://127.0.0.1:0/...`, which is invalid.

**Recommendation**:

- Expose `port_rx` or a “ready” future so callers can wait for the port.
- Or: `get_vnc_proxy_url` waits (with timeout) for `port != 0` before returning.
- Or: Frontend retries with backoff when it gets “VNC proxy not started yet”.

---

## 5. Shutdown / Cleanup — Does Drop or App Exit Properly Close Connections?

**Current behavior**:

- `VncProxyServer::Drop` calls `stop()` (L157–159).
- `stop()` sends shutdown via `shutdown_tx` (L144–145).
- `axum::serve` uses `with_graceful_shutdown(shutdown_rx.await)` (L133–134).
- Graceful shutdown stops accepting new connections and waits for in-flight handlers.

**What is not done**:

- No explicit `connection.close()` on cached connections.
- No clearing of `local_conn` or `remote_conns` on shutdown.

**What happens**:

- When the server task finishes, `HandlerState` (and its `Arc`s) is dropped.
- `Connection` refcount goes to 0 → Quinn `Connection::drop` runs → connection closes.
- So on normal shutdown, connections are closed implicitly.

**Risks**:

- Force kill (SIGKILL) or crash: no cleanup.
- Long-lived connections may not close cleanly in all edge cases.
- No explicit close makes behavior harder to reason about and debug.

**Recommendation**: On `stop()`, clear `local_conn` and `remote_conns` and explicitly close each `Connection` before signaling shutdown.

---

## 6. Multiple Devices — `remote_conns` Key Collision? `device_id` Format?

**Key**: `vmcontrol_device_id` (Ed25519 hex, 64 chars) from URL path `:device_id`.

**Collision**:

- Each VmControl instance has a unique Ed25519 `device_id`.
- No collision between different PCs.

**Format**:

- `device_id` is Ed25519 hex (see `p2p/src/device_id.rs`, `IOS_VNC_WEBSOCKET_ERROR_ANALYSIS.md`).
- If the frontend passes `agent_id` (e.g. UUID) instead of `vmcontrol_device_id`, locate fails; this is a separate bug (see `IOS_VNC_WEBSOCKET_ERROR_ANALYSIS.md`).

---

## Summary: Connection Pool Bugs and Stale State

| # | Issue | Severity | Causes "often fails"? |
|---|-------|----------|------------------------|
| 1 | `local_conn` / `remote_conns` never proactively cleared | Medium | Indirect (stale entries) |
| 2 | No connection health check before reuse | **High** | **Yes** — first use after idle often fails |
| 3 | `get_or_create_remote_conn` holds lock during full P2P connect | **High** | **Yes** — blocks other devices, long waits |
| 4 | Port 0 race at startup | Medium | **Yes** — “VNC proxy not started yet” |
| 5 | No explicit connection close on shutdown | Low | No |
| 6 | `device_id` key collision | None | No |

---

## Recommended Fixes (Priority Order)

1. **Connection health**: Probe before reuse (e.g. `open_uni()` or small `open_bi()` write), or invalidate after idle TTL.
2. **Mutex contention**: Release `remote_conns` lock before `p2p_client.connect()`, re-acquire only for insert (mirror `get_or_create_local_conn`).
3. **Port race**: Make `get_vnc_proxy_url` wait for `port != 0` (with timeout) or expose a ready future.
4. **Cleanup**: On `stop()`, clear caches and explicitly close connections.
5. **Proactive invalidation**: Clear `remote_conns` on logout; optionally add TTL or periodic cleanup for idle entries.
