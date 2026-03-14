# Phase 3 vnc_endpoint.rs Code Review

> 宁可错杀不可放过 — strict review of `novaic-app/src-tauri/p2p/src/vnc_endpoint.rs`

---

## 1. ensure_vnc_endpoint: maindesk vs subuser logic

### 1.1 Empty vm_id not rejected (BUG)

```rust
let (vm_id, username) = resource_id
    .split_once(':')
    .filter(|(_, u)| !u.is_empty())
    .ok_or_else(|| format!("Invalid subuser resource_id: {}", resource_id))?;
```

- `filter` only checks `!u.is_empty()`; `vm_id` can be empty.
- Example: `resource_id = ":alice"` → `vm_id = ""`, `username = "alice"`.
- `port_file = "/tmp/novaic/share-/vnc-alice.port"` — invalid path.
- **Fix**: Add `filter(|(v, u)| !v.is_empty() && !u.is_empty())`.

### 1.2 Empty maindesk resource_id

- `resource_id = ""` → `!"".contains(':')` → maindesk path.
- Looks for `novaic-vnc-.sock`; likely returns Err. Acceptable but unclear.
- **Recommendation**: Reject early with `if resource_id.trim().is_empty() { return Err(...) }`.

### 1.3 Path traversal in vm_id / username (SECURITY)

- `port_file = format!("{}/share-{}/vnc-{}.port", NOVAIC_DIR, vm_id, username)`.
- If `username = "../../../etc/passwd"` → path escapes share dir.
- `vm_id` with `..` can also escape.
- **Fix**: Validate `vm_id` and `username` do not contain `..`, `/`, or `\` before use.

### 1.4 Username with special chars in port file path

- `username` in port file is used as-is: `vnc-{username}.port`.
- If username contains `:`, `\0`, `/`, etc., port file path may be invalid or unsafe.
- `safe_resource_id` only affects the socket path, not the port file.
- **Recommendation**: Reject usernames with path-unsafe chars or sanitize.

---

## 2. PROXY_REGISTRY concurrency (OnceLock + Mutex)

### 2.1 Double-registration race (BUG)

Two concurrent callers for the same resource_id can both:

1. See registry empty.
2. Poll port file.
3. Remove old socket.
4. Bind and spawn proxy.
5. Insert into registry.

- Caller A: binds, spawns, inserts.
- Caller B: `remove_file` may remove A’s socket.
- On Unix, removing the file does not close the listener; the socket stays in use.
- B: `bind` succeeds; two listeners now exist for the same path.
- Result: Orphaned task, duplicate proxies, potential resource waste.

**Fix**: Use per-resource_id locking (e.g. `DashMap` + per-key `Mutex` or `RwLock`) so only one setup runs per resource_id at a time.

### 2.2 OnceLock + Mutex correctness

- `OnceLock::get_or_init` is thread-safe.
- `Arc<Mutex<HashMap>>` is fine; `tokio::sync::Mutex` must be `.await`ed.
- Lock is held correctly across registry lookup/insert/remove.

---

## 3. run_subuser_proxy and handle_proxy_connection

### 3.1 Socket lifecycle — no cleanup on VM shutdown (BUG)

- `run_subuser_proxy` runs forever until `listener.accept()` returns `Err`.
- `listener.accept()` only fails when the listener is closed (e.g. `drop`).
- No shutdown signal or VM shutdown hook.
- VM shutdown does not remove the socket or stop the proxy task.
- **Result**: Orphaned proxy tasks and sockets.

**Fix**: Either:

- Add a shutdown channel (e.g. `tokio::sync::watch`) and `select!` on it, or
- Integrate with VM lifecycle (e.g. VM shutdown removes socket and unregisters).

### 3.2 Registry cleanup on proxy exit

- When `run_subuser_proxy` exits (e.g. accept error), `resource_id` is not removed from registry.
- Next `ensure_vnc_endpoint` will see `p.exists()` false and remove.
- Acceptable if proxy exit is rare; otherwise stale entries remain until next call.

### 3.3 handle_proxy_connection — socket lifecycle

- `unix` and `tcp` are split and used in `select!`.
- `shutdown()` is called on both directions.
- `into_split` is used correctly; `UnixStream` and `TcpStream` are dropped on completion.
- **OK**.

### 3.4 Port file read error in handle_proxy_connection

- If port file is missing or invalid (VM shutdown): `read_to_string` or `parse` fails.
- Error is returned to caller; connection is dropped.
- **OK**.

### 3.5 Spawned tasks without JoinHandle

- `tokio::spawn` for `run_subuser_proxy` and `handle_proxy_connection` is fire-and-forget.
- Tasks are not joined or cancelled.
- No unbounded growth per connection; each task ends when the connection closes.
- **OK** for connection handling; proxy task is the leak.

---

## 4. safe_resource_id

### 4.1 Consistency with tunnel resource_id

- Tunnel: `resource_id` is sent as raw bytes in the stream header.
- VNC endpoint: `resource_id` = registry key; `safe_resource_id = resource_id.replace(':', '-')` for socket path.
- Socket path: `vnc-{vm_id}-{username}.sock`.
- Registry key: `{vm_id}:{username}`.
- Both use the same resource_id format; tunnel does not need to know about safe_resource_id.
- **OK**.

### 4.2 Multiple colons in resource_id

- `resource_id = "a:b:c"` → `split_once(':')` → `("a", "b:c")`.
- `username = "b:c"`; `safe_resource_id = "a-b-c"`.
- Socket path: `vnc-a-b-c.sock`.
- Port file: `share-a/vnc-b:c.port`.
- If username can contain `:`, this is consistent; port file path must match what Xvnc writes.
- **OK** if the protocol allows `:` in username.

---

## 5. Port file polling

### 5.1 TOCTOU

- Port file is read, parsed, then `break`; we do not use the parsed port.
- `port_file` is passed to `run_subuser_proxy`; each connection re-reads the port.
- Initial poll only checks existence and parseability.
- **OK** for initial poll.

### 5.2 File deletion during read

- `tokio::fs::read_to_string(&port_file)` — if deletion happens mid-read, we get `Err`.
- Loop continues and retries.
- **OK**.

### 5.3 File deletion during handle_proxy_connection read

- If port file is deleted, `read_to_string` fails.
- Connection fails; error returned.
- **OK**.

### 5.4 Port file content validation

- `s.trim().parse::<u16>()` — only checks for valid u16.
- Port 0 is valid; port 65535 is valid.
- Port 0 is unusual for VNC; may want to reject.
- **Low priority**.

### 5.5 Unused variable

- `let _port = loop { ... break p; }` — `_port` is never used.
- **Minor**: Use `let _ = loop { ... }` or remove.

---

## 6. Memory leaks and unbounded growth

### 6.1 PROXY_REGISTRY HashMap

- **Insert**: On each new subuser proxy.
- **Remove**: Only when `p.exists()` is false on `ensure_vnc_endpoint(resource_id)`.
- If a resource_id is never requested again:
  - Proxy task never exits.
  - Registry entry never removed.
- **Result**: Unbounded growth for long-lived VMs and many subusers.

### 6.2 run_subuser_proxy tasks

- One task per subuser proxy.
- Tasks never exit.
- **Result**: Unbounded growth.

### 6.3 handle_proxy_connection tasks

- One task per connection.
- Tasks exit when connection closes.
- **OK**.

---

## 7. Summary of fixes

| Severity | Issue | Fix |
|----------|-------|-----|
| **HIGH** | Empty vm_id accepted | `filter(|(v, u)| !v.is_empty() && !u.is_empty())` |
| **HIGH** | Path traversal in vm_id/username | Validate no `..`, `/`, `\` |
| **HIGH** | Double-registration race | Per-resource_id lock for setup |
| **HIGH** | No cleanup on VM shutdown | Shutdown channel or VM lifecycle integration |
| **MEDIUM** | Registry unbounded growth | Periodic cleanup or VM shutdown unregister |
| **MEDIUM** | Proxy tasks never exit | Same as VM shutdown cleanup |
| **LOW** | Empty resource_id | Early reject |
| **LOW** | Username path safety | Validate or sanitize |
| **LOW** | Unused `_port` | Remove or use |

---

## 8. Recommended additional checks

1. **maindesk resource_id**: Reject path traversal for maindesk, e.g. `resource_id.contains("..") || resource_id.contains('/')`.
2. **Resource ID length**: Limit length to avoid huge paths or DoS.
3. **Port validation**: Optionally reject port 0 or reserved ports.
