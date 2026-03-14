# 方案 C：P2P Orchestrator 重构提案

> 目标：统一 CloudBridge、VncProxy、VmControl 的 P2P/Relay 编排，解耦平台逻辑，为 `connect_relay` 提供清晰集成点。

---

## 一、现状分析

### 1.1 当前架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  lib.rs (Desktop)                                                            │
│  ┌──────────────┐    cloud_config     ┌──────────────────┐                  │
│  │ VmControl    │ ─────────────────► │ CloudBridge      │ (WebSocket→Gateway)│
│  │ Embedded     │                     │ - proxy_request   │                  │
│  │ - HTTP API   │                     │ - vm_status      │                  │
│  │ - P2P Server │                     │ - connect_relay? │ (未来)            │
│  │ - Rendezvous │                     └──────────────────┘                  │
│  └──────┬───────┘                                                           │
│         │ LocalVmControlInfo (device_id, cert_der)                          │
│         ▼                                                                    │
│  ┌──────────────────┐                                                        │
│  │ VncProxyServer   │  setup_shared() 创建                                    │
│  │ - local_conn     │  (GatewayUrl, CloudToken)                              │
│  │ - remote_conns   │                                                        │
│  │ - punch_and_connect / get_or_create_local_conn                            │
│  └──────────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  lib.rs (Mobile)                                                             │
│  - 无 VmControl                                                              │
│  - setup_shared() → VncProxyServer（仅 remote 路径）                          │
│  - local_vmcontrol = None → 所有请求走 serve_remote_*                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 问题归纳

| 问题 | 描述 |
|------|------|
| **逻辑分散** | `connect_relay` 需在 CloudBridge 处理，但建立的 Connection 要供 VncProxy/run_tunnel_server 使用，当前无共享入口 |
| **平台耦合** | Desktop 的 `local_vmcontrol`、`get_or_create_local_conn` 与 Mobile 的纯 remote 逻辑混在 vnc_proxy 内，通过 `local_vmcontrol.read().await` 判断 |
| **配置分散** | Gateway URL、CloudToken 在 setup 注入；relay_url 未注入；未来 relay 需从 Gateway 或环境变量获取 |
| **依赖链长** | CloudBridge → VmControl；VncProxy → p2p::hole_punch；二者无统一协调层 |

---

## 二、方案 C：P2P Orchestrator 设计

### 2.1 核心概念

引入 **P2P Orchestrator**（或 `ConnectionManager`）作为统一编排层：

- **职责**：统一管理 P2P 连接生命周期（直连打洞、Relay 兜底）、连接获取与分发
- **平台抽象**：通过 trait / enum 区分 Desktop 与 Mobile 的「连接来源」能力
- **依赖注入**：Gateway URL、Token、Relay URL 均可注入

### 2.2 模块边界

```
                    ┌─────────────────────────────────────────────────────┐
                    │         P2P Orchestrator (ConnectionManager)          │
                    │  - 统一连接获取：get_connection(device_id) → Connection │
                    │  - 统一 Relay 处理：on_connect_relay(relay_url, session_id) │
                    │  - 平台能力：PlatformCapability (Desktop / Mobile)     │
                    └─────────────────────────────────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│  VncProxy              │  │  CloudBridge           │  │  VmControl (P2P Server)│
│  - 仅负责 WS↔QUIC 桥接 │  │  - 仅负责 WS 消息     │  │  - 仅负责 accept 循环  │
│  - 调用 Orchestrator   │  │  - connect_relay 转发 │  │  - 调用 Orchestrator   │
│    get_connection()    │  │    给 Orchestrator     │  │    注册 PunchListener  │
└───────────────────────┘  └───────────────────────┘  └───────────────────────┘
```

### 2.3 平台 trait 设计

```rust
// p2p_orchestrator/src/platform.rs

/// 平台能力：决定「本地连接」是否存在，以及连接获取策略
pub enum PlatformKind {
    /// 桌面：有 VmControl，支持 local + remote
    Desktop {
        local_device_id: String,
        local_cert_der: Vec<u8>,
        vmcontrol_base_url: String,
    },
    /// 移动：无 VmControl，仅 remote
    Mobile,
}

/// 连接获取策略（由平台决定）
pub trait ConnectionStrategy: Send + Sync {
    /// 是否为本地设备
    fn is_local(&self, device_id: &str) -> bool;

    /// 获取本地连接（仅 Desktop 有效）
    fn get_local_connection(&self) -> Option<Connection>;

    /// 获取远端连接：punch_or_relay(gateway_url, token, device_id, relay_url?)
    async fn get_remote_connection(
        &self,
        device_id: &str,
        gateway_url: &str,
        token: &str,
        relay_url: Option<&str>,
    ) -> anyhow::Result<Connection>;
}
```

**Desktop 实现**：`is_local` 比较 device_id；`get_local_connection` 走 loopback QUIC；`get_remote_connection` 走 punch_or_relay。

**Mobile 实现**：`is_local` 恒为 false；`get_local_connection` 恒为 None；`get_remote_connection` 走 punch_or_relay。

### 2.4 P2P Orchestrator 接口

```rust
// p2p_orchestrator/src/lib.rs

pub struct P2POrchestratorConfig {
    pub gateway_url: Arc<Mutex<String>>,
    pub cloud_token: Arc<RwLock<String>>,
    pub relay_url: Option<Arc<Mutex<String>>>,  // 可注入，或从 Gateway 获取
    pub platform: PlatformKind,
}

pub struct P2POrchestrator {
    config: P2POrchestratorConfig,
    local_conn: Arc<Mutex<Option<Connection>>>,
    remote_conns: Arc<Mutex<HashMap<String, Connection>>>,
    /// PC 端：connect_relay 建立的入站 relay 连接，spawn run_tunnel_server 后由 Orchestrator 持有
    relay_inbound_conns: Arc<Mutex<HashMap<String, Connection>>>,  // session_id -> Connection
}

impl P2POrchestrator {
    /// 统一入口：获取到 device_id 的 QUIC 连接
    pub async fn get_connection(&self, device_id: &str) -> anyhow::Result<Connection> {
        match &self.config.platform {
            PlatformKind::Desktop { local_device_id, .. } if local_device_id == device_id => {
                self.get_or_create_local_conn().await
            }
            _ => self.get_or_create_remote_conn(device_id).await,
        }
    }

    /// connect_relay 专用：PC 端收到 Gateway 推送后调用
    pub async fn on_connect_relay(
        &self,
        relay_url: &str,
        session_id: &str,
        vmcontrol_base_url: &str,
    ) -> anyhow::Result<()> {
        let conn = p2p::hole_punch::connect_via_relay(
            relay_url,
            &self.config.cloud_token.read().await,
            session_id,
            RelayRole::Pc { device_id: self.device_id() },
        ).await?;
        self.relay_inbound_conns.lock().await.insert(session_id.to_string(), conn.clone());
        tokio::spawn(p2p::tunnel::run_tunnel_server(conn, vmcontrol_base_url.to_string()));
        Ok(())
    }

    async fn get_or_create_remote_conn(&self, device_id: &str) -> anyhow::Result<Connection> {
        // 1. 先查 remote_conns 缓存
        // 2. 再查 relay_inbound_conns（PC 端：若手机已 relay-request，可能已有）
        // 3. 否则 punch_or_relay：punch 超时 → relay-request → connect_via_relay
        todo!("punch_or_relay 流程")
    }
}
```

---

## 三、connect_relay 集成方案

### 3.1 流程梳理

```
手机端（Mobile）                           PC 端（Desktop）
─────────────────────────────────────────────────────────────────────────────
get_or_create_remote_conn(device_id)
  │
  ├─ punch_and_connect(15s) 超时
  │
  ├─ POST /api/p2p/relay-request { target_device_id }
  │     ───────────────────────────────────────────────► Gateway
  │                                                           │
  │                                                           │ connect_relay (WS push)
  │                                                           ▼
  │                                                    CloudBridge 收到
  │                                                           │
  │                                                           ▼
  │                                                    Orchestrator.on_connect_relay()
  │                                                           │
  │                                                           │ connect_via_relay(Pc)
  │                                                           │ run_tunnel_server(conn)
  │
  ├─ 收到 { relay_url, session_id }
  │
  └─ connect_via_relay(Mobile)
       → 缓存到 remote_conns[device_id]
```

### 3.2 关键点：避免逻辑分散

| 组件 | 职责 | 不负责 |
|------|------|--------|
| **CloudBridge** | 解析 `ConnectRelay` 消息，调用 `Orchestrator.on_connect_relay()` | 不直接调用 `connect_via_relay`，不持有 Connection |
| **P2P Orchestrator** | 持有 relay 连接、执行 `connect_via_relay`、spawn `run_tunnel_server` | 不解析 WebSocket 消息 |
| **VncProxy** | 调用 `Orchestrator.get_connection(device_id)` | 不关心 punch vs relay，不持有 relay 状态 |

### 3.3 代码级修改建议

**cloud_bridge.rs**：

```rust
// 新增 IncomingMessage 变体
#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum IncomingMessage {
    // ... 现有 ...
    ConnectRelay { relay_url: String, session_id: String },
}

// connect_and_run 内，收到 ConnectRelay 时：
IncomingMessage::ConnectRelay { relay_url, session_id } => {
    if let Some(orch) = orchestrator_handle.as_ref() {
        let vmcontrol_url = vmcontrol_base_url.to_string();
        let orch = orch.clone();
        tokio::spawn(async move {
            if let Err(e) = orch.on_connect_relay(&relay_url, &session_id, &vmcontrol_url).await {
                tracing::warn!("[CloudBridge] connect_relay failed: {}", e);
            }
        });
    }
    continue;
}
```

**vnc_proxy.rs**：

```rust
// HandlerState 新增 orchestrator
struct HandlerState {
    orchestrator: Arc<P2POrchestrator>,
    // ...
}

// 取代 get_or_create_local_conn / get_or_create_remote_conn
async fn get_connection(device_id: &str, state: &HandlerState) -> anyhow::Result<Connection> {
    state.orchestrator.get_connection(device_id).await
}
```

---

## 四、依赖注入设计

### 4.1 可注入配置

```rust
pub struct P2POrchestratorConfig {
    pub gateway_url: Arc<Mutex<String>>,
    pub cloud_token: Arc<RwLock<String>>,
    pub relay_url: Option<Arc<Mutex<String>>>,   // 可选，默认从 env 或 Gateway 获取
    pub device_id: String,                        // 本机 device_id（Desktop 需）
    pub platform: PlatformKind,
}
```

### 4.2 注入时机

| 配置项 | 注入时机 | 来源 |
|--------|----------|------|
| gateway_url | setup_shared() | load_gateway_url(data_dir) |
| cloud_token | setup_shared() | RwLock::new(String::new())，update_cloud_token 更新 |
| relay_url | setup_shared() 或首次 relay-request | 环境变量 `RELAY_URL` 或 Gateway 返回 |
| device_id | PlatformKind::Desktop 构造时 | load_or_generate_device_id |

### 4.3 setup 修改

```rust
// setup.rs
pub fn setup_shared(...) -> Result<(), ...> {
    // ... 现有 ...
    let relay_url = Arc::new(Mutex::new(
        std::env::var("NOVAIC_RELAY_URL").unwrap_or_default()
    ));
    app.manage(relay_url);

    let orchestrator = P2POrchestrator::new(P2POrchestratorConfig {
        gateway_url: gw_url.clone(),
        cloud_token: cloud_token.clone(),
        relay_url: Some(relay_url),
        device_id: String::new(),  // Desktop 时由 lib.rs 设置
        platform: PlatformKind::Mobile,  // 或 #[cfg] 区分
    });
    app.manage(orchestrator);
}
```

---

## 五、目录与模块建议

```
novaic-app/src-tauri/
├── src/
│   ├── lib.rs
│   ├── setup.rs
│   ├── vnc_proxy.rs          # 改为依赖 P2POrchestrator
│   └── p2p_orchestrator/     # 新建
│       ├── mod.rs
│       ├── platform.rs       # PlatformKind, ConnectionStrategy
│       ├── orchestrator.rs   # P2POrchestrator
│       └── config.rs         # P2POrchestratorConfig
├── vmcontrol/
│   └── src/
│       ├── cloud_bridge.rs   # 接收 Orchestrator 句柄，转发 connect_relay
│       └── lib.rs
└── p2p/
    └── src/
        ├── hole_punch.rs     # 新增 connect_via_relay, punch_or_relay
        └── ...
```

---

## 六、实施顺序建议

| 阶段 | 内容 | 依赖 |
|------|------|------|
| 1 | 新建 `p2p_orchestrator` 模块，定义 `PlatformKind`、`P2POrchestratorConfig` | - |
| 2 | 实现 `P2POrchestrator::get_connection`，内部复用现有 `get_or_create_local_conn` / `get_or_create_remote_conn` 逻辑 | p2p |
| 3 | VncProxy 改为调用 Orchestrator，移除 `HandlerState` 内 `local_conn`、`remote_conns` | 1, 2 |
| 4 | p2p 新增 `connect_via_relay`、`punch_or_relay` | Gateway relay-request |
| 5 | CloudBridge 新增 `ConnectRelay` 消息，调用 `Orchestrator.on_connect_relay` | 1, 4 |
| 6 | setup 注入 relay_url、Orchestrator | 1 |

---

## 七、方案 C 对比小结

| 维度 | 方案 C 特点 |
|------|-------------|
| **统一入口** | P2POrchestrator 统一管理 local/remote/relay 连接获取 |
| **平台解耦** | PlatformKind trait 区分 Desktop/Mobile，VncProxy 无平台分支 |
| **connect_relay** | CloudBridge 仅转发，Orchestrator 执行建连 + run_tunnel_server |
| **依赖注入** | gateway_url、cloud_token、relay_url 均可注入 |
| **迁移成本** | 中等：需新建模块、重构 vnc_proxy、cloud_bridge 接入 |

---

## 八、附录：Mobile 与 Desktop 路径对比

| 路径 | Desktop | Mobile |
|------|---------|--------|
| local_vmcontrol | Some(LocalVmControlInfo) | None |
| route_vnc(device_id) | device_id == local → serve_local | 恒走 serve_remote |
| get_or_create_local_conn | 有 | 不调用 |
| get_or_create_remote_conn | 有（连其他 PC） | 有（连本机 PC） |
| CloudBridge | 有 | 无 |
| connect_relay | 有（PC 端） | 无 |

方案 C 通过 `PlatformKind::Desktop` / `PlatformKind::Mobile` 将上述差异内聚到 Orchestrator，上层 VncProxy 统一调用 `get_connection(device_id)`。
