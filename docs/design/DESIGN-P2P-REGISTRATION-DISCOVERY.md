# P2P Server 注册与发现设计

> 组件化、非业务化的注册/发现抽象，支持多后端（Gateway、mDNS、未来 Relay）。

---

## 一、现状

| 能力 | 实现 | 范围 |
|------|------|------|
| **注册** | Gateway heartbeat | 云端，跨网 |
| **注册** | mDNS advertise | 局域网 |
| **发现** | Gateway locate | 按 device_id 查 ext_addr + cert |
| **发现** | mDNS discover | 局域网设备列表 |

问题：注册与发现逻辑分散在 `rendezvous`、`local_discovery`，无统一抽象，难以扩展（如 Relay 注册表）。

---

## 二、核心概念

### 2.1 服务描述（ServerDescriptor）

```rust
/// 可连接 P2P 服务器的描述信息（与具体传输无关）
#[derive(Clone, Debug)]
pub struct ServerDescriptor {
    /// 唯一标识（业务层决定语义，如 device_id）
    pub id: String,
    /// 可连接地址（直连：ip:port；Relay：relay_url + session_id）
    pub endpoint: EndpointInfo,
    /// 连接所需附加数据（如 TLS cert pinning）
    pub metadata: HashMap<String, String>,
}

#[derive(Clone, Debug)]
pub enum EndpointInfo {
    /// 直连：外网 IP:Port（STUN 获取）
    Direct(SocketAddr),
    /// Relay：需通过 relay 服务连接
    Relay { relay_url: String, session_id: String },
}
```

- **id**：业务层语义（NovAIC 用 device_id），组件层不解释
- **endpoint**：纯技术信息，如何建立连接
- **metadata**：可扩展（cert_der_b64、http_port 等）

### 2.2 注册（Registration）

```rust
/// 注册后端：Server 向某处「宣告」自己的存在与可连接信息
#[async_trait]
pub trait Registry: Send + Sync {
    /// 注册/刷新服务信息，返回是否成功
    async fn register(&self, descriptor: &ServerDescriptor) -> anyhow::Result<()>;
    /// 注销（可选，部分后端无显式注销）
    async fn unregister(&self, id: &str) -> anyhow::Result<()>;
}
```

### 2.3 发现（Discovery）

```rust
/// 发现后端：Client 从某处「查询」目标 Server 的可连接信息
#[async_trait]
pub trait Discovery: Send + Sync {
    /// 按 id 查询单个服务
    async fn lookup(&self, id: &str) -> anyhow::Result<Option<ServerDescriptor>>;
}

/// 可选：持续发现（如 mDNS 设备列表）
#[async_trait]
pub trait DiscoveryStream: Send + Sync {
    type Event;
    /// 返回发现事件流（Discovered / Removed）
    fn stream(&self) -> impl Stream<Item = Self::Event>;
}
```

---

## 三、后端实现

### 3.1 GatewayRegistry（云端注册）

```rust
/// 实现 Registry：通过 Gateway heartbeat API
pub struct GatewayRegistry {
    base_url: String,
    auth_token: Arc<RwLock<String>>,
}

impl GatewayRegistry {
    pub fn new(base_url: String, auth_token: Arc<RwLock<String>>) -> Self { ... }
}

#[async_trait]
impl Registry for GatewayRegistry {
    async fn register(&self, d: &ServerDescriptor) -> anyhow::Result<()> {
        let EndpointInfo::Direct(addr) = d.endpoint else {
            anyhow::bail!("Gateway registry only supports Direct endpoint");
        };
        let req = HeartbeatRequest {
            device_id: d.id.clone(),
            ext_addr: addr.to_string(),
            local_port: addr.port(),
            cert_der_b64: d.metadata.get("cert_der_b64").cloned(),
        };
        heartbeat(&self.base_url, &self.auth_token.read().await, &req).await?;
        Ok(())
    }
    async fn unregister(&self, _id: &str) -> anyhow::Result<()> {
        // Gateway 无显式注销，依赖心跳超时
        Ok(())
    }
}
```

### 3.2 GatewayDiscovery（云端发现）

```rust
/// 实现 Discovery：通过 Gateway locate API
pub struct GatewayDiscovery {
    base_url: String,
    auth_token: Arc<RwLock<String>>,
}

#[async_trait]
impl Discovery for GatewayDiscovery {
    async fn lookup(&self, id: &str) -> anyhow::Result<Option<ServerDescriptor>> {
        let resp = locate(&self.base_url, &self.auth_token.read().await, id).await?;
        if !resp.online {
            return Ok(None);
        }
        let addr = resp.ext_addr.parse::<SocketAddr>()?;
        let mut metadata = HashMap::new();
        if let Some(cert) = resp.cert_der {
            metadata.insert("cert_der_b64".to_string(), cert);
        }
        Ok(Some(ServerDescriptor {
            id: id.to_string(),
            endpoint: EndpointInfo::Direct(addr),
            metadata,
        }))
    }
}
```

### 3.3 MdnsRegistry（局域网注册）

```rust
/// 实现 Registry：通过 mDNS 广播
pub struct MdnsRegistry {
    service_type: String,  // 如 "_novaic._tcp.local."
}

#[async_trait]
impl Registry for MdnsRegistry {
    async fn register(&self, d: &ServerDescriptor) -> anyhow::Result<()> {
        let service = descriptor_to_vmcontrol_service(d);
        let shutdown = Arc::new(Notify::new());
        tokio::spawn(advertise(service, shutdown));
        // 需持有 shutdown 以便 unregister 时触发
        // 实际实现中 MdnsRegistry 需持有 JoinHandle 或 shutdown_tx
        Ok(())
    }
    async fn unregister(&self, id: &str) -> anyhow::Result<()> {
        // 触发 shutdown，advertise 循环退出并 unregister
        Ok(())
    }
}
```

### 3.4 MdnsDiscovery（局域网发现）

```rust
/// 实现 DiscoveryStream：mDNS 持续发现
pub struct MdnsDiscovery {
    service_type: String,
}

impl MdnsDiscovery {
    pub fn stream(&self) -> impl Stream<Item = DiscoveryStreamEvent> {
        // 内部调用 local_discovery::discover，将 DiscoveryEvent 映射为 DiscoveryStreamEvent
    }
}

pub enum DiscoveryStreamEvent {
    Discovered(ServerDescriptor),
    Removed(String),
}
```

### 3.5 未来：RelayRegistry / RelayDiscovery

- **RelayRegistry**：PC 连接 relay 时，relay 内部维护 session_id → device_id 映射，可视为「注册」
- **RelayDiscovery**：手机 relay-request 返回 relay_url + session_id，可视为「发现」结果

---

## 四、组合策略（多后端）

### 4.1 注册：多后端并行

```rust
/// 组合多个 Registry，注册时向所有后端发送
pub struct CompositeRegistry {
    backends: Vec<Arc<dyn Registry>>,
}

#[async_trait]
impl Registry for CompositeRegistry {
    async fn register(&self, d: &ServerDescriptor) -> anyhow::Result<()> {
        for backend in &self.backends {
            if let Err(e) = backend.register(d).await {
                tracing::warn!("Registry backend failed: {}", e);
                // 可选：全部失败才返回 Err
            }
        }
        Ok(())
    }
    async fn unregister(&self, id: &str) -> anyhow::Result<()> {
        for backend in &self.backends {
            let _ = backend.unregister(id).await;
        }
        Ok(())
    }
}
```

### 4.2 发现：级联查询

```rust
/// 组合多个 Discovery，按优先级依次 lookup
pub struct CompositeDiscovery {
    backends: Vec<Arc<dyn Discovery>>,
}

#[async_trait]
impl Discovery for CompositeDiscovery {
    async fn lookup(&self, id: &str) -> anyhow::Result<Option<ServerDescriptor>> {
        for backend in &self.backends {
            if let Ok(Some(d)) = backend.lookup(id).await {
                return Ok(Some(d));
            }
        }
        Ok(None)
    }
}
```

**优先级示例**：先 mDNS（同网快），再 Gateway（跨网）。

### 4.3 发现：流式 + 按需

- **流式**：mDNS 持续发现，用于「设备列表」UI
- **按需**：Gateway locate，用于「已知 device_id 时获取连接信息」

两者可并存，由业务层决定何时用哪种。

---

## 五、与 P2pServer / P2pClient 集成

### 5.1 P2pServer 使用 Registry

```rust
// P2pServer::start 内
let descriptor = ServerDescriptor {
    id: device_id.clone(),
    endpoint: EndpointInfo::Direct(ext_addr),
    metadata: {
        let mut m = HashMap::new();
        m.insert("cert_der_b64".to_string(), base64::encode(&cert_der));
        m
    },
};

if let Some(registry) = &config.registry {
    registry.register(&descriptor).await?;
}

// 心跳循环：定期 registry.register(descriptor)
```

### 5.2 P2pClient 使用 Discovery

```rust
// P2pClient::connect 内
let descriptor = config.discovery
    .lookup(target_id)
    .await?
    .ok_or_else(|| anyhow!("Device not found"))?;

match descriptor.endpoint {
    EndpointInfo::Direct(addr) => {
        let cert = descriptor.metadata.get("cert_der_b64")...;
        connect_to_peer(addr, target_id, cert).await
    }
    EndpointInfo::Relay { relay_url, session_id } => {
        connect_via_relay(&relay_url, &session_id, ...).await
    }
}
```

---

## 六、配置注入

```rust
pub struct P2pServerConfig {
    pub port: u16,
    pub registry: Option<Arc<dyn Registry>>,  // None = 不注册
    pub registry_interval_secs: u64,
    // ...
}

pub struct P2pClientConfig {
    pub discovery: Arc<dyn Discovery>,
    pub connect_strategy: ConnectStrategy,
    // ...
}
```

业务层（setup / lib.rs）负责构造具体 Registry / Discovery 实现并注入。

---

## 七、目录结构建议

```
p2p/
├── src/
│   ├── registry/
│   │   ├── mod.rs       # Registry trait, CompositeRegistry
│   │   ├── gateway.rs   # GatewayRegistry
│   │   └── mdns.rs      # MdnsRegistry
│   ├── discovery/
│   │   ├── mod.rs       # Discovery trait, DiscoveryStream, CompositeDiscovery
│   │   ├── gateway.rs   # GatewayDiscovery
│   │   └── mdns.rs      # MdnsDiscovery
│   ├── types.rs         # ServerDescriptor, EndpointInfo
│   └── ...
```

---

## 八、总结

| 概念 | 抽象 | 实现 |
|------|------|------|
| **注册** | `Registry` trait | GatewayRegistry, MdnsRegistry |
| **发现** | `Discovery` trait | GatewayDiscovery, MdnsDiscovery |
| **服务描述** | `ServerDescriptor` | 与传输无关，支持 Direct / Relay |
| **组合** | CompositeRegistry, CompositeDiscovery | 多后端并行/级联 |

- **组件化**：Registry / Discovery 为 trait，可替换、可组合
- **非业务化**：ServerDescriptor 的 id 无业务语义，endpoint 仅描述连接方式
- **可扩展**：新增 Relay 等后端只需实现 trait，无需改调用方
