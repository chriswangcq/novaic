# P2P 架构与入口概览 — 第一轮调研（浅层）

## 1. P2P 相关代码所在目录

| 目录 | 说明 |
|------|------|
| `novaic-app/src-tauri/p2p/` | **P2P 核心 crate**：Rust 库，供 novaic-app 桌面/移动端共用 |
| `novaic-gateway/gateway/api/p2p.py` | **Gateway P2P API**：heartbeat、locate、relay-request 等 REST 接口 |
| `novaic-quic-service/` | **Relay + STUN 服务**：独立 Rust 进程，提供 QUIC 中继与 STUN 外网地址 |

---

## 2. P2P 核心模块清单

### 2.1 novaic-app/src-tauri/p2p/

| 模块 | 文件 | 职责 |
|------|------|------|
| **client** | `client.rs` | P2P 客户端统一入口：`connect()`（relay）、`connect_direct()`（本地直连） |
| **server** | `server.rs` | P2P 服务端：STUN → QUIC bind → heartbeat → accept loop |
| **hole_punch** | `hole_punch.rs` | QUIC UDP 打洞：`listen_for_peer`（PC 侧）、`connect_to_peer`（直连） |
| **relay** | `relay.rs` | Relay 连接：`connect_via_relay`、`connect_via_relay_only`（打洞已移除，远端仅 relay） |
| **rendezvous** | `rendezvous.rs` | STUN 外网地址、Gateway heartbeat 注册、locate 查询 |
| **tunnel** | `tunnel.rs` | QUIC 流多路复用：`run_tunnel_server`、`open_vnc_stream`、`open_scrcpy_stream` |
| **vnc_endpoint** | `vnc_endpoint.rs` | VNC 端点统一：`ensure_vnc_endpoint`（maindesk/subuser）、`shutdown_proxy_for_vm` |
| **config** | `config.rs` | `P2pServerConfig`、`P2pClientConfig`、`resolve_p2p_port` |
| **crypto** | `crypto.rs` | TLS 证书生成、cert pinning |
| **device_id** | `device_id.rs` | Ed25519 设备身份 |
| **local_discovery** | `local_discovery.rs` | LAN mDNS 广播与发现 |
| **discovery** | `discovery.rs` | `GatewayDiscovery`、`MdnsDiscovery`、`CompositeDiscovery` |
| **registry** | `registry.rs` | `GatewayRegistry`、`MdnsRegistry`、`CompositeRegistry` |
| **types** | `types.rs` | `EndpointInfo`、`LocalVmControlInfo`、`ServerDescriptor` |

### 2.2 novaic-quic-service/

| 模块 | 文件 | 职责 |
|------|------|------|
| **relay** | `relay.rs` | QUIC Relay 服务端：配对 PC 与手机连接 |
| **stun** | `stun.rs` | STUN 服务器（RFC 5389） |
| **protocol** | `protocol.rs` | Relay 协议定义 |
| **auth** | `auth.rs` | Relay 鉴权 |
| **config** | `config.rs` | 配置 |

### 2.3 novaic-gateway/

| 模块 | 文件 | 职责 |
|------|------|------|
| **P2P API** | `gateway/api/p2p.py` | `/api/p2p/heartbeat`、`/api/p2p/locate/{device_id}`、`/api/p2p/relay-request`、`/api/p2p/validate-device` |

---

## 3. P2P 入口调用点

### 3.1 setup.rs（应用启动）

```
setup_shared()
  ├── p2p::GatewayDiscovery::new(gw_url, cloud_token)
  ├── p2p::P2pClientConfig { discovery, .. }
  ├── p2p::P2pClient::new(p2p_config)
  └── VncProxyServer::new(gw_url, cloud_token, p2p_client)
```

- **位置**：`novaic-app/src-tauri/src/setup.rs` 第 66–80 行
- **作用**：创建 `P2pClient`、`VncProxyServer`，注入到 Tauri 状态

### 3.2 vnc_proxy.rs（VNC/Scrcpy 连接）

| 场景 | 调用链 |
|------|--------|
| **本地**（device_id == 本机） | `connect_direct(127.0.0.1, device_id, cert_der)` → `hole_punch::connect_to_peer` → `tunnel::open_vnc_stream` / `open_scrcpy_stream` |
| **远端**（device_id != 本机） | `p2p_client.connect(gateway_url, token, device_id)` → `relay::connect_via_relay_only` → `tunnel::open_vnc_stream` / `open_scrcpy_stream` |

- **路由**：`/vnc/:device_id/:agent_id`、`/scrcpy/:device_id/:device_serial`
- **位置**：`novaic-app/src-tauri/src/vnc_proxy.rs` 第 140–141、316、340、417、442、489 行

### 3.3 vmcontrol/lib.rs（桌面端 P2P 服务端启动）

```
start_embedded_server()
  └── p2p::P2pServer::start(cloud_config, vmcontrol_http_port)
        ├── rendezvous::get_external_addr()     // STUN
        ├── hole_punch::listen_for_peer()       // QUIC bind
        ├── registry.register() / heartbeat     // Gateway 注册
        └── accept loop → tunnel::run_tunnel_server(conn)
```

- **位置**：`novaic-app/src-tauri/vmcontrol/src/lib.rs` 第 231–256 行
- **作用**：桌面端启动 P2P 服务端，写入 `LocalVmControlInfo` 到 `SharedLocalVmControl`

### 3.4 vmcontrol/cloud_bridge.rs（Relay 入站）

```
IncomingMessage::ConnectRelay { relay_url, session_id }
  └── p2p::relay::connect_via_relay(relay_url, jwt, session_id, RelayRole::Pc { device_id })
        └── p2p::tunnel::run_tunnel_server(conn, vmcontrol_base_url)
```

- **位置**：`novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` 第 279–300 行
- **作用**：PC 收到 Gateway 推送的 `connect_relay` 后，连接 Relay 并启动 tunnel server

### 3.5 vmcontrol/api/routes/vnc.rs

```
ensure_vnc_endpoint(resource_id)  // p2p::vnc_endpoint
```

- **位置**：`novaic-app/src-tauri/vmcontrol/src/api/routes/vnc.rs` 第 25 行

### 3.6 vmcontrol/api/routes/vm.rs

```
p2p::vnc_endpoint::shutdown_proxy_for_vm(&id)  // VM 删除时关闭 subuser 代理
```

- **位置**：`novaic-app/src-tauri/vmcontrol/src/api/routes/vm.rs` 第 813 行

### 3.7 commands（前端调用）

| 命令 | 文件 | 说明 |
|------|------|------|
| `get_vnc_proxy_url` | `commands/vnc_urls.rs` | 获取 VNC WebSocket URL，依赖 `local_vmcontrol` / my-devices |
| `get_scrcpy_proxy_url` | `commands/vnc_urls.rs` | 同上，Scrcpy |
| `vnc_bridge` | `commands/vnc_bridge.rs` | VNC bridge 逻辑，解析 `pc_client_id` |

---

## 4. P2P 架构简图（文字描述）

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            NovAIC P2P 架构（当前状态）                             │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────┐                    ┌──────────────────┐
  │   手机 App        │                    │   桌面 App        │
  │   (Tauri Mobile)  │                    │   (Tauri Desktop) │
  └────────┬─────────┘                    └────────┬──────────┘
           │                                       │
           │  VncProxy 请求                         │  VmControl 内嵌
           │  ws://127.0.0.1:port/vnc/...          │
           ▼                                       ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                         novaic-app (Tauri)                                   │
  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────────┐  │
  │  │  setup.rs   │───▶│ P2pClient   │◀───│ vnc_proxy.rs                     │  │
  │  │             │    │ (relay only)│    │ - 本地: connect_direct(127.0.0.1)│  │
  │  └─────────────┘    └──────┬──────┘    │ - 远端: connect(relay)           │  │
  │                           │           └─────────────────────────────────┘  │
  │                           │                          │                     │
  │                           │                          │ tunnel::open_*_stream│
  │                           │                          ▼                     │
  │  ┌──────────────────────────────────────────────────────────────────────┐ │
  │  │  p2p crate                                                            │ │
  │  │  client → relay / hole_punch → tunnel                                 │ │
  │  └──────────────────────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────────────────────┘
           │                                       │
           │  relay::connect_via_relay_only         │  P2pServer::start
           │  (Gateway locate → relay URL)          │  hole_punch::listen + heartbeat
           ▼                                       ▼
  ┌──────────────────┐                    ┌──────────────────┐
  │ novaic-quic-service│                    │ novaic-gateway   │
  │ - Relay 服务       │◀──────────────────▶│ - /api/p2p/*     │
  │ - STUN 服务       │   heartbeat/locate  │   heartbeat      │
  │                   │   relay-request     │   locate         │
  └──────────────────┘                    │   relay-request  │
           ▲                               └──────────────────┘
           │
           │  PC 收到 connect_relay 推送
           │  cloud_bridge → relay::connect_via_relay → run_tunnel_server
           │
  ┌────────┴─────────┐
  │  VmControl        │
  │  (CloudBridge)    │
  └──────────────────┘

连接路径：
  - 本地：VncProxy → connect_direct(127.0.0.1) → hole_punch::connect_to_peer → tunnel
  - 远端：VncProxy → P2pClient::connect → relay::connect_via_relay_only → tunnel
  - PC 入站：Gateway 推送 connect_relay → CloudBridge → relay::connect_via_relay → run_tunnel_server
```

---

## 5. 关键文件清单

### 5.1 P2P 核心（novaic-app/src-tauri/p2p/）

| 文件 | 行数（约） | 说明 |
|------|------------|------|
| `src/lib.rs` | ~40 | 模块导出、pub use |
| `src/client.rs` | ~62 | P2pClient |
| `src/server.rs` | ~270 | P2pServer |
| `src/hole_punch.rs` | ~154 | QUIC 打洞 |
| `src/relay.rs` | ~241 | Relay 连接 |
| `src/rendezvous.rs` | ~423 | STUN、heartbeat、locate |
| `src/tunnel.rs` | ~320 | QUIC 流多路复用 |
| `src/vnc_endpoint.rs` | ~302 | VNC 端点 |
| `src/config.rs` | ~71 | 配置 |

### 5.2 入口与集成

| 文件 | 说明 |
|------|------|
| `novaic-app/src-tauri/src/setup.rs` | P2pClient 创建、VncProxy 注入 |
| `novaic-app/src-tauri/src/vnc_proxy.rs` | VNC/Scrcpy 代理，P2P 连接入口 |
| `novaic-app/src-tauri/vmcontrol/src/lib.rs` | P2pServer 启动 |
| `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | ConnectRelay 处理 |
| `novaic-app/src-tauri/vmcontrol/src/api/routes/vnc.rs` | ensure_vnc_endpoint |
| `novaic-app/src-tauri/vmcontrol/src/api/routes/vm.rs` | shutdown_proxy_for_vm |
| `novaic-app/src-tauri/src/commands/vnc_urls.rs` | get_vnc_proxy_url、get_scrcpy_proxy_url |
| `novaic-app/src-tauri/src/commands/vnc_bridge.rs` | vnc_bridge 命令 |

### 5.3 服务端

| 文件 | 说明 |
|------|------|
| `novaic-gateway/gateway/api/p2p.py` | P2P REST API |
| `novaic-quic-service/src/relay.rs` | Relay 服务 |
| `novaic-quic-service/src/stun.rs` | STUN 服务 |

---

## 6. 依赖关系（Cargo.toml）

- **novaic-app** 依赖 `p2p = { path = "p2p" }`（桌面与移动端均启用）
- **vmcontrol** 依赖 `p2p = { path = "../p2p" }`（仅桌面端）

---

*调研完成时间：2025-03-12*
