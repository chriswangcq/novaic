# Phase 3 Error Handling Review

> Strict review of `vnc_endpoint.rs` and related logic. Be strict.

---

## 1. ensure_vnc_endpoint maindesk — novaic-vnc-*.sock fallback

**Current behavior:** Only checks exact `novaic-vnc-{id}.sock` in two dirs:
- `/tmp/novaic`
- `std::env::temp_dir().join("novaic")`

**Gap:** No fallback to any `novaic-vnc-*.sock` when there is exactly one VM.

**Context:** The old `find_vnc_target` (or equivalent) may have had a single-VM fallback: when `resource_id` is ambiguous (e.g. frontend passes generic device_id, or my-devices returns only one PC/VM), scan for `novaic-vnc-*.sock` and use it if exactly one exists.

**Current codebase:** No such fallback exists. `ensure_vnc_endpoint` requires exact `resource_id` match.

**Recommendation (strict):**
- **Option A (keep strict):** Do not add wildcard fallback. Require correct `resource_id` from caller. Single-VM resolution belongs in the routing layer (my-devices, get_vnc_proxy_url), not in endpoint resolution.
- **Option B (add fallback):** If `resource_id` is provided but no matching socket exists, and exactly one `novaic-vnc-*.sock` exists in the search dirs, use it and log a warning. This helps legacy or misconfigured callers but adds ambiguity risk.

**Verdict:** Prefer **Option A**. The Phase 3 design assumes `resource_id` is authoritative. If single-VM fallback is needed, it should be a documented, explicit mode (e.g. `resource_id = ""` or `"*"`) rather than implicit.

---

## 2. Subuser — 30s timeout, 500ms interval for Xvnc startup

**Current constants:**
```rust
const SUBUSER_POLL_TIMEOUT_SECS: u64 = 30;
const SUBUSER_POLL_INTERVAL_MS: u64 = 500;
```
→ 60 polls over 30s.

**Adequacy:**
- Xvnc typically starts within a few seconds when properly configured.
- Known delays (e.g. 20s with `-via` SSH tunnel) are due to tunnel setup, not Xvnc itself.
- 30s is conservative and should cover slow VM boot + Xvnc init.
- 500ms interval is reasonable: not too aggressive (CPU), not too slow (UX).

**Edge cases:**
- Heavy load or slow disk: 30s may still be insufficient.
- Consider making these configurable (env vars) for tuning in production.

**Verdict:** Adequate for typical use. Document that 30s is a hard limit; frontend should surface "Xvnc did not start in time" and allow manual retry.

---

## 3. handle_proxy_connection — port file deleted mid-connection

**Current behavior:** Re-reads port file at the start of each new connection (good for VM restart).

**Scenario:** Port file is deleted while an existing connection is active.

**Analysis:**
- Port is read only when establishing a new connection.
- Once TCP to `127.0.0.1:{port}` is established, the port file is no longer used for that connection.
- If the port file is deleted mid-connection: the existing TCP connection continues until one side closes. No mid-connection re-read.
- If the VM stops and Xvnc exits: TCP will get RST/EOF; the read/write loops will see `Ok(0)` or `Err` and break. Handled correctly.

**Scenario:** Port file deleted between read and TCP connect (race).
- We read port, then file is deleted, then we call `TcpStream::connect`.
- If VM is still running: connect may succeed; we are fine.
- If VM stopped: connect fails; we return `Err`. Correct.

**Scenario:** Port file deleted during a new connection attempt, before we read.
- `read_to_string` returns `Err` (No such file or directory).
- We return `Err`. Correct.

**Verdict:** No bug. Port file is only used at connection establishment. Mid-connection deletion does not affect active connections.

---

## 4. run_subuser_proxy — listener.accept() loop when listener is closed

**Current behavior:**
```rust
loop {
    match listener.accept().await {
        Ok((unix, _)) => { ... }
        Err(e) => {
            warn!("[VNC] Proxy accept error: {}", e);
            break;
        }
    }
}
```

**When does `accept()` return Err?**
- When the listener is closed (dropped): `accept()` returns an error (e.g. "connection refused", "bad file descriptor").
- The loop correctly breaks on `Err`.

**How can the listener be closed?**
- The `UnixListener` is owned by `run_subuser_proxy`; it is not stored elsewhere.
- There is no shutdown mechanism: no `CancellationToken`, no `select!` with shutdown signal.
- The listener is only dropped when `run_subuser_proxy` returns (i.e. when the task finishes or is aborted).
- The task is spawned with `tokio::spawn` and never explicitly cancelled.

**Conclusion:** The listener is never explicitly closed. The proxy runs until process exit. If we wanted graceful shutdown (e.g. when VM stops), we would need:
- A `CancellationToken` or channel passed to `run_subuser_proxy`
- `tokio::select! { _ = shutdown.recv() => break; result = listener.accept() => ... }`
- On shutdown: drop the listener (or call a close method if available) so `accept()` wakes with Err.

**Verdict:** Loop correctly breaks on accept error. No explicit close path exists; proxy runs indefinitely. For strictness: add a shutdown mechanism if VM lifecycle hooks become available.

---

## 5. Proxy registry — entries never removed when VM stops (unbounded growth)

**Current behavior:**
- `PROXY_REGISTRY`: `HashMap<String, PathBuf>` keyed by `resource_id` (e.g. `"vm123:alice"`).
- Entries are added when a subuser proxy is created (line 116).
- Entries are removed only when: registry lookup finds the path and `p.exists()` is false (lines 65–70).

**Problem:** For subuser, the path is `/tmp/novaic/vnc-{resource_id}.sock` — our proxy socket. It exists as long as the proxy process/task is running. The proxy is spawned and never stopped. So `p.exists()` remains true even after the VM stops.

**Result:** Registry grows with every distinct subuser ever connected. Entries are never removed. Unbounded growth.

**Strict fix options:**

1. **Validate port file on registry hit (subuser):** When returning from registry for subuser, also check that the port file exists. If not, remove from registry and fall through to poll logic (which will fail with timeout, but we clean up).
2. **Remove on connection failure:** When `handle_proxy_connection` fails with "port file not found" or "connection refused" to Xvnc, remove the resource_id from the registry. Requires `handle_proxy_connection` to call back into the registry (e.g. via shared `Arc<Mutex<Registry>>` or a channel).
3. **VM stop hook:** When VM stop is detected (e.g. via VmControl API or device status), explicitly remove subuser entries for that VM from the registry. Requires integration with VM lifecycle.
4. **TTL / periodic cleanup:** Periodically scan registry; for each subuser entry, check port file existence; remove if gone. Adds background task complexity.

**Recommended (strict):** Implement **Option 1** — on registry hit for subuser, verify port file exists. If not, remove entry and treat as cache miss. This prevents stale entries when the VM has stopped and the port file is gone, without requiring VM lifecycle integration.

**Implementation sketch:**
```rust
// In ensure_vnc_endpoint, subuser branch, when we have a registry hit:
if let Some(p) = g.get(resource_id) {
    if p.exists() {
        // For subuser: also verify port file still exists
        let port_file = format!("{}/share-{}/vnc-{}.port", NOVAIC_DIR, vm_id, username);
        if tokio::fs::metadata(&port_file).await.is_ok() {
            return Ok(p.clone());
        }
        // Port file gone — VM stopped; remove stale entry
        g.remove(resource_id);
    } else {
        g.remove(resource_id);
    }
}
```

---

## Summary

| # | Issue | Severity | Action |
|---|-------|----------|--------|
| 1 | maindesk novaic-vnc-*.sock fallback | Low | Keep strict; no implicit fallback |
| 2 | Subuser 30s/500ms | OK | Adequate; consider env config |
| 3 | Port file deleted mid-connection | None | No bug; port only used at connect |
| 4 | Listener closed in accept loop | Low | Loop breaks correctly; add shutdown if needed |
| 5 | Proxy registry unbounded growth | **High** | Validate port file on registry hit; remove if gone |
