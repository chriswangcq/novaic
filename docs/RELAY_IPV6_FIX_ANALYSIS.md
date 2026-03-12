# Relay URL 解析问题分析报告

## 一、connect_via_relay 调用位置与 relay_url 来源

### 1.1 调用位置

| 位置 | 文件 | 行号 | 说明 |
|------|------|------|------|
| CloudBridge | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | 260-275 | 收到 `ConnectRelay` 消息时调用 |
| punch_or_relay | `novaic-app/src-tauri/p2p/src/relay.rs` | 190-195 | 打洞失败后走 relay 时调用 |
| P2pClient | `novaic-app/src-tauri/p2p/src/client.rs` | 54, 150 | 收到 Relay 端点时委托 `relay::connect_via_relay` |

### 1.2 relay_url 来源

1. **Gateway 推送（PC 侧）**：CloudBridge 收到 WebSocket 消息 `IncomingMessage::ConnectRelay { relay_url, session_id }`，`relay_url` 由 Gateway 在 `send_push_to_device(..., "connect_relay", {"relay_url": relay_url, "session_id": session_id})` 中携带。

2. **relay-request 响应（手机侧）**：`punch_or_relay` 调用 `rendezvous::relay_request()`，返回 `RelayRequestResponse { relay_url, session_id }`。`relay_url` 来自 Gateway 的 `POST /api/p2p/relay-request` 响应。

3. **Gateway 侧配置**：`novaic-gateway/gateway/api/p2p.py` 第 211 行：
   ```python
   relay_url = os.environ.get("RELAY_URL", "https://relay.gradievo.com/p2p/relay").strip()
   ```

4. **环境变量覆盖**：`NOVAIC_RELAY_URL` 可在 punch_or_relay 中覆盖 relay_request 返回的 relay_url（`relay_url_override`）。

---

## 二、IPv6 解析问题

### 2.1 问题位置

| 文件 | 行号 | 代码 |
|------|------|------|
| `p2p/src/relay.rs` | 49-51 | `format!("{}:{}", host, port).parse::<SocketAddr>()` |
| `vmcontrol/src/lib.rs` | 161-163 | `format!("{}:{}", host, port).parse::<SocketAddr>()` |

### 2.2 根因

- **IPv4 / 域名**：`format!("{}:{}", "relay.gradievo.com", 443)` → `"relay.gradievo.com:443"` ✓ 可解析
- **IPv6**：`format!("{}:{}", "::1", 443)` → `"::1:443"` ✗ **无法解析**

RFC 3986 / RFC 5952 规定：IPv6 在 host:port 中必须写成 `[::1]:443`，否则 `::1:443` 会被误解析（冒号歧义）。

当 `relay_url` 为 `https://[::1]:443/p2p/relay` 时：
- `url::Url::parse` 正确解析
- `host_str()` 返回 `"::1"`（不含方括号）
- `format!("{}:{}", "::1", 443)` → `"::1:443"` → `parse()` 失败

---

## 三、url::Url::parse 与 host_str() 行为

对 `https://relay.gradievo.com/p2p/relay`：

- `Url::parse()` 成功
- `host_str()` 返回 `Some("relay.gradievo.com")`（域名，无端口）
- `port()` 返回 `None`，`unwrap_or(443)` → 443

对 `https://[::1]:443/p2p/relay`：

- `host_str()` 返回 `Some("::1")`（IPv6 无方括号，RFC 5952 格式）
- `port()` 返回 `Some(443)`
- `format!("{}:{}", "::1", 443)` → `"::1:443"` → 解析失败

---

## 四、修复建议

### 4.1 relay.rs：parse_relay_url + connect_via_relay

**方案**：根据 host 是否为 IPv6，生成 `host:port` 或 `[host]:port`。

```rust
/// 解析 relay_url（如 https://relay.gradievo.com/p2p/relay）得到 host 和 port，
/// 并返回可直接 parse 成 SocketAddr 的 address 字符串（IPv6 使用 [host]:port 格式）。
fn parse_relay_url(relay_url: &str) -> anyhow::Result<(String, u16, String)> {
    let url = url::Url::parse(relay_url)
        .map_err(|e| anyhow::anyhow!("Invalid relay_url: {}", e))?;
    let host = url
        .host_str()
        .ok_or_else(|| anyhow::anyhow!("relay_url has no host"))?
        .to_string();
    let port = url.port().unwrap_or(443);
    // IPv6 必须用 [host]:port 格式，否则 "::1:443" 无法解析
    let addr_str = match url.host() {
        Some(url::Host::Ipv6(_)) => format!("[{}]:{}", host, port),
        _ => format!("{}:{}", host, port),
    };
    Ok((host, port, addr_str))
}
```

`connect_via_relay` 中：

```rust
let (host, _port, addr_str) = parse_relay_url(relay_url)?;
let addr: SocketAddr = addr_str
    .parse()
    .map_err(|e| anyhow::anyhow!("Invalid relay address: {}", e))?;
// endpoint.connect(addr, &host) 仍用 host 做 SNI
```

### 4.2 vmcontrol/lib.rs：bind 地址

若 `host` 可能为 IPv6（如 `::`、`::1`），同样需要区分：

```rust
let addr_str = if host.contains(':') {
    format!("[{}]:{}", host, port)
} else {
    format!("{}:{}", host, port)
};
let addr: SocketAddr = addr_str
    .parse()
    .map_err(|e| anyhow::anyhow!("Invalid address {}:{}: {}", host, port, e))?;
```

### 4.3 最小改动（仅 relay.rs）

若暂时不改 `parse_relay_url` 签名，可在 `connect_via_relay` 内直接处理：

```rust
let (host, port) = parse_relay_url(relay_url)?;
let addr_str = match host.contains(':') {
    true => format!("[{}]:{}", host, port),
    false => format!("{}:{}", host, port),
};
let addr: SocketAddr = addr_str
    .parse()
    .map_err(|e| anyhow::anyhow!("Invalid relay address: {}", e))?;
```

`host.contains(':')` 对域名和 IPv4 为 false，对 IPv6 为 true，可满足当前需求。

---

## 五、总结

| 问题 | 根因 | 修复 |
|------|------|------|
| `connect_via_relay` 调用 | CloudBridge 收到 connect_relay → 调用；punch_or_relay 打洞失败后调用 | 无需改 |
| `relay_url` 来源 | Gateway RELAY_URL / relay-request 返回；CloudBridge 推送 | 无需改 |
| IPv6 解析失败 | `format!("{}:{}", "::1", 443)` → `"::1:443"` 无法 parse | 对 IPv6 使用 `[host]:port` |
| `host_str()` 对 `https://relay.gradievo.com/p2p/relay` | 返回 `"relay.gradievo.com"` | 正常 |
