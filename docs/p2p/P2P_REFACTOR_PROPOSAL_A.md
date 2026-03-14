# P2P 模块化重构方案 A

> **范围**：`p2p` crate 与 vmcontrol 的集成，面向模块化、可配置、可扩展（含 Relay 兜底）。

---

## 一、现状分析

### 1.1 模块结构

| 模块 | 职责 | 调用方 |
|------|------|--------|
| `device_id` | Ed25519 身份加载/生成 | vmcontrol, lib.rs |
| `types` | VmControlService, DiscoveryEvent | vmcontrol, local_discovery |
| `local_discovery` | mDNS 广播/发现 | vmcontrol |
| `crypto` | TLS 证书生成、cert pinning | vmcontrol, hole_punch, lib.rs |
| `rendezvous` | STUN 外网地址、Gateway 心跳、locate | vmcontrol, hole_punch |
| `hole_punch` | QUIC 监听、连接、punch_and_connect | vmcontrol, vnc_proxy |
| `tunnel` | QUIC 流多路复用（VNC/scrcpy） | vmcontrol, vnc_proxy |

### 1.2 紧耦合点

```
vmcontrol/lib.rs::setup_p2p_server()
├── p2p::device_id::DeviceIdentity::load_or_generate
├── p2p::crypto::generate_server_tls
├── p2p::rendezvous::get_external_addr
├── p2p::hole_punch::listen_for_peer
├── p2p::rendezvous::run_heartbeat_loop
└── p2p::tunnel::run_tunnel_server
```

- **P2P_PORT=19998** 硬编码于 `vmcontrol/lib.rs`、`vnc_proxy.rs`、`hole_punch.rs` 注释
- **流程固定**：STUN → QUIC bind → heartbeat → accept，无法替换或跳过某一步
- **无抽象层**：vmcontrol 直接依赖 5 个 p2p 子模块

### 1.3 调用链概览

```
PC 侧（vmcontrol）:
  start_embedded_server
    → setup_p2p_server（内联 60+ 行）
      → device_id, crypto, rendezvous, hole_punch, tunnel

手机侧（vnc_proxy）:
  get_or_create_remote_conn → punch_and_connect（hole_punch）
  get_or_create_local_conn  → connect_to_peer（hole_punch）
  serve_*_vnc/scrcpy       → tunnel::open_vnc_stream / open_scrcpy_stream
```

---

## 二、模块边界与职责划分

### 2.1 目标分层

```
┌─────────────────────────────────────────────────────────────────┐
│  vmcontrol / vnc_proxy（调用方）                                   │
│  仅依赖 P2pServer / P2pClient 抽象，不直接 import p2p::* 子模块    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  p2p::server / p2p::client（统一入口）                             │
│  P2pServer, P2pClient 结构体，封装配置与生命周期                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  p2p 内部子模块（可插拔）                                          │
│  stun, transport, rendezvous, tunnel                             │
│  通过 trait 或策略注入，支持替换实现                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责表（重构后）

| 模块 | 职责 | 依赖 |
|------|------|------|
| **p2p::server** | P2P 服务端：启动、配置、生命周期 | stun, transport, rendezvous, tunnel |
| **p2p::client** | P2P 客户端：连接、打洞、Relay 兜底 | transport, rendezvous, tunnel |
| **p2p::stun** | 外网地址获取（从 rendezvous 抽离） | 无 |
| **p2p::transport** | QUIC 监听/连接（从 hole_punch 重命名） | crypto |
| **p2p::rendezvous** | Gateway 心跳、locate（仅 HTTP API） | 无 |
| **p2p::tunnel** | 流协议不变 | 无 |
| **p2p::relay** | 新增：Relay 连接（未来） | transport, tunnel |

---

## 三、抽象层设计

### 3.1 P2pServer 结构体

```rust
// p2p/src/server.rs

/// P2P 服务端配置（可配置端口、STUN、心跳间隔等）
#[derive(Clone)]
pub struct P2pServerConfig {
    pub port: u16,
    pub stun_server: Option<String>,      // None = 默认 stun.gradievo.com:3478
    pub heartbeat_interval_secs: u64,   // 默认 25
    pub stun_retry_interval_secs: u64,   // 默认 300
}

impl Default for P2pServerConfig {
    fn default() -> Self {
        Self {
            port: 19998,
            stun_server: None,
            heartbeat_interval_secs: 25,
            stun_retry_interval_secs: 300,
        }
    }
}

/// P2P 服务端：封装 STUN、QUIC 绑定、心跳、accept 全流程
pub struct P2pServer {
    config: P2pServerConfig,
    data_dir: PathBuf,
}

impl P2pServer {
    pub fn new(config: P2pServerConfig, data_dir: PathBuf) -> Self { ... }

    /// 启动 P2P 服务端，返回 (LocalVmControlInfo, shutdown_handle)
    /// 调用方负责在 graceful shutdown 时调用 shutdown_handle
    pub async fn start(
        &self,
        cloud_config: Option<&CloudBridgeConfig>,
        vmcontrol_http_port: u16,
    ) -> anyhow::Result<(LocalVmControlInfo, P2pShutdownHandle)> {
        // 1. 加载 identity + 生成 TLS
        // 2. STUN（可配置跳过或自定义服务器）
        // 3. 绑定 QUIC
        // 4. 启动 heartbeat（若有 cloud_config）
        // 5. 启动 accept loop
        // 返回 LocalVmControlInfo 供 VncProxy 注册
    }
}
```

**vmcontrol 调用**：

```rust
// vmcontrol/lib.rs

let p2p_config = P2pServerConfig {
    port: std::env::var("NOVAIC_P2P_PORT").ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(19998),
    ..Default::default()
};

let p2p_server = P2pServer::new(p2p_config, data_dir.clone());
let (local_info, p2p_shutdown) = p2p_server.start(cloud_config.as_ref(), actual_addr.port()).await?;

// 在 graceful shutdown 时
let _ = p2p_shutdown.send(());
```

### 3.2 P2pClient 结构体

```rust
// p2p/src/client.rs

/// 连接策略：直连 / Relay 兜底 / 仅 Relay
#[derive(Clone, Copy)]
pub enum ConnectStrategy {
    DirectOnly,           // 当前行为：打洞失败即报错
    DirectThenRelay,      // 打洞 15s 超时后走 Relay（未来）
    RelayOnly,            // 仅 Relay（未来）
}

/// P2P 客户端配置
#[derive(Clone)]
pub struct P2pClientConfig {
    pub connect_strategy: ConnectStrategy,
    pub punch_timeout_secs: u64,   // 默认 15
    pub relay_url: Option<String>, // 未来：relay.gradievo.com
}

/// P2P 客户端：连接远端 PC
pub struct P2pClient {
    config: P2pClientConfig,
}

impl P2pClient {
    pub fn new(config: P2pClientConfig) -> Self { ... }

    /// 连接远端设备：Gateway locate + 打洞（+ 可选 Relay 兜底）
    pub async fn connect(
        &self,
        gateway_url: &str,
        jwt: &str,
        target_device_id: &str,
    ) -> anyhow::Result<Connection> {
        let locate = rendezvous::locate(gateway_url, jwt, target_device_id).await?;
        // ... 校验 ext_addr、cert ...
        match self.config.connect_strategy {
            ConnectStrategy::DirectOnly => {
                hole_punch::connect_to_peer(addr, target_device_id, &cert_bytes).await
            }
            ConnectStrategy::DirectThenRelay => {
                // 先尝试打洞，15s 超时后 fallback relay（未来实现）
                todo!("relay fallback")
            }
            _ => ...
        }
    }
}
```

**vnc_proxy 调用**：

```rust
// vnc_proxy.rs

let p2p_client = P2pClient::new(P2pClientConfig::default());
let conn = p2p_client.connect(&gateway_url, &token, device_id).await?;
```

### 3.3 LocalVmControlInfo 归属

```rust
// p2p/src/server.rs 或 p2p::types

pub struct LocalVmControlInfo {
    pub device_id: String,
    pub cert_der: Vec<u8>,
    pub port: u16,  // 新增：便于 vnc_proxy 使用 127.0.0.1:{port}
}
```

- 从 `vnc_proxy::LocalVmControlInfo` 迁移到 `p2p`，或保留在 vnc_proxy 但由 `P2pServer::start` 返回填充。

---

## 四、可插拔 / 可配置设计

### 4.1 STUN 可配置

```rust
// p2p/src/stun.rs（从 rendezvous 抽离）

pub trait StunProvider: Send + Sync {
    async fn get_external_addr(&self, local_port: u16) -> anyhow::Result<SocketAddr>;
}

/// 默认实现：RFC 5389 STUN
pub struct DefaultStunProvider {
    server: String,  // 从 NOVAIC_STUN_SERVER 或默认 stun.gradievo.com:3478
}

impl StunProvider for DefaultStunProvider { ... }

/// 测试用：固定返回
pub struct MockStunProvider(pub SocketAddr);
impl StunProvider for MockStunProvider { ... }
```

`P2pServerConfig` 可扩展：

```rust
pub struct P2pServerConfig {
    // ...
    pub stun_provider: Option<Arc<dyn StunProvider>>,  // None = 使用 DefaultStunProvider
}
```

### 4.2 传输层可配置（预留）

```rust
// p2p/src/transport.rs

pub trait TransportListener: Send + Sync {
    async fn accept(&self, timeout: Duration) -> anyhow::Result<Box<dyn TransportConnection>>;
    fn close(&self);
}

pub trait TransportConnection: Send + Sync {
    fn remote_address(&self) -> SocketAddr;
    async fn open_bi(&self) -> anyhow::Result<(SendStream, RecvStream)>;
    // ...
}
```

- 当前仅实现 `QuicTransportListener`（包装现有 `hole_punch::listen_for_peer`）
- 未来可增加 `RelayTransportListener` 用于 Relay 模式

### 4.3 心跳可配置

```rust
pub struct P2pServerConfig {
    // ...
    pub heartbeat_interval_secs: u64,
    pub heartbeat_enabled: bool,  // 无 cloud_config 时自动 false
}
```

### 4.4 Accept 循环可配置

```rust
// P2pServerConfig

pub struct P2pServerConfig {
    // ...
    pub accept_idle_timeout_secs: u64,  // 默认 300
    pub connection_handler: Option<Arc<dyn Fn(Connection) + Send + Sync>>,  // 可选自定义
}
```

- 默认使用 `tunnel::run_tunnel_server`
- 测试时可注入 mock handler

---

## 五、Relay 兜底集成

### 5.1 连接策略扩展

```rust
// 当 ConnectStrategy::DirectThenRelay 时

pub async fn connect(&self, ...) -> anyhow::Result<Connection> {
    let locate = rendezvous::locate(...).await?;

    // 1. 尝试直连
    let direct_result = tokio::time::timeout(
        Duration::from_secs(self.config.punch_timeout_secs),
        hole_punch::connect_to_peer(addr, target_device_id, &cert_bytes)
    ).await;

    if let Ok(Ok(conn)) = direct_result {
        return Ok(conn);
    }

    // 2. 超时或失败 → Relay
    if let Some(relay_url) = &self.config.relay_url {
        return relay::connect_via_relay(relay_url, gateway_url, jwt, target_device_id).await;
    }

    Err(anyhow!("P2P failed and relay not configured"))
}
```

### 5.2 Relay 模块接口（预留）

```rust
// p2p/src/relay.rs（未来新增）

pub async fn connect_via_relay(
    relay_url: &str,
    gateway_url: &str,
    jwt: &str,
    target_device_id: &str,
) -> anyhow::Result<Connection> {
    // 1. POST /api/p2p/relay-request { target_device_id }
    // 2. 收到 { relay_url, session_id }
    // 3. QUIC 连接 relay，发送 ConnectRequest { target_device_id, jwt, session_id }
    // 4. relay 配对后返回 stream，复用 tunnel 协议
    todo!("see DESIGN-novaic-quic-service.md")
}
```

### 5.3 与 tunnel 的兼容

- Relay 复用 `tunnel::open_vnc_stream`、`open_scrcpy_stream` 协议
- `Connection` 类型统一（quinn::Connection），调用方无感知

---

## 六、端口配置统一

### 6.1 配置来源优先级

```rust
// 1. 环境变量 NOVAIC_P2P_PORT
// 2. 配置文件（未来）
// 3. 默认 19998

pub fn resolve_p2p_port() -> u16 {
    std::env::var("NOVAIC_P2P_PORT")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(19998)
}
```

### 6.2 消除硬编码

| 位置 | 修改 |
|------|------|
| vmcontrol/lib.rs | `const P2P_PORT` → `P2pServerConfig::default().port` 或 `resolve_p2p_port()` |
| vnc_proxy.rs | `LOCAL_P2P_PORT` → 从 `LocalVmControlInfo.port` 或共享配置读取 |
| vnc_proxy 本地连接 | `127.0.0.1:{LocalVmControlInfo.port}` |

---

## 七、目录结构建议

```
p2p/
├── Cargo.toml
├── src/
│   ├── lib.rs
│   ├── config.rs      # P2pServerConfig, P2pClientConfig, resolve_p2p_port
│   ├── server.rs      # P2pServer（新）
│   ├── client.rs      # P2pClient（新）
│   ├── stun.rs        # 从 rendezvous 抽离 STUN（可选，或保留在 rendezvous）
│   ├── transport.rs  # hole_punch 重命名，或保留 hole_punch 作为内部实现
│   ├── rendezvous.rs # 仅心跳、locate、relay-request
│   ├── tunnel.rs     # 不变
│   ├── crypto.rs     # 不变
│   ├── device_id.rs  # 不变
│   ├── types.rs      # 不变，可增加 LocalVmControlInfo
│   ├── local_discovery.rs
│   └── relay.rs      # 未来：Relay 连接
```

### 7.1 lib.rs 导出

```rust
// p2p/src/lib.rs

pub mod config;
pub mod server;
pub mod client;
pub mod device_id;
pub mod types;
pub mod local_discovery;
pub mod crypto;
pub mod rendezvous;
pub mod hole_punch;  // 或 transport
pub mod tunnel;

pub use config::{P2pServerConfig, P2pClientConfig, ConnectStrategy};
pub use server::P2pServer;
pub use client::P2pClient;
pub use types::LocalVmControlInfo;  // 若迁移至此
```

---

## 八、迁移步骤建议

1. **Phase 1**：在 p2p 内新增 `server.rs`、`client.rs`、`config.rs`，封装现有逻辑，vmcontrol 逐步改为调用 `P2pServer`，vnc_proxy 改为调用 `P2pClient`。
2. **Phase 2**：端口配置化，STUN 可配置，心跳/accept 参数可配置。
3. **Phase 3**：抽离 STUN trait、预留 Transport trait，为 Relay 做准备。
4. **Phase 4**：实现 `relay.rs` 与 `ConnectStrategy::DirectThenRelay`。

---

## 九、总结

| 目标 | 方案 |
|------|------|
| 模块边界 | server/client 作为统一入口，vmcontrol/vnc_proxy 仅依赖 p2p::server、p2p::client |
| 抽象层 | P2pServer、P2pClient 结构体 + P2pServerConfig、P2pClientConfig |
| 可配置 | 端口、STUN、心跳间隔、accept 超时、连接策略 |
| 可插拔 | StunProvider trait、预留 Transport trait |
| Relay 兜底 | ConnectStrategy::DirectThenRelay，P2pClient 内 15s 超时后走 relay |
| 端口 | NOVAIC_P2P_PORT 环境变量，默认 19998 |
