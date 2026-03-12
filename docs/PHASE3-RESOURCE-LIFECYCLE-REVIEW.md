# Phase 3 Resource Lifecycle Review

**Strict audit of subuser VNC proxy lifecycle. All four concerns are confirmed.**

---

## 1. `run_subuser_proxy` — Task Runs Forever

**Location:** `novaic-app/src-tauri/p2p/src/vnc_endpoint.rs:108-111, 124-145`

```rust
tokio::spawn(async move {
    run_subuser_proxy(listener, port_file_owned, resource_id_owned).await;
});
// ...
async fn run_subuser_proxy(...) {
    loop {
        match listener.accept().await {
            Ok((unix, _)) => { /* spawn per-connection task */ }
            Err(e) => { break; }  // only exit on accept error
        }
    }
}
```

**Problem:** The loop never exits under normal conditions. When the VM stops:
- The proxy task keeps running indefinitely
- It continues to hold the `UnixListener` and the socket file
- No shutdown signal, no timeout, no VM-stop hook

**Impact:** One orphaned task per subuser, forever. With many VMs/users over time, this accumulates.

**Old port forwarding:** `handle_proxy_connection` reads `port_file` on **each** connection (line 153-157). So:
- If VM restarts and Xvnc overwrites the port file → new connections get the new port ✓
- If VM is stopped → port file may be missing/stale → `TcpStream::connect` fails with "Connection refused" or "No such file"
- The proxy still accepts Unix connections and then fails on TCP connect — wasted work and confusing errors

---

## 2. `PROXY_REGISTRY` — Never Removes Entries

**Location:** `novaic-app/src-tauri/p2p/src/vnc_endpoint.rs:19-26, 113-117`

```rust
static PROXY_REGISTRY: OnceLock<Arc<Mutex<HashMap<String, PathBuf>>>> = ...;
// insert on proxy start (line 116)
// remove only in one place: when p.exists() is false (line 69)
```

**Problem:** Entries are only removed when `ensure_vnc_endpoint` is called again and `p.exists()` is false. Since the proxy task never exits, the socket file always exists. So the registry entry is never removed.

**Impact:** `HashMap` grows unbounded with every subuser that has ever connected. Memory leak over long-running sessions with many VMs/users.

---

## 3. `UnixListener` — When Does It Get Dropped?

**Answer:** Only when the spawned task exits.

**Lifecycle:**
1. `UnixListener::bind(&socket_path)` creates the listener
2. It is moved into `run_subuser_proxy` and then into the `tokio::spawn` task
3. The task runs `loop { listener.accept().await ... }` forever
4. `UnixListener` is dropped when the task exits
5. Task exits only on `listener.accept()` returning `Err` (e.g. listener closed, or rare OS error)

**Conclusion:** Under normal operation, the listener is never dropped. The socket file `/tmp/novaic/vnc-{id}.sock` remains bound until process exit.

**Corollary:** `stop_vm` removes `novaic-vnc-{id}.sock` (maindesk) but **cannot** remove subuser sockets — they are held by the proxy. Even if we added `std::fs::remove_file` for subuser sockets in `stop_vm`, it would fail with "Device or resource busy" because the proxy still has the listener bound.

---

## 4. TTL or Cleanup on VM Stop?

**Recommendation: Yes. Cleanup on VM stop is required.**

| Approach | Pros | Cons |
|----------|------|------|
| **TTL** | Simple, self-healing | Doesn't know VM state; may kill proxy while VM still running |
| **Cleanup on VM stop** | Correct lifecycle, no orphans | Requires vmcontrol → p2p hook |
| **Both** | Belt and suspenders | More complexity |

**Strict recommendation:** Implement **cleanup on VM stop** as the primary mechanism. TTL can be an optional safety net for edge cases (e.g. vmcontrol crash, missed stop event).

### Required Changes

1. **`vnc_endpoint.rs` — Add shutdown API**
   - `pub async fn shutdown_proxy_for_vm(vm_id: &str)` — for all `resource_id` where `resource_id == vm_id` or `resource_id.starts_with(vm_id + ":")`
   - Store `AbortHandle` (or `CancellationToken`) per proxy task so we can abort it
   - On shutdown: abort task → task exits → `UnixListener` dropped → socket file released
   - Remove entries from `PROXY_REGISTRY` for that VM

2. **`stop_vm` in vmcontrol** — Call shutdown
   - After killing the VM process and cleaning maindesk sockets, call `p2p::vnc_endpoint::shutdown_proxy_for_vm(&id)`
   - Then remove subuser socket files (they should be unbound by then, or remove is best-effort)

3. **Registry structure**
   - Current: `HashMap<String, PathBuf>` (resource_id → socket path)
   - Needed: `HashMap<String, ProxyEntry>` where `ProxyEntry { path, abort_handle }` so we can abort and remove

4. **Optional TTL**
   - If desired: background task that periodically checks `port_file` existence or TCP connect to port; if VM appears dead for N minutes, abort proxy and remove from registry. Not a substitute for VM-stop cleanup.

---

## Summary Table

| Issue | Confirmed | Severity |
|-------|-----------|----------|
| Proxy task runs forever on VM stop | ✓ | High — resource leak |
| PROXY_REGISTRY never removes | ✓ | High — memory leak |
| UnixListener never dropped | ✓ | High — socket file never released |
| Need cleanup on VM stop | ✓ | Required |

---

## References

- `novaic-app/src-tauri/p2p/src/vnc_endpoint.rs` — proxy spawn, registry, `run_subuser_proxy`
- `novaic-app/src-tauri/vmcontrol/src/api/routes/vm.rs` — `stop_vm` (cleans maindesk only)
- `novaic-app/src-tauri/vmcontrol/src/api/routes/vnc.rs` — calls `ensure_vnc_endpoint`
