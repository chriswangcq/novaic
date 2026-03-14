# 方案 B：VncProxy 与 P2P 连接生命周期模块化重构

> **范围**：vnc_proxy.rs、连接缓存、local_vmcontrol → get_or_create_local_conn 与 remote → get_or_create_remote_conn 流程。

---

## 一、现状分析

### 1.1 当前结构

```
VncProxyServer
├── HandlerState
│   ├── local_vmcontrol: SharedLocalVmControl   # lib.rs 在 VmControl 启动时写入
│   ├── gateway_url, cloud_token, vmcontrol_url
│   ├── local_conn: Mutex<Option<Connection>>   # 桌面：本机 loopback 复用
│   └── remote_conns: Mutex<HashMap<device_id, Connection>>  # 远端设备复用
```

### 1.2 连接获取流程

| 路径 | 条件 | 调用链 | 依赖 |
|------|------|--------|------|
| **本地** | `device_id == local_vmcontrol.device_id` | `get_or_create_local_conn` → `p2p::hole_punch::connect_to_peer(127.0.0.1:19998, ...)` → `tunnel::open_vnc_stream` | 硬编码 `LOCAL_P2P_PORT=19998` |
| **远端** | `device_id != local` | `get_or_create_remote_conn` → `p2p::hole_punch::punch_and_connect(gateway_url, token, device_id, 0)` → `tunnel::open_vnc_stream` | 直接依赖 `p2p::hole_punch` |

### 1.3 问题点

1. **VncProxy 与 hole_punch 强耦合**：Vnc_proxy 直接调用 `p2p::hole_punch::connect_to_peer` 和 `punch_and_connect`，无法插入 relay 等 fallback。
2. **端口重复定义**：`vmcontrol::P2P_PORT=19998` 与 `vnc_proxy::LOCAL_P2P_PORT=19998` 两处硬编码。
3. **连接获取与缓存逻辑混在 HandlerState**：get_or_create_* 既负责「解析策略」又负责「缓存」。
4. **relay 无法接入**：`punch_and_connect` 超时直接失败，无 relay 兜底路径。

---

## 二、方案 B 设计目标

1. **抽取连接获取**：独立 `ConnectionResolver` 或 `P2pConnectionPool`，负责「按 device_id 获取 Connection」。
2. **解耦 VncProxy 与 hole_punch**：VncProxy 只依赖 `ConnectionResolver` trait，不直接调用 `p2p::hole_punch`。
3. **relay fallback 可插**：通过 `punch_or_relay` 策略，在 punch 超时后自动走 relay。
4. **桌面 vs 移动端**：`local_conn` 仅在桌面（有 local_vmcontrol）存在；`remote_conns` 在移动端为主；两者由同一 resolver 统一入口。

---

## 三、核心组件设计

### 3.1 ConnectionResolver trait（抽象连接获取）

```rust
// novaic-app/src-tauri/src/vnc_proxy/connection_resolver.rs（新建）

use quinn::Connection;
use std::sync::Arc;

/// 连接解析策略：按 device_id 获取 QUIC Connection，支持 punch / relay 等实现。
#[async_trait::async_trait]
pub trait ConnectionResolver: Send + Sync {
    /// 获取到指定 device_id 的 QUIC 连接。
    /// - 本地：device_id 为本机时，走 loopback 127.0.0.1:port
    /// - 远端：device_id 为远端时，走 punch 或 punch_or_relay
    async fn resolve(&self, device_id: &str) -> anyhow::Result<Connection>;
}
```

### 3.2 P2pConnectionPool（连接池 + 缓存）

```rust
// novaic-app/src-tauri/src/vnc_proxy/connection_pool.rs（新建）

use quinn::Connection;
use std::collections::HashMap;
use tokio::sync::Mutex;

/// 连接池：缓存本地 + 远端 QUIC 连接，按 device_id 去重。
#[derive(Clone)]
pub struct P2pConnectionPool {
    /// 本地连接缓存（仅桌面有值；移动端无 local_vmcontrol 时此分支永不触发）
    local_conn: Arc<Mutex<Option<Connection>>>,
    /// 远端连接缓存：device_id -> Connection
    remote_conns: Arc<Mutex<HashMap<String, Connection>>>,
}

impl P2pConnectionPool {
    pub fn new() -> Self {
        Self {
            local_conn: Arc::new(Mutex::new(None)),
            remote_conns: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// 检查缓存是否有效（未关闭）
    fn is_conn_valid(conn: &Connection) -> bool {
        conn.close_reason().is_none()
    }

    pub async fn get_local(&self) -> Option<Connection> {
        let guard = self.local_conn.lock().await;
        guard.as_ref().filter(|c| Self::is_conn_valid(c)).cloned()
    }

    pub async fn set_local(&self, conn: Connection) {
        let mut guard = self.local_conn.lock().await;
        *guard = Some(conn);
    }

    pub async fn get_remote(&self, device_id: &str) -> Option<Connection> {
        let guard = self.remote_conns.lock().await;
        guard.get(device_id).filter(|c| Self::is_conn_valid(c)).cloned()
    }

    pub async fn set_remote(&self, device_id: &str, conn: Connection) {
        let mut guard = self.remote_conns.lock().await;
        guard.insert(device_id.to_string(), conn);
    }

    pub async fn remove_remote(&self, device_id: &str) {
        let mut guard = self.remote_conns.lock().await;
        guard.remove(device_id);
    }

    pub async fn invalidate_local(&self) {
        let mut guard = self.local_conn.lock().await;
        *guard = None;
    }
}
```

### 3.3 DefaultConnectionResolver（实现 ConnectionResolver）

```rust
// novaic-app/src-tauri/src/vnc_proxy/default_resolver.rs（新建）

use quinn::Connection;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::RwLock;

/// 默认 resolver：本地 loopback + 远端 punch_or_relay。
pub struct DefaultConnectionResolver {
    pool: P2pConnectionPool,
    local_info: Arc<RwLock<Option<LocalVmControlInfo>>>,
    gateway_url: SharedGatewayUrl,
    cloud_token: SharedCloudToken,
    local_p2p_port: u16,
    /// 是否启用 relay fallback（punch 超时后走 relay）
    relay_fallback: bool,
}

impl DefaultConnectionResolver {
    pub fn new(
        local_info: SharedLocalVmControl,
        gateway_url: SharedGatewayUrl,
        cloud_token: SharedCloudToken,
        local_p2p_port: u16,
        relay_fallback: bool,
    ) -> Self {
        Self {
            pool: P2pConnectionPool::new(),
            local_info,
            gateway_url,
            cloud_token,
            local_p2p_port,
            relay_fallback,
        }
    }

    pub fn pool(&self) -> &P2pConnectionPool {
        &self.pool
    }
}

#[async_trait::async_trait]
impl ConnectionResolver for DefaultConnectionResolver {
    async fn resolve(&self, device_id: &str) -> anyhow::Result<Connection> {
        let local_id = self.local_info.read().await
            .as_ref()
            .map(|i| i.device_id.clone());

        if local_id.as_deref() == Some(device_id) {
            self.resolve_local(&local_id.unwrap()).await
        } else {
            self.resolve_remote(device_id).await
        }
    }
}

impl DefaultConnectionResolver {
    async fn resolve_local(&self, device_id: &str) -> anyhow::Result<Connection> {
        if let Some(conn) = self.pool.get_local().await {
            return Ok(conn);
        }

        let info = self.local_info.read().await.clone()
            .ok_or_else(|| anyhow::anyhow!("VmControl P2P not ready yet"))?;

        let addr: SocketAddr = format!("127.0.0.1:{}", self.local_p2p_port).parse()?;

        // 通过 trait 或抽象层调用，而非直接 p2p::hole_punch
        let conn = self.connect_local(&addr, &info.device_id, &info.cert_der).await?;

        self.pool.set_local(conn.clone()).await;
        Ok(conn)
    }

    async fn resolve_remote(&self, device_id: &str) -> anyhow::Result<Connection> {
        if let Some(conn) = self.pool.get_remote(device_id).await {
            return Ok(conn);
        }

        let gateway_url = self.gateway_url.lock().unwrap_or_else(|e| e.into_inner()).clone();
        let token = self.cloud_token.read().await.clone();

        if gateway_url.is_empty() {
            anyhow::bail!("Gateway URL not configured");
        }
        if token.is_empty() {
            anyhow::bail!("Not logged in — JWT token missing");
        }

        let conn = if self.relay_fallback {
            // punch_or_relay：先 punch，超时后 relay
            p2p::connection::punch_or_relay(&gateway_url, &token, device_id).await?
        } else {
            p2p::connection::punch_and_connect(&gateway_url, &token, device_id).await?
        };

        self.pool.set_remote(device_id, conn.clone()).await;
        Ok(conn)
    }

    async fn connect_local(
        &self,
        addr: &SocketAddr,
        device_id: &str,
        cert_der: &[u8],
    ) -> anyhow::Result<Connection> {
        p2p::connection::connect_to_peer(*addr, device_id, cert_der).await
    }
}
```

---

## 四、p2p 解耦与 punch_or_relay 接入

### 4.1 新增 p2p::connection 模块（统一入口）

```rust
// novaic-app/src-tauri/p2p/src/connection.rs（新建）

//! 连接获取统一入口：对外暴露 connect_to_peer、punch_and_connect、punch_or_relay。
//! 内部转发到 hole_punch，relay 逻辑在 punch_or_relay 中实现。

pub use crate::hole_punch::{connect_to_peer, punch_and_connect};

/// punch 超时后走 relay 的 fallback。
pub async fn punch_or_relay(
    gateway_url: &str,
    jwt: &str,
    target_device_id: &str,
) -> anyhow::Result<quinn::Connection> {
    // 1. 先 punch_and_connect（15s 超时）
    match crate::hole_punch::punch_and_connect(gateway_url, jwt, target_device_id, 0).await {
        Ok(conn) => return Ok(conn),
        Err(e) => {
            tracing::warn!("[P2P] Punch failed: {}, falling back to relay", e);
        }
    }

    // 2. relay-request 获取 relay_url + session_id
    let (relay_url, session_id) = crate::relay_client::request_relay(gateway_url, jwt, target_device_id).await?;

    // 3. connect_via_relay
    crate::hole_punch::connect_via_relay(&relay_url, jwt, &session_id, RelayRole::Mobile { target_device_id: target_device_id.to_string() }).await
}
```

### 4.2 VncProxy 与 hole_punch 解耦

**重构前**：vnc_proxy 直接 `use p2p::hole_punch`。

**重构后**：vnc_proxy 只依赖 `ConnectionResolver` 和 `p2p::connection`（后者由 resolver 内部使用）。

```rust
// vnc_proxy.rs 重构后

async fn get_or_create_local_conn(state: &HandlerState) -> anyhow::Result<Connection> {
    state.resolver.resolve_local().await  // 或通过 resolver.resolve(local_device_id)
}

async fn get_or_create_remote_conn(device_id: &str, state: &HandlerState) -> anyhow::Result<Connection> {
    state.resolver.resolve(device_id).await
}
```

---

## 五、桌面 vs 移动端差异化

### 5.1 平台差异

| 平台 | local_vmcontrol | local_conn | remote_conns |
|------|-----------------|------------|--------------|
| **桌面** | 有（VmControl 嵌入式） | 有，用于本机 VNC | 无（桌面端通常不连远端 PC 的 VNC） |
| **移动端** | 无（None） | 永不触发 | 有，用于连远端 PC |

### 5.2 实现建议

1. **ConnectionResolver 统一入口**：`resolve(device_id)` 内部根据 `local_info.as_ref()` 判断：
   - 若 `local_id == device_id` 且 `local_info.is_some()` → 走 `resolve_local`
   - 否则 → 走 `resolve_remote`

2. **移动端**：`local_info` 始终为 `None`，`resolve_local` 分支永远不会执行，`local_conn` 保持空。

3. **条件编译**（可选）：若需进一步精简移动端二进制，可对 `local_conn` 做 `#[cfg(not(any(target_os = "android", target_os = "ios")))]`，但当前逻辑已足够（`local_info` 为 None 时不会走 local 路径）。

### 5.3 代码示意

```rust
// resolve 内部逻辑
async fn resolve(&self, device_id: &str) -> anyhow::Result<Connection> {
    let local_id = self.local_info.read().await.as_ref().map(|i| i.device_id.clone());

    if local_id.as_deref() == Some(device_id) {
        // 桌面：local_info 有值；移动端：此分支永不进入（local_info 为 None）
        self.resolve_local().await
    } else {
        // 远端：桌面/移动端都可能用（移动端为主）
        self.resolve_remote(device_id).await
    }
}
```

---

## 六、端口配置统一

### 6.1 现状

- `vmcontrol::P2P_PORT = 19998`
- `vnc_proxy::LOCAL_P2P_PORT = 19998`

### 6.2 建议

**方案 A**：在 `p2p` crate 中定义统一常量：

```rust
// p2p/src/lib.rs
pub const DEFAULT_P2P_PORT: u16 = 19998;
```

**方案 B**：通过 `ConnectionResolver` 构造注入：

```rust
// setup.rs 或 lib.rs
let local_port = vmcontrol::P2P_PORT;  // 或从 config 读取
let resolver = DefaultConnectionResolver::new(
    local_vmcontrol,
    gateway_url,
    cloud_token,
    local_port,
    relay_fallback: true,
);
```

---

## 七、文件变更清单

| 模块 | 变更 |
|------|------|
| **vnc_proxy** | 拆分为 `vnc_proxy/` 目录，引入 `ConnectionResolver`、`P2pConnectionPool`、`DefaultConnectionResolver` |
| **p2p** | 新增 `connection.rs`，统一 `connect_to_peer`、`punch_and_connect`、`punch_or_relay` 入口 |
| **hole_punch** | 新增 `connect_via_relay`（若尚未实现），保持 `punch_and_connect` 不变 |
| **p2p** | 新增 `relay_client.rs`（`request_relay` 调用 Gateway `POST /api/p2p/relay-request`） |
| **vnc_proxy** | `HandlerState` 持有 `Arc<dyn ConnectionResolver>`，移除对 `p2p::hole_punch` 的直接依赖 |
| **setup.rs** | 构造 `DefaultConnectionResolver` 并注入 VncProxy |
| **lib.rs** | 写入 `SharedLocalVmControl` 逻辑不变；可选注入 `local_p2p_port` |

---

## 八、与 CloudBridge 的 relay 连接共享

根据 `DESIGN-novaic-quic-service-IMPLEMENTATION.md`，PC 端 CloudBridge 收到 `connect_relay` 后会建立 relay 连接。该连接需与 VncProxy 共享。

**建议**：PC 端不执行 `get_or_create_remote_conn`（手机连 PC 时，是手机端的 VncProxy 在连）。PC 端若未来有「被连」场景，需要：

- `SharedRelayConnections: Arc<RwLock<HashMap<session_id, Connection>>>`
- CloudBridge 收到 connect_relay 后建连并写入
- VncProxy 的 resolver 在「被连」场景下先查此共享，再决定是否走 punch

当前方案 B 主要针对**手机端**的 `get_or_create_remote_conn` 解耦与 relay 接入；PC 端 relay 共享可后续单独迭代。

---

## 九、实施顺序建议

1. **Phase 1**：新增 `p2p::connection`（re-export hole_punch），`punch_or_relay` 占位（先 fallback 到 punch 失败）。
2. **Phase 2**：抽取 `P2pConnectionPool`，`ConnectionResolver` trait，`DefaultConnectionResolver`。
3. **Phase 3**：VncProxy 接入 resolver，移除对 hole_punch 的直接调用。
4. **Phase 4**：实现 relay 完整流程（relay-request、connect_via_relay、CloudBridge 共享）。

---

## 十、小结

| 目标 | 方案 |
|------|------|
| 连接获取独立 | `ConnectionResolver` trait + `DefaultConnectionResolver` |
| 解耦 hole_punch | VncProxy 依赖 `p2p::connection`（或 resolver 内部），不直接 `use p2p::hole_punch` |
| relay fallback | `punch_or_relay` 在 `p2p::connection` 中实现，resolver 可配置 `relay_fallback` |
| 桌面 vs 移动 | 统一 `resolve(device_id)`，`local_info` 为 None 时仅走 remote |
