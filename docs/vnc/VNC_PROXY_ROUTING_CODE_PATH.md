# vnc_proxy 本机/远程路由实现 — 中层调研

## 1. route_vnc、serve_local_vnc、serve_remote_vnc 实现

### 1.1 route_vnc（路由入口）

**位置**：`novaic-app/src-tauri/src/vnc_proxy.rs` L239–262

```rust
async fn route_vnc(ws, device_id, agent_id, state) -> Result<()> {
    let local_id = state.local_vmcontrol.read().await
        .as_ref()
        .map(|info| info.device_id.clone());

    if local_id.as_deref() == Some(device_id) {
        // 本机 VmControl：QUIC loopback
        serve_local_vnc(ws, agent_id, &state).await
    } else if let Some((failed_did, err)) = state.p2p_setup_error.read().await.as_ref() {
        if failed_did == device_id {
            anyhow::bail!("P2P setup failed: {}. Please check NOVAIC_P2P_PORT and firewall.", err);
        }
        serve_remote_vnc(ws, device_id, agent_id, &state).await
    } else {
        // 远端设备：Gateway locate + QUIC P2P
        serve_remote_vnc(ws, device_id, agent_id, &state).await
    }
}
```

**路由规则**：

| 条件 | 分支 |
|------|------|
| `device_id == local_vmcontrol.device_id` | `serve_local_vnc`（本机 QUIC loopback） |
| `p2p_setup_error` 存在且 `failed_did == device_id` | 直接 `bail`，不尝试连接 |
| 其他 | `serve_remote_vnc`（远端 P2P） |

### 1.2 serve_local_vnc（本机路径）

**位置**：`vnc_proxy.rs` L304–326

```rust
async fn serve_local_vnc(ws, agent_id, state) -> Result<()> {
    let conn = get_or_create_local_conn(state).await?;  // 127.0.0.1:port
    let (quic_send, quic_recv) = p2p::tunnel::open_vnc_stream(&conn, agent_id).await?;
    bridge_ws_quic(ws, quic_send, quic_recv).await
}
```

流程：**本地 QUIC 连接** → **open_vnc_stream(agent_id)** → **WS ↔ QUIC 桥接**

### 1.3 serve_remote_vnc（远端路径）

**位置**：`vnc_proxy.rs` L429–451

```rust
async fn serve_remote_vnc(ws, device_id, agent_id, state) -> Result<()> {
    let conn = get_or_create_remote_conn(device_id, state).await?;  // Gateway + relay
    let (quic_send, quic_recv) = p2p::tunnel::open_vnc_stream(&conn, agent_id).await?;
    bridge_ws_quic(ws, quic_send, quic_recv).await
}
```

流程：**远端 QUIC 连接** → **open_vnc_stream(agent_id)** → **WS ↔ QUIC 桥接**

---

## 2. get_or_create_local_conn vs get_or_create_remote_conn

### 2.1 get_or_create_local_conn

**位置**：`vnc_proxy.rs` L381–427

| 项目 | 说明 |
|------|------|
| 缓存 | `state.local_conn`：单条 `Option<(Connection, Instant)>` |
| 目标 | `127.0.0.1:{info.port}`（来自 `local_vmcontrol`） |
| 建连 | `p2p_client.connect_direct(addr, &info.device_id, &info.cert_der)` |
| TTL | `conn_still_valid`：`close_reason().is_none() && elapsed < 4min` |
| 竞态 | 启动时 `local_vmcontrol` 可能未就绪，最多重试 3 次（500ms 间隔） |
| 持锁 | 短锁查缓存 → 释放 → 建连 → 持锁写缓存（避免多窗口并发建连） |

### 2.2 get_or_create_remote_conn

**位置**：`vnc_proxy.rs` L455–416

| 项目 | 说明 |
|------|------|
| 缓存 | `state.remote_conns`：`HashMap<device_id, (Connection, Instant)>` |
| 目标 | 通过 Gateway `relay` 定位远端设备 |
| 建连 | `p2p_client.connect(&gateway_url, &token, device_id)` |
| TTL | 同 `conn_still_valid` |
| 前置 | `gateway_url`、`token` 非空，否则 `bail` |
| 持锁 | 短锁查缓存 → 释放 → 建连（不持锁）→ 持锁写缓存 |

### 2.3 对比

| 维度 | local | remote |
|------|-------|--------|
| 地址 | `127.0.0.1:{port}` | Gateway relay + device_id |
| 缓存 | 单条 | 按 device_id 分 |
| 建连 | `connect_direct` | `connect`（relay） |
| 超时 | 本地快 | 通常 10–30s |

---

## 3. ensure_vnc_endpoint 对 maindesk/subuser 的处理

**位置**：`novaic-app/src-tauri/p2p/src/vnc_endpoint.rs` L107–204

**调用链**：`tunnel::handle_incoming_stream`（PC 侧）→ `ensure_vnc_endpoint(resource_id)`

### 3.1 resource_id 格式

- **maindesk**：`{vm_id}`（即 device_id）
- **subuser**：`{vm_id}:{username}`

### 3.2 maindesk 分支（`resource_id` 不含 `:`）

```rust
if !resource_id.contains(':') {
    let sock = PathBuf::from(NOVAIC_DIR).join(format!("novaic-vnc-{}.sock", resource_id));
    // 查找 /tmp/novaic 或 env::temp_dir()/novaic 下的 novaic-vnc-{resource_id}.sock
    if p.exists() { return Ok(p); }
    return Err("VNC socket not found for VM '{}'...");
}
```

- 直接返回 QEMU VNC socket 路径
- 无轮询、无代理

### 3.3 subuser 分支（`resource_id` 含 `:`）

```rust
let (vm_id, username) = resource_id.split_once(':')...;
let port_file = "{NOVAIC_DIR}/share-{vm_id}/vnc-{username}.port";
let socket_path = "{NOVAIC_DIR}/vnc-{resource_id.replace(':', '-')}.sock";
```

1. **轮询 port 文件**：最多 30s，500ms 间隔
2. **创建 Unix 代理**：`UnixListener::bind(socket_path)` → `run_subuser_proxy`
3. **代理逻辑**：`handle_proxy_connection`：Unix ↔ TCP(127.0.0.1:{port})
4. **注册**：`PROXY_REGISTRY` 记录 `(socket_path, JoinHandle)` 便于 shutdown

### 3.4 安全校验

- `validate_resource_id`：长度 ≤ 80，仅允许 `[a-zA-Z0-9_-]`（maindesk）或 `vm_id:username`（subuser）

---

## 4. vnc_proxy 路由决策代码路径

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ HTTP GET /vnc/:device_id/:agent_id                                                │
│   device_id = pc_client_id (物理 PC 标识)                                         │
│   agent_id  = resource_id (maindesk: device_id; subuser: {device_id}:{username})   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ vnc_handler (L177)                                                                │
│   ws.on_upgrade → route_vnc(ws, device_id, agent_id, state)                      │
│   30s 超时：超时则 send Close reason                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ route_vnc (L239)                                                                  │
│   local_id = local_vmcontrol.device_id                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────────┐   ┌───────────────────────────────────────────────────────┐
│ device_id ==      │   │ device_id != local_id                                  │
│ local_id          │   │   p2p_setup_error?                                      │
└───────────────────┘   │     failed_did == device_id → bail                       │
        │               │     else → serve_remote_vnc                              │
        ▼               │   else → serve_remote_vnc                               │
┌───────────────────┐   └───────────────────────────────────────────────────────┘
│ serve_local_vnc   │                           │
└───────────────────┘                           ▼
        │                           ┌───────────────────────────────────────────┐
        │                           │ serve_remote_vnc                          │
        │                           │   get_or_create_remote_conn(device_id)     │
        │                           │   → p2p_client.connect(gateway, token, id) │
        │                           └───────────────────────────────────────────┘
        ▼                                           │
┌───────────────────┐                               │
│ get_or_create_    │                               │
│ local_conn        │                               │
│ → connect_direct  │                               │
│   (127.0.0.1:    │                               │
│    local_port)   │                               │
└───────────────────┘                               │
        │                                           │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ tunnel::open_vnc_stream(conn, agent_id)                                          │
│   写入 stream header [0x01][len][agent_id]                                       │
│   返回 (quic_send, quic_recv)                                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ bridge_ws_quic(ws, quic_send, quic_recv)                                         │
│   WS ↔ QUIC 双向桥接                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### PC 侧（Tunnel Server）— ensure_vnc_endpoint 调用点

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ run_tunnel_server(conn, vmcontrol_base_url)                                      │
│   loop { conn.accept_bi() → handle_incoming_stream(send, recv) }                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ handle_incoming_stream                                                            │
│   读取 [stream_type][id_len][resource_id]                                        │
│   stream_type == 0x01 (VNC) → ensure_vnc_endpoint(resource_id)                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ensure_vnc_endpoint(resource_id)                                                  │
│   maindesk: 返回 novaic-vnc-{resource_id}.sock                                   │
│   subuser:  轮询 port 文件 → 建 Unix 代理 → 返回 vnc-{resource_id}.sock          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ UnixStream::connect(socket_path) → proxy_quic_to_unix(send, recv, unix)           │
│   QUIC stream ↔ Unix socket 双向桥接                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 关键点

1. **vnc_proxy 不区分 maindesk/subuser**：只传 `agent_id`（即 resource_id）给 `open_vnc_stream`。
2. **maindesk/subuser 区分在 PC 侧**：`ensure_vnc_endpoint` 根据 `resource_id` 是否含 `:` 分支。
3. **本机/远端区分在 vnc_proxy**：`device_id` 与 `local_vmcontrol.device_id` 比较决定 local/remote 路径。
