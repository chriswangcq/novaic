# 第二轮调研（中层）：P2P Relay 与 Tunnel 实现细节

## 一、relay.rs 实现逻辑

### 1.1 `connect_via_relay`（relay.rs:49–151）

**职责**：通过 relay 服务建立 QUIC 连接（PC 或手机侧均可调用）。

**实现流程**：

| 步骤 | 代码位置 | 说明 |
|-----|----------|------|
| 1 | L54–65 | `parse_relay_url` 解析 host:port，非 IP 则 DNS 解析 |
| 2 | L67–82 | `relay_client_tls()` + `hole_punch::p2p_transport_config()` 构建 ClientConfig，绑定 `0.0.0.0:0` 创建 Endpoint |
| 3 | L84–95 | `endpoint.connect(addr, &host)` 超时 30s，建立 QUIC 连接 |
| 4 | L97–114 | `conn.open_bi()` 开双向流，按 `RelayRole` 写 JSON：
  - **Pc**：`{ device_id, jwt, session_id }`
  - **Mobile**：`{ target_device_id, jwt, session_id }`
  - 写入后 `send.finish()` |
| 5 | L116–131 | 读取 relay 响应（逐字节直到 `\n`），超时 40s |
| 6 | L133–144 | 解析 JSON `{ ok, error }`，`!ok` 则 bail 返回错误 |

**关键代码片段**：

```49:95:novaic-app/src-tauri/p2p/src/relay.rs
pub async fn connect_via_relay(
    relay_url: &str,
    jwt: &str,
    session_id: &str,
    role: RelayRole,
) -> anyhow::Result<Connection> {
    let (host, port) = parse_relay_url(relay_url)?;
    // ... DNS 解析 ...
    let conn = tokio::time::timeout(
        Duration::from_secs(30),
        async {
            endpoint
                .connect(addr, &host)
                .map_err(|e| anyhow::anyhow!("Relay connect failed: {}", e))?
                .await
                .map_err(|e| anyhow::anyhow!("Relay handshake failed: {}", e))
        },
    )
    .await
    .map_err(|_| anyhow::anyhow!("Relay connection timeout after 30s"))??;
```

```99:114:novaic-app/src-tauri/p2p/src/relay.rs
    let json = match &role {
        RelayRole::Pc { device_id } => serde_json::json!({
            "device_id": device_id,
            "jwt": jwt,
            "session_id": session_id,
        }),
        RelayRole::Mobile { target_device_id } => serde_json::json!({
            "target_device_id": target_device_id,
            "jwt": jwt,
            "session_id": session_id,
        }),
    };
    let line = serde_json::to_string(&json)?;
    send.write_all(line.as_bytes()).await?;
    send.write_all(b"\n").await?;
    send.finish()?;
```

---

### 1.2 `connect_via_relay_only`（relay.rs:156–239）

**职责**：手机侧远端连接入口，仅走 relay（打洞已移除）。

**实现流程**：

| 步骤 | 代码位置 | 说明 |
|-----|----------|------|
| 1 | L161 | `rendezvous::relay_request(gateway_url, jwt, target_device_id)` → `{ relay_url, session_id }` |
| 2 | L162–165 | `relay_url_override`（如 `NOVAIC_RELAY_URL`）可选覆盖 relay_url |
| 3 | L179–235 | 最多 4 次尝试：`connect_via_relay(..., RelayRole::Mobile)` |
| 4 | L201–225 | 若错误含 `session` / `expired` → 重新 `relay_request` 获取新 session_id 再重试 |
| 5 | L226–234 | 否则按 2s/4s/8s 指数退避重试 |

**关键代码片段**：

```156:188:novaic-app/src-tauri/p2p/src/relay.rs
/// 通过 relay 建立远端连接（打洞已移除，仅 relay）。
pub async fn connect_via_relay_only(
    gateway_url: &str,
    jwt: &str,
    target_device_id: &str,
    relay_url_override: Option<&str>,
) -> anyhow::Result<Connection> {
    let relay_resp = crate::rendezvous::relay_request(gateway_url, jwt, target_device_id).await?;
    let relay_url = relay_url_override
        .filter(|s| !s.trim().is_empty())
        .map(String::from)
        .unwrap_or_else(|| relay_resp.relay_url.clone());
    // ...
    for attempt in 1..=4 {
        match connect_via_relay(
            &current_relay_url,
            jwt,
            &current_relay_resp.session_id,
            RelayRole::Mobile {
                target_device_id: target_device_id.to_string(),
            },
        )
        .await
        {
            Ok(conn) => return Ok(conn),
            Err(e) => {
                // session 错误时 refresh 再重试
                // 否则 2s/4s/8s 退避
            }
        }
    }
```

---

## 二、tunnel.rs 数据流

### 2.1 `run_tunnel_server`（tunnel.rs:47–67）

**职责**：PC 侧监听 QUIC 连接上的 incoming streams，为每个 stream  spawn 独立 handler。

**数据流**：

```
QUIC Connection (conn)
    │
    └─► accept_bi() 循环
            │
            ├─► Ok((send, recv)) → tokio::spawn(handle_incoming_stream(send, recv, base))
            │
            └─► Err(e) → 连接关闭，return
```

**关键代码**：

```47:67:novaic-app/src-tauri/p2p/src/tunnel.rs
pub async fn run_tunnel_server(conn: Connection, vmcontrol_base_url: String) {
    info!(
        "[Tunnel] Server: handling P2P connection from {}",
        conn.remote_address()
    );

    loop {
        match conn.accept_bi().await {
            Ok((send, recv)) => {
                let base = vmcontrol_base_url.clone();
                tokio::spawn(async move {
                    if let Err(e) = handle_incoming_stream(send, recv, &base).await {
                        warn!("[Tunnel] Stream handler error: {}", e);
                    }
                });
            }
            Err(e) => {
                info!("[Tunnel] Connection closed: {}", e);
                return;
            }
        }
    }
}
```

---

### 2.2 `handle_incoming_stream`（tunnel.rs:70–139）

**职责**：解析 stream 头部，按类型路由到 VNC / scrcpy。

**流协议**：

```
[stream_type: u8][id_len: u8][id: id_len bytes]
- 0x01: VNC
- 0x02: Scrcpy
```

**数据流**：

```
recv stream
    │
    ├─► read stream_type, id_len, id_bytes
    │
    ├─► 0x01 (VNC):
    │       ensure_vnc_endpoint(resource_id) → Unix socket 路径
    │       UnixStream::connect(path) → proxy_quic_to_unix(send, recv, unix)
    │
    ├─► 0x02 (Scrcpy):
    │       ws_url = {base}/api/android/scrcpy?device={resource_id}
    │       proxy_quic_to_ws(send, recv, ws_url)
    │
    └─► 其他: 写 ERR:unknown_stream_type
```

**关键代码**：

```70:139:novaic-app/src-tauri/p2p/src/tunnel.rs
async fn handle_incoming_stream(
    mut send: SendStream,
    mut recv: RecvStream,
    vmcontrol_base_url: &str,
) -> anyhow::Result<()> {
    // 读取流头部：[stream_type: u8][id_len: u8][id: bytes]
    let stream_type = recv.read_u8().await?;
    let id_len = recv.read_u8().await? as usize;
    // ...
    match stream_type {
        0x01 => {
            // VNC: ensure_vnc_endpoint 统一 maindesk/subuser，返回 Unix socket 路径
            match crate::vnc_endpoint::ensure_vnc_endpoint(&resource_id).await {
                Ok(socket_path) => {
                    let unix = UnixStream::connect(&socket_path).await?;
                    proxy_quic_to_unix(send, recv, unix).await?;
                }
                // ...
            }
        }
        0x02 => {
            // scrcpy：连接 VmControl 的 WS 端点，做 QUIC ↔ WS 桥接
            let ws_url = format!("{}/api/android/scrcpy?device={}", ...);
            proxy_quic_to_ws(send, recv, &ws_url).await?;
        }
        unknown => { /* ... */ }
    }
}
```

---

### 2.3 `open_vnc_stream`（tunnel.rs:266–278）

**职责**：手机侧发起 VNC 隧道连接，返回 `(SendStream, RecvStream)`。

**数据流**：

```
conn.open_bi() (15s 超时)
    │
    └─► write_stream_header(0x01, vm_id)
    │       [0x01][len][vm_id bytes]
    │
    └─► 返回 (send, recv) 供 bridge_ws_quic 桥接
```

**关键代码**：

```266:278:novaic-app/src-tauri/p2p/src/tunnel.rs
pub async fn open_vnc_stream(
    conn: &Connection,
    vm_id: &str,
) -> anyhow::Result<(SendStream, RecvStream)> {
    let (mut send, recv) = tokio::time::timeout(
        Duration::from_secs(OPEN_BI_TIMEOUT_SECS),
        conn.open_bi(),
    )
    .await
    .map_err(|_| anyhow::anyhow!("open_vnc_stream timed out after {}s", OPEN_BI_TIMEOUT_SECS))??;
    write_stream_header(&mut send, StreamType::Vnc as u8, vm_id).await?;
    info!("[Tunnel] Opened VNC stream for vm={}", vm_id);
    Ok((send, recv))
}
```

---

## 三、打洞是否已移除？当前远端连接是否仅走 relay？

**结论**：**打洞已移除，远端连接仅走 relay。**

| 证据 | 位置 |
|------|------|
| `relay.rs` 注释 | L3: `通过 relay 服务建立远端 QUIC 连接（打洞已移除）` |
| `relay.rs` 注释 | L154: `通过 relay 建立远端连接（打洞已移除，仅 relay）` |
| `client.rs` 注释 | L3: `打洞已移除，远端连接仅走 relay` |
| `client.rs` 注释 | L26: `远端连接：通过 relay 建立（打洞已移除）` |
| `hole_punch.rs` 注释 | L153: `connect_to_peer 用于本地 loopback；远端打洞已移除，仅 relay` |
| `vnc_proxy.rs` 注释 | L5–7: `本地与远端均使用 p2p（relay + tunnel，打洞已移除）` |
| `config.rs` 注释 | L46: `打洞移除后未使用，保留以兼容构造` |

**实际调用链**：

- **远端**：`P2pClient::connect` → `relay::connect_via_relay_only` → `relay_request` + `connect_via_relay`
- **本地**：`P2pClient::connect_direct` → `hole_punch::connect_to_peer`（127.0.0.1:19998）

`hole_punch.rs` 中的 `punch_and_connect` 已不存在；`relay_request` 替代 `locate` 作为远端发现入口。`hole_punch` 模块仍保留：
- `connect_to_peer`：本地 loopback
- `p2p_transport_config()`：relay 的 transport config
- `listen_for_peer` / `PunchListener`：PC 端 QUIC 监听（本地 P2P 端口）

---

## 四、Relay / Tunnel 调用链汇总

### 4.1 手机侧（Tauri Mobile）VNC 远端连接

```
VncProxy::serve_remote_vnc
    └─► get_or_create_remote_conn(device_id)
            └─► P2pClient::connect(gateway_url, token, device_id)
                    └─► relay::connect_via_relay_only(
                            gateway_url, jwt, target_device_id, relay_url_override)
                            ├─► rendezvous::relay_request(gateway_url, jwt, target_device_id)
                            │       POST /api/p2p/relay-request
                            │
                            └─► connect_via_relay(relay_url, jwt, session_id, RelayRole::Mobile)
                                    QUIC connect → open_bi → JSON handshake
    └─► tunnel::open_vnc_stream(&conn, agent_id)
            └─► conn.open_bi() → write_stream_header(0x01, agent_id)
    └─► bridge_ws_quic(ws, quic_send, quic_recv)
```

### 4.2 PC 侧（CloudBridge）Relay 入站

```
CloudBridge 收到 IncomingMessage::ConnectRelay { relay_url, session_id }
    └─► tokio::spawn(async {
            relay::connect_via_relay(relay_url, jwt, session_id, RelayRole::Pc { device_id })
            └─► QUIC connect → open_bi → JSON handshake
            └─► tunnel::run_tunnel_server(conn, vmcontrol_base_url)
                    └─► loop { conn.accept_bi() → handle_incoming_stream(send, recv, base) }
                            └─► stream_type 0x01: ensure_vnc_endpoint → UnixStream → proxy_quic_to_unix
```

### 4.3 本地 VNC（桌面 app）

```
VncProxy::serve_local_vnc
    └─► get_or_create_local_conn
            └─► P2pClient::connect_direct(127.0.0.1:19998, device_id, cert_der)
                    └─► hole_punch::connect_to_peer(addr, device_id, cert_der, timeout)
    └─► tunnel::open_vnc_stream(&conn, agent_id)
    └─► bridge_ws_quic(ws, quic_send, quic_recv)
```

---

## 五、关键代码位置速查

| 功能 | 文件 | 行号 |
|------|------|------|
| `connect_via_relay` | `p2p/src/relay.rs` | 49–151 |
| `connect_via_relay_only` | `p2p/src/relay.rs` | 156–239 |
| `relay_request` | `p2p/src/rendezvous.rs` | 247–295 |
| `run_tunnel_server` | `p2p/src/tunnel.rs` | 47–67 |
| `handle_incoming_stream` | `p2p/src/tunnel.rs` | 70–139 |
| `open_vnc_stream` | `p2p/src/tunnel.rs` | 266–278 |
| `proxy_quic_to_unix` | `p2p/src/tunnel.rs` | 144–176 |
| `proxy_quic_to_ws` | `p2p/src/tunnel.rs` | 185–256 |
| `write_stream_header` | `p2p/src/tunnel.rs` | 301–316 |
| CloudBridge 处理 ConnectRelay | `vmcontrol/src/cloud_bridge.rs` | 279–322 |
| `get_or_create_remote_conn` | `src/vnc_proxy.rs` | 455–508 |
| `P2pClient::connect` | `p2p/src/client.rs` | 27–40 |
