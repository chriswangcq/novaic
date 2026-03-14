# Gateway 与 Tauri 职责边界（Round 2 — 中层）

> 基于 R1 输出，深入分析 Gateway 与 Tauri 职责边界，含数据流边界图。

**输入**：`docs/survey-2026/GATEWAY_API_ROUND1.md`、Gateway 路由、Tauri commands、vmcontrol、vnc_proxy

---

## 一、VNC 路由：Gateway 不参与，Tauri vnc_proxy 全权

### 1.1 结论

| 维度 | 结论 |
|------|------|
| **Gateway 参与** | ❌ 无。Gateway 不提供 VNC WebSocket 代理、不参与 VNC 数据转发 |
| **Tauri 全权** | ✅ vnc_proxy 监听 `127.0.0.1:{动态端口}`，全权处理 VNC/Scrcpy 路由与数据桥接 |

### 1.2 vnc_proxy 职责

| 能力 | 实现位置 | 说明 |
|------|----------|------|
| **WS 入口** | `novaic-app/src-tauri/src/vnc_proxy.rs` | `/vnc/:device_id/:agent_id`、`/scrcpy/:device_id/:device_serial` |
| **本机路由** | `route_vnc` / `route_scrcpy` | `device_id == local_vmcontrol.device_id` → QUIC loopback 127.0.0.1 |
| **远端路由** | `serve_remote_vnc` / `serve_remote_scrcpy` | `get_or_create_remote_conn` → P2pClient.connect（relay） |
| **数据桥接** | `bridge_ws_quic` / `bridge_ws_quic_scrcpy` | WebSocket ↔ QUIC 双向转发 |

### 1.3 数据路径（VNC）

```
前端 noVNC
    → ws://127.0.0.1:{proxy_port}/vnc/{pc_client_id}/{agent_id}
    → vnc_proxy (Tauri)
        ├─ 本机：connect_direct(127.0.0.1) → tunnel::open_vnc_stream → QUIC loopback
        └─ 远端：P2pClient.connect(gateway_url, token, device_id)
                    → relay_request (HTTP) → connect_via_relay (QUIC)
                    → tunnel::open_vnc_stream → bridge_ws_quic
```

- Gateway 仅被 `relay_request` 调用（手机端 P2pClient 内部），**不参与 VNC 数据流**。
- VNC 帧从浏览器 → vnc_proxy WS → QUIC → VmControl tunnel → VNC socket，全程在 Tauri 侧完成。

---

## 二、Relay：Gateway relay-request/validate，Tauri 实际 connect_via_relay

### 2.1 职责划分

| 角色 | 职责 | 实现 |
|------|------|------|
| **Gateway** | relay-request、validate-relay-session、relay-refresh-for-pc | `gateway/api/p2p.py` |
| **Tauri** | 实际建立 QUIC 连接 | `p2p/relay.rs`、`p2p/client.rs`、CloudBridge |

### 2.2 Gateway 侧

| 端点 | 方法 | 职责 |
|------|------|------|
| `POST /api/p2p/relay-request` | 手机调用 | 校验 target_device_id、推 connect_relay 给 PC（via DeviceRegistry）、登记 PendingRelaySession、返回 relay_url + session_id |
| `GET /api/p2p/validate-relay-session` | Relay 服务调用 | 校验 session_id 是否由 relay-request 创建且未过期 |
| `POST /api/p2p/relay-refresh-for-pc` | PC 调用 | PC 重试 connect_via_relay 时 session 过期，续期 session |

### 2.3 Tauri 侧

| 组件 | 职责 |
|------|------|
| **CloudBridge** | 收到 `connect_relay` 后调用 `p2p::relay::connect_via_relay`，建立 QUIC 连接并启动 tunnel server |
| **P2pClient.connect** | 手机端：`relay_request` → `connect_via_relay`（或 `connect_via_relay_only`） |
| **p2p/relay.rs** | `connect_via_relay(relay_url, jwt, session_id, role)` 实际建立到 Relay 的 QUIC 连接 |

### 2.4 流程

```
手机端 VNC 连接远端 PC：
  1. vnc_proxy.get_or_create_remote_conn(device_id)
  2. P2pClient.connect(gateway_url, token, device_id)
  3. rendezvous::relay_request(gateway_url, jwt, device_id)  ← Gateway
  4. Gateway: 校验 → send_push_and_wait_ack(connect_relay) → PC
  5. PC CloudBridge: 收到 connect_relay → connect_via_relay(relay_url, jwt, session_id, RelayRole::Pc)
  6. 手机: connect_via_relay(relay_url, jwt, session_id, RelayRole::Mobile)
  7. Relay 服务: 收到 ConnectRequest → GET validate-relay-session ← Gateway
  8. 两端 QUIC 连接建立，VNC 数据经 relay 转发
```

---

## 三、VM/Device 启动：Gateway 编排转发，VmControl 执行

### 3.1 职责划分

| 角色 | 职责 |
|------|------|
| **Gateway** | REST 编排、鉴权、PC 路由、转发到 CloudBridge |
| **VmControl** | 实际执行 QEMU/Android 启动、停止、状态查询 |

### 3.2 Gateway 编排

| 模块 | 端点 | 转发目标 |
|------|------|----------|
| **vm.py** | `POST /api/vm/start`、`POST /api/vm/stop`、`POST /api/vm/setup` | `get_pc_client_manager(user_id)` → `vm_start` / `vm_shutdown` / `vm_setup` |
| **devices.py** | `POST /api/devices/{id}/start`、`stop`、`setup` | `_get_pc_manager_for_device(device, user_id, pc_client_id)` → `vm_start` / `android_emulator_start` 等 |

### 3.3 调用链

```
前端 devices.start(deviceId, pcClientId?)
    → invoke('gateway_post', { path: '/api/devices/{id}/start', body: {} })
    → Gateway devices.py
        → _get_pc_manager_for_device(device, user_id, pc_client_id)
        → get_pc_client_manager(user_id, pc_client_id)
        → _DeviceManagerAdapter.vm_start(device.id, body)
        → forward_to_device / send_control_to_device
            → DeviceRegistry.get_device(pc_client_id) → device.ws.send_json({ type: "vm_start", ... })
    → CloudBridge (Tauri)
        → IncomingMessage::VmStart
        → forward_to_vmcontrol(client, base_url, "POST", "/api/vms/{vm_id}/start", body)
    → VmControl HTTP (本地)
        → QEMU / Android 实际启动
```

### 3.4 多 PC 路由

- `devices/start` 支持 `pc_client_id` 查询参数，或使用 `device.pc_client_id`。
- `vm/start` 无 `pc_client_id`，取 `get_pc_client_manager(user_id)` 第一个已连接设备。

---

## 四、Cloud Bridge：Gateway 维护 DeviceRegistry，Tauri 维持 WS 连接

### 4.1 职责划分

| 角色 | 职责 |
|------|------|
| **Gateway** | DeviceRegistry、WebSocket 服务端 `/internal/pc/ws`、消息路由 |
| **Tauri** | CloudBridge 客户端、维持 WS 连接、转发到 VmControl |

### 4.2 Gateway 侧

| 组件 | 说明 |
|------|------|
| **DeviceRegistry** | `_devices: Dict[device_id, DeviceState]`，以 device_id 为键管理所有已连接 PC 的 WebSocket |
| **WebSocket 端点** | `@router.websocket("/pc/ws")`，挂载于 `/internal`，完整路径 `/internal/pc/ws` |
| **握手头** | `x-device-id`、`x-user-id`、`x-app-instance-id`、`x-machine-label` |
| **消息类型** | 下发：`proxy_request`、`connect_relay`、`vm_start` 等；接收：`proxy_response`、`connect_relay_ack`、`ping` |

### 4.3 Tauri 侧

| 组件 | 说明 |
|------|------|
| **CloudBridge** | `vmcontrol/src/cloud_bridge.rs`，连接 `{gateway_url}/internal/pc/ws` |
| **重连** | 断线后 5 秒自动重连，每次重连前重新读取 JWT |
| **转发** | 收到 `proxy_request` / `vm_start` 等 → `forward_to_vmcontrol` → 本地 VmControl HTTP |

### 4.4 数据流

```
Tools Server / 前端
    → Gateway HTTP (vm.py / devices.py / p2p.py)
        → get_device_registry().get_device(device_id)
        → device.ws.send_json({ type: "vm_start", ... })
    → CloudBridge WS (Tauri)
        → forward_to_vmcontrol(...)
    → VmControl HTTP (127.0.0.1)
        → QEMU / ADB
```

---

## 五、数据流边界图

### 5.1 请求入口与出口

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              请求入口（Entry Points）                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  前端 (React)                                                                    │
│      invoke('gateway_get/post', { path, body })  ──────────────────────────────►│
│                                                                                  │
│  Tools Server / RO                                                               │
│      HTTP → Gateway /api/*  ───────────────────────────────────────────────────►│
│                                                                                  │
│  Relay 服务                                                                      │
│      GET /api/p2p/validate-relay-session  ─────────────────────────────────────►│
│      GET /api/p2p/validate-device  ─────────────────────────────────────────────►│
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Gateway (REST + WS 服务端)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  REST: /api/agents, /api/devices, /api/vm, /api/p2p, ...                         │
│  Internal: /internal/pc/ws (CloudBridge 连接)                                    │
│                                                                                  │
│  出口：                                                                          │
│    • forward_to_device / send_control_to_device  ──► DeviceRegistry → WS ───────►│
│    • send_push_and_wait_ack(connect_relay)  ──────► DeviceRegistry → WS ───────►│
│    • 直接返回（heartbeat, locate, my-devices, relay-request 等）                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
┌───────────────────────────┐ ┌───────────────────┐ ┌───────────────────────────┐
│  Tauri (gateway_get/post)  │ │  CloudBridge WS   │ │  Tauri vnc_proxy          │
│  代理到 Gateway HTTP       │ │  接收 VM/relay 指令│ │  不经过 Gateway           │
└───────────────────────────┘ └───────────────────┘ └───────────────────────────┘
                    │                   │                   │
                    ▼                   ▼                   ▼
┌───────────────────────────┐ ┌───────────────────┐ ┌───────────────────────────┐
│  Gateway 返回 JSON        │ │  VmControl HTTP   │ │  本机: QUIC loopback       │
│  (agents, devices, p2p…)  │ │  QEMU / ADB       │ │  远端: P2pClient.connect    │
└───────────────────────────┘ └───────────────────┘ └───────────────────────────┘
```

### 5.2 按场景的数据流

| 场景 | 请求入口 | Gateway 参与 | 出口 |
|------|----------|--------------|------|
| **REST API（agents/devices/vm/p2p）** | 前端 gateway_get/post | ✅ 处理并返回 | 直接返回 或 forward_to_device |
| **VM/Device 启动** | 前端 gateway_post | ✅ 编排、转发 | forward_to_device → CloudBridge WS |
| **Relay 会话创建** | 手机 relay_request | ✅ 校验、推 connect_relay | send_push_and_wait_ack → CloudBridge WS |
| **Relay 会话校验** | Relay 服务 | ✅ validate-relay-session | 直接返回 |
| **VNC 连接** | 前端 noVNC → vnc_proxy WS | ❌ 不参与 | vnc_proxy 内部 P2pClient / QUIC loopback |
| **CloudBridge 连接** | Tauri CloudBridge | ✅ 接受 WS、维护 DeviceRegistry | 接收连接、路由消息 |

### 5.3 简化边界图

```
                    ┌─────────────────────────────────────────┐
                    │              Gateway                     │
                    │  • REST API 编排                         │
                    │  • DeviceRegistry (WS 服务端)             │
                    │  • P2P: heartbeat, locate, relay-*      │
                    │  • validate-relay-session (Relay 调用)   │
                    └──────────────┬──────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │ 前端 REST     │      │ CloudBridge  │      │ Relay 服务   │
    │ gateway_*    │      │ WS 客户端    │      │ validate-*   │
    └──────┬───────┘      └──────┬───────┘      └──────────────┘
           │                     │
           ▼                     ▼
    ┌──────────────┐      ┌──────────────┐
    │ Tauri        │      │ VmControl    │
    │ (代理+状态)   │      │ (QEMU/ADB)   │
    └──────┬───────┘      └──────────────┘
           │
           ▼
    ┌──────────────┐
    │ vnc_proxy    │  ← 不经过 Gateway，直接 WS→QUIC
    │ (VNC 全权)   │
    └──────────────┘
```

---

## 六、参考文件

| 文件 | 说明 |
|------|------|
| `novaic-gateway/gateway/api/p2p.py` | relay-request、validate-relay-session、relay-refresh-for-pc |
| `novaic-gateway/gateway/api/internal/pc_client.py` | DeviceRegistry、/internal/pc/ws |
| `novaic-gateway/gateway/api/devices.py` | devices/start、_get_pc_manager_for_device |
| `novaic-gateway/gateway/api/vm.py` | vm/start、get_pc_client_manager |
| `novaic-app/src-tauri/src/vnc_proxy.rs` | VNC 全权路由、本机/远端、WS↔QUIC |
| `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | CloudBridge WS 客户端、connect_relay、forward_to_vmcontrol |
| `novaic-app/src-tauri/p2p/src/relay.rs` | connect_via_relay |
| `novaic-app/src-tauri/p2p/src/client.rs` | P2pClient.connect、connect_via_relay_only |
| `novaic-app/src-tauri/src/commands/gateway.rs` | gateway_get、gateway_post |
