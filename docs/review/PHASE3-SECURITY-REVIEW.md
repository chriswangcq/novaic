# Phase 3 Security Review — resource_id and Path Safety

> Review of `ensure_vnc_endpoint(resource_id)` and related path construction in the VNC backend unification (unify-vnc Phase 3).

---

## 1. resource_id Sources (Untrusted Input)

| Source | Location | Validation |
|--------|----------|------------|
| **QUIC stream** | `tunnel.rs` L76–82 | None. `id_len` from `read_u8()` (0–255), `resource_id = String::from_utf8(id_bytes)`. No content validation. |
| **URL path** | `vnc_proxy.rs` `/vnc/{pc_client_id}/{resource_id}` | None. Axum `Path` extractor decodes URL; `resource_id` can be arbitrary. |
| **VmControl API** | `vmcontrol/api/routes/vnc.rs` `GET /api/vms/:resource_id/vnc` | None. Same as above. |

**Risk**: Attacker can send `resource_id = "../../../etc/passwd"`, `"a".repeat(10000)`, or other malicious input.

---

## 2. safe_resource_id = resource_id.replace(':', '-')

**Current code** (`vnc_endpoint.rs` L59):
```rust
let safe_resource_id = resource_id.replace(':', '-');
```

**Issues**:

1. **Path traversal**: `replace(':', '-')` does not sanitize `..`, `/`, `\`, or null bytes.
   - `resource_id = "../../../etc/passwd"` → `safe_resource_id = "../../../etc/passwd"` (unchanged).
   - `PathBuf::from("/tmp/novaic").join(format!("vnc-{}.sock", safe_resource_id))` produces a path that resolves outside `/tmp/novaic` (e.g. `/etc/passwd.sock`).

2. **Very long input**: No length limit. `resource_id` of 10,000 chars yields a socket path exceeding `UNIX_PATH_MAX` (typically 108 bytes), causing `UnixListener::bind` to fail or undefined behavior.

3. **Other dangerous chars**: `/`, `\`, null bytes, control chars are not rejected.

---

## 3. Socket Path `/tmp/novaic/vnc-{safe_resource_id}.sock`

**Current construction**:
```rust
let socket_path = PathBuf::from(NOVAIC_DIR).join(format!("vnc-{}.sock", safe_resource_id));
```

**Rust `PathBuf::join` behavior**:
- Joining a path containing `..` can escape the base directory.
- Example: `PathBuf::from("/tmp/novaic").join("vnc-../../../etc/passwd.sock")` → `/etc/passwd.sock` after resolution.

**Mitigation**: Validate `resource_id` with a strict allowlist so it cannot produce path traversal. Do not rely on `PathBuf::join` alone.

---

## 4. port_file Path

**Current code** (`vnc_endpoint.rs` L57):
```rust
let port_file = format!("{}/share-{}/vnc-{}.port", NOVAIC_DIR, vm_id, username);
```

**Issues**:
- `vm_id` and `username` come from `resource_id.split_once(':')` — no validation.
- `vm_id = "../../../etc"`, `username = "passwd"` → `/tmp/novaic/share-../../../etc/vnc-passwd.port` → path traversal.
- Same risk for `read_to_string(&port_file)` and `remove_file(&socket_path)`.

---

## 5. UnixListener::bind

**Current code** (`vnc_endpoint.rs` L103):
```rust
let listener = UnixListener::bind(&socket_path).map_err(|e| { ... })?;
```

**Risk**: If `socket_path` escaped via malicious `resource_id`, we could:
- Bind a socket at `/etc/passwd.sock` or another sensitive path.
- Overwrite or create files outside `/tmp/novaic`.

---

## 6. maindesk Branch (Same Issues)

**Current code** (L36–42):
```rust
let sock = PathBuf::from(NOVAIC_DIR).join(format!("novaic-vnc-{}.sock", resource_id));
// ...
let p = dir.join(format!("novaic-vnc-{}.sock", resource_id));
```

`resource_id` is used directly without sanitization. Same path-traversal and length risks.

---

## 7. tunnel.rs — id_len Overflow (Known)

`write_stream_header` uses `id_bytes.len() as u8`; values > 255 overflow. `P2P-SUBAGENT-FIX-LIST.md` already documents this. We should enforce `resource_id.len() <= 255` in both tunnel and vnc_endpoint.

---

## Recommended Fixes

### A. Strict resource_id Validation

Add `validate_resource_id(resource_id: &str) -> Result<(), String>`:

- **Allowlist**: `[a-zA-Z0-9_-]` for maindesk; `[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+` for subuser.
- **Reject**: `/`, `\`, `.`, `..`, null, control chars, any non-ASCII if desired.
- **Length**: `resource_id.len() <= 80` (keeps `/tmp/novaic/vnc-{id}.sock` under UNIX_PATH_MAX 108).

### B. Path Safety Check (Defense in Depth)

After constructing `socket_path` and `port_file`:
- Resolve to canonical path and verify `path.starts_with("/tmp/novaic")` (or use `strip_prefix` on canonical base).
- Reject if the resolved path escapes the base.

### C. tunnel.rs

- Validate `id_len <= 255` before allocating.
- Call `validate_resource_id` before `ensure_vnc_endpoint`.

### D. VmControl vnc.rs

- Call `validate_resource_id` before `ensure_vnc_endpoint`.

### E. vnc_proxy.rs

- Validate `resource_id` when handling `/vnc/{pc_client_id}/{resource_id}` (or rely on `ensure_vnc_endpoint` if it validates early).

---

## Summary

| Issue | Severity | Fix |
|-------|----------|-----|
| Path traversal via resource_id | **High** | Strict allowlist validation |
| Very long resource_id | **Medium** | Length limit (≤80) |
| port_file path traversal | **High** | Same validation for vm_id, username |
| maindesk path injection | **High** | Same validation |
| id_len u8 overflow (tunnel) | **Medium** | Validate id_len ≤ MAX_RESOURCE_ID_LEN |
| Unix socket path length | **Low** | Length limit covers this |

---

## Implementation (Done)

- **`vnc_endpoint.rs`**: Added `validate_resource_id()` with allowlist `[a-zA-Z0-9_-]` (maindesk) and `[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+` (subuser). Max length 80. Called at start of `ensure_vnc_endpoint`.
- **`tunnel.rs`**: Validate `id_len` before allocating; validate `resource_id` length in `write_stream_header` before sending.
