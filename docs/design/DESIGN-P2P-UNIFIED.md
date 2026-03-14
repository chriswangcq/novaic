# NovAIC P2P 架构统一设计

> 汇总讨论：novaic-quic-service、p2p 模块化、注册与发现、Relay 兜底。组件化、非业务化、可扩展。

---

## 一、总览

### 1.1 架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               NovAIC P2P 架构                                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │  业务层（vmcontrol, vnc_proxy, CloudBridge）                                       │   │
│  │  仅依赖 P2pServer / P2pClient，不直接 import p2p 子模块                            │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                               │
│  ┌──────────────────────────────────────▼──────────────────────────────────────────┐   │
│  │  p2p 统一入口                                                                      │   │
│  │  P2pServer（Registry 注入）  │  P2pClient（Discovery 注入，ConnectStrategy）      │   │
│  └──────────────────────────────────────┬──────────────────────────────────────────┘   │
│                                          │                                               │
│  ┌──────────────────────────────────────▼──────────────────────────────────────────┐   │
│  │  注册与发现（trait 抽象）                                                           │   │
│  │  Registry: GatewayRegistry, MdnsRegistry  │  Discovery: GatewayDiscovery, MdnsDiscovery │   │
│  └──────────────────────────────────────┬──────────────────────────────────────────┘   │
│                                          │                                               │
│  ┌──────────────────────────────────────▼──────────────────────────────────────────┐   │
│  │  传输层                                                                           │   │
│  │  stun | transport (hole_punch) | tunnel | relay                                    │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  外部服务                                                                                 │
│  api.gradievo.com (Gateway)  │  stun.gradievo.com (STUN)  │  relay.gradievo.com (Relay)  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **组件化** | Registry/Discovery 为 trait，P2pServer/P2pClient 为统一入口，可替换、可组合 |
| **非业务化** | ServerDescriptor.id 无业务语义，endpoint 仅描述连接方式（Direct/Relay） |
| **可配置** | 端口、STUN、心跳、连接策略均通过 Config 注入 |
| **可扩展** | 新增 Relay、新 Registry 后端只需实现 trait |

---

## 二、novaic-quic-service（STUN + Relay）

### 2.1 定位

- **STUN**：stun.gradievo.com:3478（RFC 5389 标准），PC 获取 ext_addr
- **Relay**：relay.gradievo.com（HTTPS 443 默认），P2P 失败时兜底

### 2.2 端口约定

| 服务 | 域名 | 端口 | 说明 |
|------|------|------|------|
| STUN | stun.gradievo.com | 3478 | RFC 5389 标准默认 |
| Relay | relay.gradievo.com | 443 | HTTPS 默认，路径 `/p2p/relay` |

### 2.3 Relay 流程

```
手机 punch 超时(15s)
  → POST /api/p2p/relay-request { target_device_id }
  → Gateway 推 connect_relay 给 PC，返回 { relay_url, session_id } 给手机
  → PC 连接 relay (RegisterPc)
  → 手机连接 relay (ConnectRequest)
  → relay 配对，转发 stream（复用 tunnel 协议）
```

### 2.4 详细设计

见 `docs/DESIGN-novaic-quic-service.md`、`docs/DESIGN-novaic-quic-service-IMPLEMENTATION.md`。

---

## 三、p2p 模块化（方案 A）

### 3.1 分层

```
业务层 (vmcontrol, vnc_proxy)
        │
        ▼
P2pServer / P2pClient（统一入口）
        │
        ▼
Registry / Discovery（注册与发现）
        │
        ▼
stun, transport, tunnel, relay（传输）
```

### 3.2 P2pServer

```rust
pub struct P2pServerConfig {
    pub port: u16,                          // 默认 19998，可 NOVAIC_P2P_PORT
    pub stun_server: Option<String>,         // None = stun.gradievo.com:3478
    pub registry: Option<Arc<dyn Registry>>, // None = 不注册
    pub registry_interval_secs: u64,         // 默认 25
    pub stun_retry_interval_secs: u64,       // 默认 300
}

pub struct P2pServer { ... }

impl P2pServer {
    /// 返回 (LocalVmControlInfo, P2pShutdownHandle)
    pub async fn start(&self, ...) -> Result<(LocalVmControlInfo, P2pShutdownHandle)>;
}
```

**流程**：STUN → QUIC bind → 启动 registry 心跳（若注入）→ accept loop → 每连接 spawn `run_tunnel_server`。

### 3.3 P2pClient

```rust
pub enum ConnectStrategy {
    DirectOnly,        // 打洞失败即报错
    DirectThenRelay,   // 15s 超时后走 Relay
    RelayOnly,
}

pub struct P2pClientConfig {
    pub discovery: Arc<dyn Discovery>,
    pub connect_strategy: ConnectStrategy,
    pub punch_timeout_secs: u64,
    pub relay_url: Option<String>,
}

pub struct P2pClient { ... }

impl P2pClient {
    pub async fn connect(&self, target_id: &str) -> Result<Connection>;
}
```

**流程**：`discovery.lookup(target_id)` → 按 `EndpointInfo` 直连或 relay → 返回 `Connection`。

### 3.4 connect_relay 归属（PC 端）

- **CloudBridge**：解析 `ConnectRelay` 消息，调用 `P2pClient::connect_via_relay(relay_url, session_id)` 或等价接口
- **P2pClient**：提供 `connect_via_relay` 方法，供 CloudBridge 调用；建连后 spawn `run_tunnel_server`
- **共享**：PC 端 relay 连接为「入站」，由 `run_tunnel_server` 处理 stream，无需与 VncProxy 共享

---

## 四、注册与发现

### 4.1 核心类型

```rust
#[derive(Clone, Debug)]
pub struct ServerDescriptor {
    pub id: String,
    pub endpoint: EndpointInfo,
    pub metadata: HashMap<String, String>,
}

pub enum EndpointInfo {
    Direct(SocketAddr),
    Relay { relay_url: String, session_id: String },
}

#[async_trait]
pub trait Registry: Send + Sync {
    async fn register(&self, d: &ServerDescriptor) -> Result<()>;
    async fn unregister(&self, id: &str) -> Result<()>;
}

#[async_trait]
pub trait Discovery: Send + Sync {
    async fn lookup(&self, id: &str) -> Result<Option<ServerDescriptor>>;
}
```

### 4.2 后端实现

| 后端 | Registry | Discovery | 范围 |
|------|----------|-----------|------|
| Gateway | heartbeat API | locate API | 云端 |
| mDNS | advertise | discover / stream | 局域网 |
| Relay | 未来 | relay-request 返回 | relay |

### 4.3 组合

- **CompositeRegistry**：多后端并行注册
- **CompositeDiscovery**：多后端级联 lookup（如先 mDNS 再 Gateway）

### 4.4 与 P2pServer / P2pClient 集成

- **P2pServer**：构造 `ServerDescriptor`，定期 `registry.register(&descriptor)`
- **P2pClient**：`discovery.lookup(id)` 得到 `ServerDescriptor`，按 `endpoint` 决定连接方式

---

## 五、目录结构

### 5.1 p2p crate

```
p2p/
├── src/
│   ├── lib.rs
│   ├── config.rs           # P2pServerConfig, P2pClientConfig, ConnectStrategy
│   ├── server.rs           # P2pServer
│   ├── client.rs           # P2pClient
│   ├── types.rs            # ServerDescriptor, EndpointInfo, LocalVmControlInfo
│   ├── registry/
│   │   ├── mod.rs          # Registry trait, CompositeRegistry
│   │   ├── gateway.rs      # GatewayRegistry
│   │   └── mdns.rs         # MdnsRegistry
│   ├── discovery/
│   │   ├── mod.rs          # Discovery trait, CompositeDiscovery
│   │   ├── gateway.rs     # GatewayDiscovery
│   │   └── mdns.rs         # MdnsDiscovery
│   ├── stun.rs             # 从 rendezvous 抽离
│   ├── transport.rs        # hole_punch 重命名
│   ├── rendezvous.rs       # heartbeat, locate HTTP 实现（供 GatewayRegistry/Discovery 用）
│   ├── tunnel.rs
│   ├── relay.rs            # connect_via_relay, punch_or_relay
│   ├── crypto.rs
│   ├── device_id.rs
│   └── local_discovery.rs
```

### 5.2 novaic-quic-service

```
novaic-quic-service/
├── src/
│   ├── main.rs
│   ├── config.rs
│   ├── stun.rs
│   ├── relay.rs
│   ├── protocol.rs
│   └── auth.rs
```

---

## 六、配置汇总

### 6.1 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| NOVAIC_P2P_PORT | 19998 | P2P QUIC 端口 |
| NOVAIC_STUN_SERVER | stun.gradievo.com:3478 | STUN 服务器 |
| NOVAIC_RELAY_URL | - | Relay URL（如 https://relay.gradievo.com/p2p/relay） |

### 6.2 Gateway 配置

| 配置 | 说明 |
|------|------|
| RELAY_URL | https://relay.gradievo.com/p2p/relay |

### 6.3 novaic-quic-service 配置

| 配置 | 说明 |
|------|------|
| GATEWAY_URL | Gateway 地址（relay 鉴权调用） |
| STUN_PORT | 3478 |
| RELAY_LISTEN | 443 或内部端口 |

---

## 七、实施阶段

### Phase 1：p2p 基础抽象（2–3 周）

1. 新增 `p2p::server`、`p2p::client`、`p2p::config`
2. 实现 `P2pServer`、`P2pClient`，封装现有逻辑
3. vmcontrol 改用 `P2pServer`，vnc_proxy 改用 `P2pClient`
4. 端口配置化（NOVAIC_P2P_PORT）

### Phase 2：注册与发现抽象（2 周）

1. 新增 `ServerDescriptor`、`EndpointInfo`、`Registry`、`Discovery` trait
2. 实现 `GatewayRegistry`、`GatewayDiscovery`（包装现有 heartbeat/locate）
3. 实现 `MdnsRegistry`、`MdnsDiscovery`（包装 local_discovery）
4. `P2pServerConfig.registry`、`P2pClientConfig.discovery` 注入

### Phase 3：novaic-quic-service（3–4 周）

1. 新建 novaic-quic-service 项目
2. 实现 STUN 模块
3. 实现 Relay 模块（HTTP/3、鉴权、配对、stream 转发）
4. Gateway 新增 relay-request、send_push_to_device、validate-device

### Phase 4：Relay 兜底（2 周）

1. p2p 新增 `relay.rs`：`connect_via_relay`、`punch_or_relay`
2. `P2pClient` 支持 `ConnectStrategy::DirectThenRelay`
3. CloudBridge 处理 `connect_relay`，调用 `connect_via_relay` 并 spawn `run_tunnel_server`
4. vnc_proxy 使用 `P2pClient::connect`（内部自动 punch_or_relay）

### Phase 5：部署与收尾（1 周）✅

1. novaic-quic-service 部署（stun.gradievo.com、relay.gradievo.com）— 见 `docs/PHASE5-DEPLOYMENT.md`
2. 支持生产 TLS 证书（RELAY_TLS_CERT_PATH / RELAY_TLS_KEY_PATH）
3. 部署脚本：`novaic-quic-service/deploy/deploy.sh`

---

## 八、数据流总览

### 8.1 PC 启动

```
VmControl start_embedded_server
  → P2pServer::start(config)
    → STUN 获取 ext_addr
    → QUIC bind
    → registry.register(ServerDescriptor { id, endpoint: Direct(addr), metadata: { cert_der_b64 } })
    → 启动 registry 心跳循环（每 25s）
    → accept loop → run_tunnel_server
```

### 8.2 手机连接（直连成功）

```
VncProxy get_or_create_remote_conn(device_id)
  → P2pClient::connect(device_id)
    → discovery.lookup(device_id)  // GatewayDiscovery
    → ServerDescriptor { endpoint: Direct(addr), metadata: { cert_der_b64 } }
    → connect_to_peer(addr, device_id, cert)
    → tunnel::open_vnc_stream
```

### 8.3 手机连接（直连超时 → Relay）

```
P2pClient::connect (DirectThenRelay)
  → discovery.lookup → Direct(addr)
  → connect_to_peer 超时 15s
  → relay-request(device_id)
  → 收到 { relay_url, session_id }
  → connect_via_relay(relay_url, session_id, Mobile)
  → tunnel::open_vnc_stream（经 relay 转发）
```

### 8.4 PC 收到 connect_relay

```
CloudBridge 收到 ConnectRelay { relay_url, session_id }
  → P2pClient::connect_via_relay(relay_url, session_id, Pc)
  → 连接 relay，发送 RegisterPc
  → spawn run_tunnel_server(conn, vmcontrol_base_url)
```

---

## 九、文档索引

| 文档 | 内容 |
|------|------|
| `DESIGN-novaic-quic-service.md` | STUN + Relay 服务设计 |
| `DESIGN-novaic-quic-service-IMPLEMENTATION.md` | novaic-quic-service 按模块实施计划 |
| `P2P_REFACTOR_PROPOSAL_A.md` | p2p 模块化详细设计（方案 A） |
| `DESIGN-P2P-REGISTRATION-DISCOVERY.md` | 注册与发现 trait 设计 |
| `P2P_REFACTOR_SUMMARY_ABC.md` | 方案 A/B/C 对比与推荐 |
