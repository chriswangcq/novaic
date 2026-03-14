# VNC Backend Flow Research

Research trace of the VNC backend flow from frontend to Unix socket or TCP port, including maindesk vs subuser divergence.

---

## 1. Trace: route_vnc → get_vnc_proxy_url → vnc_bridge → p2p tunnel find_vnc_target

### 1.1 Frontend Entry Points

| Component | Entry | agentId / resource_id Source |
|-----------|-------|-----------------------------|
| **Maindesk** | `VNCViewShared`, `DeviceVNCView`, `vncStream`, `useVNCConnection`, `useDeviceVNCConnection` | `device.id` (VM agent_id) |
| **Subuser** | `VmUserVNCView` | `${deviceId}:${username}` (e.g. `abc123:alice`) |

**Data flow from DeviceFloatingPanel:**
- **Main**: `VNCViewShared agentId={agentId} deviceId={device.id}` → `streamKey = deviceId` → `getVncTransport(deviceId)`
- **Subuser**: `VmUserVNCView deviceId={device.id} username={binding.subject_id}` → `getVncTransport(\`${deviceId}:${username}\`)`

### 1.2 Tauri Commands

| Command | File | Purpose |
|---------|------|---------|
| `get_vnc_proxy_url` | `vnc_urls.rs` | Returns `ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id}` |
| `vnc_bridge_connect` | `vnc_bridge.rs` | OTA mode: Rust connects to VncProxy WS, returns bridge_id for IPC |

**get_vnc_proxy_url flow:**
1. Resolve `device_id`: `local_vmcontrol.device_id` (desktop) OR `deviceId` param OR Gateway `my-devices` first online
2. `agent_id` = caller-provided (main: `device.id`, subuser: `${deviceId}:${username}`)
3. Return `p.ws_url(&device_id, &agent_id)` → `ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id}`

**vnc_bridge_connect flow (OTA):**
1. Same `resolve_device_id` + `agent_id` as above
2. `tokio_tungstenite::connect_async(&ws_url)` to VncProxy
3. Spawn task: WS ↔ `vnc_bridge_send` / `vnc_bridge:{id}:data` events

### 1.3 VncProxy (vnc_proxy.rs)

**Route:** `GET /vnc/:device_id/:agent_id` → `vnc_handler` → `route_vnc`

**route_vnc logic:**
```
if local_vmcontrol.device_id == device_id:
    serve_local_vnc(ws, agent_id)   # QUIC loopback 127.0.0.1
else:
    serve_remote_vnc(ws, device_id, agent_id)  # P2P connect via Gateway
```

**Local path:**
1. `get_or_create_local_conn()` → `p2p_client.connect_direct(127.0.0.1:{port}, device_id, cert_der)`
2. `p2p::tunnel::open_vnc_stream(&conn, agent_id)` → QUIC stream with header `[0x01][len][agent_id bytes]`
3. `bridge_ws_quic(ws, quic_send, quic_recv)` — bidirectional proxy

**Remote path:**
1. `get_or_create_remote_conn(device_id)` → `p2p_client.connect(gateway_url, token, device_id)` (relay)
2. Same `open_vnc_stream(&conn, agent_id)` + `bridge_ws_quic`

### 1.4 P2P Tunnel (p2p/tunnel.rs)

**PC side (Tunnel Server):**
- `run_tunnel_server(conn, vmcontrol_base_url)` — accepts incoming QUIC streams
- `handle_incoming_stream`: reads `[stream_type][id_len][id_bytes]`
- For `stream_type == 0x01` (VNC): `resource_id = String::from_utf8(id_bytes)`
- Calls `find_vnc_target(&resource_id)` → `VncTarget::Tcp(port)` | `VncTarget::Unix(path)` | `VncTarget::NotFound`
- Proxies QUIC stream ↔ Unix socket or TCP

**Client side (Tauri app):**
- `open_vnc_stream(conn, vm_id)` writes header `[0x01][len][vm_id bytes]`, returns `(SendStream, RecvStream)`

---

## 2. resource_id Flow: Frontend → Unix Socket / TCP Port

```
Frontend                    Tauri / VncProxy              P2P Tunnel (PC)              Target
─────────────────────────────────────────────────────────────────────────────────────────────────
Maindesk:
  device.id                 agent_id in WS path          resource_id in stream         find_vnc_target
  "abc123"        →        /vnc/{did}/abc123      →     [0x01][6]["abc123"]     →     Unix: /tmp/novaic/novaic-vnc-abc123.sock

Subuser:
  deviceId:username        agent_id in WS path          resource_id in stream         find_vnc_target
  "abc123:alice"   →       /vnc/{did}/abc123:alice →     [0x01][12]["abc123:alice"] →  TCP: 127.0.0.1:{port}
                                                                                            port from /tmp/novaic/share-abc123/vnc-alice.port
```

**Summary:**
- `resource_id` = `agent_id` in the URL path (unchanged through the pipeline)
- VncProxy passes it to `open_vnc_stream(conn, agent_id)` (same value)
- Tunnel server reads it from the stream header and passes to `find_vnc_target(&resource_id)`

---

## 3. Maindesk vs Subuser Divergence (tunnel.rs find_vnc_target)

**Location:** `novaic-app/src-tauri/p2p/src/tunnel.rs` — `find_vnc_target(resource_id: &str)`

### 3.1 Branch Logic

```rust
// 多用户格式：{vm_id}:{username}
if let Some(colon_pos) = resource_id.find(':') {
    let vm_id   = &resource_id[..colon_pos];
    let username = &resource_id[colon_pos + 1..];
    if !username.is_empty() {
        // SUBUSER: TCP port file
        let port_file = format!("/tmp/novaic/share-{}/vnc-{}.port", vm_id, username);
        if let Ok(s) = std::fs::read_to_string(&port_file) {
            if let Ok(port) = s.trim().parse::<u16>() {
                return VncTarget::Tcp(port);  // → 127.0.0.1:{port}
            }
        }
        return VncTarget::NotFound(...);
    }
}

// MAINDESK: QEMU VNC Unix socket
let vm_id = resource_id;
let qemu_vnc = format!("/tmp/novaic/novaic-vnc-{}.sock", vm_id);
if std::path::Path::new(&qemu_vnc).exists() {
    return VncTarget::Unix(qemu_vnc);
}
return VncTarget::NotFound(...);
```

### 3.2 Divergence Table

| Type | resource_id Format | Target | Path / Port Source |
|------|-------------------|--------|--------------------|
| **Maindesk** | `{vm_id}` | Unix socket | `/tmp/novaic/novaic-vnc-{vm_id}.sock` (QEMU VNC) |
| **Subuser** | `{vm_id}:{username}` | TCP | `/tmp/novaic/share-{vm_id}/vnc-{username}.port` → read port → `127.0.0.1:{port}` (TigerVNC/Xvnc) |

### 3.3 Why the Split

- **Maindesk**: QEMU uses `-vnc unix:/tmp/novaic/novaic-vnc-{vm_id}.sock`; socket exists when VM is running.
- **Subuser**: TigerVNC/Xvnc runs inside the VM; port is written to a 9p-shared file. VM host must connect via TCP (hostfwd) to the guest Xvnc port.

---

## 4. File Index

| File | Role |
|------|------|
| **vnc_proxy.rs** | `route_vnc`, `serve_local_vnc`, `serve_remote_vnc`, `vnc_handler`; WS path `/vnc/:device_id/:agent_id`; local vs remote routing |
| **vnc_urls.rs** | `get_vnc_proxy_url` — resolves device_id, returns ws_url |
| **vnc_bridge.rs** | `vnc_bridge_connect` — OTA bridge; `resolve_device_id`; connects to VncProxy WS via IPC |
| **p2p/tunnel.rs** | `find_vnc_target`, `handle_incoming_stream`, `open_vnc_stream`; maindesk vs subuser divergence |
| **vmcontrol api/routes** | VNC: no HTTP route (direct tunnel → socket). Scrcpy: `/api/android/scrcpy?device={serial}` (WebSocket) |

### VmControl VNC-Related Routes

| Route | Purpose |
|-------|---------|
| `/api/vms/:id/vnc` | Legacy VNC WebSocket (vnc.rs; maindesk only) |
| `/api/android/scrcpy` | Scrcpy WebSocket (used by tunnel for remote scrcpy) |
| `/api/android/scrcpy/status` | Scrcpy availability check |

**Note:** VNC for maindesk/subuser does **not** go through VmControl HTTP. It goes:
- VncProxy WS → QUIC tunnel → `find_vnc_target` → Unix socket or TCP

Scrcpy uses VmControl: tunnel → `ws://{vmcontrol_base}/api/android/scrcpy?device={serial}` → `scrcpy::scrcpy_websocket`.

---

## 5. Related Documents

- `docs/MAINDESK_VS_SUBUSER_VNC_ANALYSIS.md` — frontend/backend differences, retry behavior, RFB options
