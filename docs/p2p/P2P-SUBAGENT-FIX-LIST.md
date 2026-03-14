# P2P 修复清单 — 前 4 个 Subagent 发现汇总

> 基于 P2P-PHASE4-CODE-REVIEW-REPORT.md 及 subagent 1–4 的专项分析整理。
> 重点关注：relay URL 解析（IPv6）、P2P registry 响应、CloudBridge 与 p2p relay 的关系。

---

## 一、问题与修复对照表

| # | 问题 | 严重度 | 涉及文件 | 修改内容 |
|---|------|--------|----------|----------|
| 1 | relay URL IPv6 解析错误 | 高 | relay.rs | 对 IPv6 host 使用 `[host]:port` 格式 |
| 2 | CloudBridge 使用建连时 token 快照，JWT 可能过期 | 高 | cloud_bridge.rs | ConnectRelay 时从 cloud_token 重新读取 |
| 3 | CloudBridge 直接 import p2p::relay，违反分层 | 中 | cloud_bridge.rs | 改用 P2pClient::connect_via_relay |
| 4 | spawn 内错误不传播，手机侧无失败反馈 | 中 | cloud_bridge.rs | 向 Gateway 发送 relay_connect_failed |
| 5 | P2P registry heartbeat 响应解析失败（missing field `ok`） | 中 | rendezvous.rs / p2p.py | 先检查 status，错误响应单独处理 |
| 6 | tunnel resource_id 超 255 字节导致 u8 溢出 | 高 | tunnel.rs | 校验 resource_id.len() <= 255 |

---

## 二、具体修改内容

### 1. `novaic-app/src-tauri/p2p/src/relay.rs` — relay URL 解析（IPv6）

**问题**：`https://[::1]:443/p2p/relay` 时，`format!("{}:{}", "::1", 443)` → `"::1:443"` 无法被 `SocketAddr::parse` 解析。IPv6 地址需使用 `[host]:port` 格式。

**修改**：

```rust
// 原 parse_relay_url 返回 (host, port)，connect_via_relay 中：
// let addr: SocketAddr = format!("{}:{}", host, port).parse()...

// 修改 parse_relay_url，使其返回可直接用于 SocketAddr 的 addr_str：
fn parse_relay_url(relay_url: &str) -> anyhow::Result<(String, u16, String)> {
    let url = url::Url::parse(relay_url)
        .map_err(|e| anyhow::anyhow!("Invalid relay_url: {}", e))?;
    let host = url
        .host_str()
        .ok_or_else(|| anyhow::anyhow!("relay_url has no host"))?
        .to_string();
    let port = url.port().unwrap_or(443);
    // IPv6 需 [host]:port 格式
    let addr_str = if host.contains(':') {
        format!("[{}]:{}", host, port)
    } else {
        format!("{}:{}", host, port)
    };
    Ok((host, port, addr_str))
}

// connect_via_relay 中：
let (host, _port, addr_str) = parse_relay_url(relay_url)?;
let addr: SocketAddr = addr_str
    .parse()
    .map_err(|e| anyhow::anyhow!("Invalid relay address: {}", e))?;
```

---

### 2. `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` — JWT 重新读取 + 分层 + 错误反馈

**问题 1**：ConnectRelay 使用 `connect_and_run` 入参 `token`，长连接下 JWT 可能已过期。

**修改**：将 `cloud_token: Arc<tokio::sync::RwLock<String>>` 传入 `connect_and_run`，在 ConnectRelay 分支内重新读取：

```rust
// connect_and_run 签名增加 cloud_token 参数
async fn connect_and_run(
    ws_url: &str,
    vmcontrol_base_url: &str,
    token: &str,
    device_id: &str,
    cloud_token: Arc<tokio::sync::RwLock<String>>,  // 新增
    http_client: &reqwest::Client,
)

// ConnectRelay 分支内：
IncomingMessage::ConnectRelay { relay_url, session_id } => {
    let cloud_token = Arc::clone(&cloud_token);  // 需在调用 connect_and_run 时传入
    let relay_url = relay_url.clone();
    let session_id = session_id.clone();
    let base = vmcontrol_base_url.to_string();
    let did = device_id.to_string();
    let sink_clone = Arc::clone(&sink);
    tokio::spawn(async move {
        let jwt = cloud_token.read().await.clone();  // 重新读取最新 token
        if jwt.is_empty() {
            tracing::warn!("[CloudBridge] connect_via_relay: token empty, skip");
            return;
        }
        match p2p::P2pClient::connect_via_relay(  // 改用 P2pClient（见下）
            &relay_url,
            &jwt,
            &session_id,
            p2p::RelayRole::Pc { device_id: did.clone() },
        )
        .await
        {
            Ok(conn) => {
                tracing::info!("[CloudBridge] Relay connected, starting tunnel server");
                p2p::tunnel::run_tunnel_server(conn, base).await;
            }
            Err(e) => {
                tracing::warn!("[CloudBridge] connect_via_relay failed: {}", e);
                // TODO: 向 Gateway 发送 relay_connect_failed（需扩展 OutgoingMessage）
            }
        }
    });
    continue;
}
```

**问题 2**：直接 `p2p::relay::connect_via_relay` 违反分层。p2p lib 已导出 `connect_via_relay`，可改为 `p2p::connect_via_relay` 或 `p2p::P2pClient::connect_via_relay`（client 已有静态方法）。

**修改**：使用 `p2p::connect_via_relay`（lib.rs 已 `pub use relay::connect_via_relay`）。

**问题 3**：spawn 内错误不传播。需扩展 `OutgoingMessage` 增加 `relay_connect_failed`，并在 Gateway 侧处理（可选，需 Gateway 配合）。

---

### 3. `novaic-app/src-tauri/p2p/src/rendezvous.rs` — heartbeat 响应解析

**问题**：当 Gateway 返回 401/403 等错误时，响应体为 `{"detail":"..."}`，无 `ok` 字段。客户端直接 `resp.json::<HeartbeatResponse>()` 会报 `missing field 'ok'`。

**修改**：先检查 `resp.status().is_success()`，失败时解析 `detail` 并返回明确错误：

```rust
// heartbeat 函数内：
Ok(resp) => {
    let status = resp.status();
    let body_text = resp.text().await?;
    if !status.is_success() {
        let detail = serde_json::from_str::<serde_json::Value>(&body_text)
            .ok()
            .and_then(|v| v.get("detail").and_then(|d| d.as_str()).map(String::from))
            .unwrap_or_else(|| body_text);
        anyhow::bail!("Heartbeat failed ({}): {}", status, detail);
    }
    let parsed: HeartbeatResponse = serde_json::from_str(&body_text)?;
    return Ok(parsed);
}
```

---

### 4. `novaic-app/src-tauri/p2p/src/tunnel.rs` — resource_id 长度校验

**问题**：`write_stream_header` 中 `id_len = resource_id.as_bytes().len() as u8`，超过 255 会溢出。

**修改**：

```rust
async fn write_stream_header(
    send: &mut SendStream,
    stream_type: u8,
    resource_id: &str,
) -> anyhow::Result<()> {
    let id_bytes = resource_id.as_bytes();
    if id_bytes.len() > 255 {
        anyhow::bail!("resource_id too long (max 255 bytes): {} bytes", id_bytes.len());
    }
    send.write_u8(stream_type).await?;
    send.write_u8(id_bytes.len() as u8).await?;
    send.write_all(id_bytes).await?;
    Ok(())
}
```

---

### 5. `novaic-gateway/gateway/api/p2p.py` — P2P registry 响应

**现状**：`HeartbeatResponse` 已有 `ok: bool`，`return HeartbeatResponse(ok=True)` 正确。问题主要出在客户端对非 2xx 响应的解析。若 Gateway 在认证失败时返回 `{"detail":"..."}`，客户端需按上文 rendezvous 修改处理。

**可选**：确保所有错误响应格式一致，便于客户端区分。

---

## 三、CloudBridge 与 p2p relay 的关系（设计澄清）

| 组件 | 职责 | 与 relay 的关系 |
|------|------|------------------|
| **CloudBridge** | 维持 Gateway WebSocket，转发 proxy_request、connect_relay 等 | 收到 `connect_relay` 后调用 `p2p::connect_via_relay`，建立 PC→relay 连接，再 spawn `run_tunnel_server` |
| **P2pClient** | 手机侧 discovery + punch + relay | `punch_or_relay` 打洞失败后调 `relay_request` 拿 session_id，再 `connect_via_relay`（Mobile 角色） |
| **relay (novaic-quic-service)** | 中继 QUIC 连接 | PC 先 RegisterPc，手机后 ConnectRequest；手机侧已有 2s/4s/8s 重试缓解竞态 |

**关系**：CloudBridge 是 PC 端接收 Gateway 推送的入口；relay 连接由 p2p 模块建立，CloudBridge 只负责触发调用并传入最新 JWT。

---

## 四、修复优先级建议

1. **立即**：relay IPv6 解析（#1）、tunnel resource_id 校验（#6）
2. **短期**：CloudBridge JWT 重新读取（#2）、heartbeat 错误响应处理（#5）
3. **中期**：CloudBridge 改用 p2p 顶层 API（#3）、relay_connect_failed 反馈（#4）
