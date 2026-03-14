# VNC 连接决策流程图（文字版）

> 第一轮调研：VNC/Relay 连接流概览

## 一、整体流程

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 前端入口                                                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  AgentDesktopView / DeviceDesktopView          VNCViewShared (main 缩略图)       │
│  createVncTransport(VncTarget)                  subscribeToVNCStream(streamKey)  │
│          │                                              │                        │
│          └──────────────────┬────────────────────────────┘                        │
│                             ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 传输层决策                                                                   ││
│  │  shouldUseVncBridge() ? VncBridgeTransport : invoke('get_vnc_proxy_url')    ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                             │                                                    │
│  OTA: VncBridgeTransport.connect()             非 OTA: URL 直接给 RFB            │
│  → invoke('vnc_bridge_connect')                 → new RFB(container, wsUrl)      │
│  → Rust 连接 ws://127.0.0.1:{port}/vnc/...      → WebSocket(wsUrl)               │
│                             │                                                    │
│                             ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ VncProxy WebSocket 入口: ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id}   ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 二、device_id 解析（get_vnc_proxy_url / vnc_bridge_connect）

```
device_id = local_vmcontrol.device_id  ??  pcClientId
         ?? (my-devices 第一个 online 的 pc_client_id)
```

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 解析 device_id                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  local_vmcontrol 有值 ?                                                           │
│       │                                                                           │
│       ├─ YES → device_id = local_vmcontrol.device_id ?? pcClientId                │
│       │         (桌面端：本机 VmControl 已启动)                                   │
│       │                                                                           │
│       └─ NO  → 调用 Gateway GET /api/p2p/my-devices                              │
│                 ?current_app_instance_id={app_id}                                 │
│                 → 取第一个 online 的 pc_client_id                                 │
│                 (移动端：无本机 VmControl，需从 my-devices 选目标 PC)             │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 三、vnc_proxy 路由决策

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ route_vnc(ws, device_id, agent_id)                                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  local_id = local_vmcontrol.read().device_id                                      │
│                                                                                   │
│  device_id == local_id ?                                                          │
│       │                                                                           │
│       ├─ YES → serve_local_vnc                                                    │
│       │         (本机 QUIC loopback)                                              │
│       │         get_or_create_local_conn                                          │
│       │         → connect_direct(127.0.0.1:19998)                                 │
│       │         → tunnel::open_vnc_stream                                         │
│       │                                                                           │
│       └─ NO  → serve_remote_vnc                                                  │
│                 (远端 Gateway locate + Relay)                                      │
│                 get_or_create_remote_conn                                         │
│                 → P2pClient::connect(gateway_url, token, device_id)              │
│                 → relay::connect_via_relay_only                                    │
│                 → tunnel::open_vnc_stream                                         │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 四、Relay 决策点汇总

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Relay 决策点                                                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  1. 前端 OTA vs WebSocket                                                         │
│     └─ shouldUseVncBridge() = window.isSecureContext                             │
│        → OTA: VncBridgeTransport (IPC 桥接)                                       │
│        → 非 OTA: WebSocket URL 直连                                               │
│                                                                                   │
│  2. vnc_proxy 本机 vs 远程                                                        │
│     └─ device_id == local_vmcontrol.device_id ?                                  │
│        → 本机: get_or_create_local_conn → connect_direct(127.0.0.1:19998)         │
│        → 远程: get_or_create_remote_conn → P2pClient::connect                     │
│                                                                                   │
│  3. 远程连接路径（打洞已移除）                                                    │
│     └─ P2pClient::connect → relay::connect_via_relay_only                        │
│        → relay_request (POST /api/p2p/relay-request)                              │
│        → Gateway 推送 connect_relay 到 PC                                        │
│        → 手机: connect_via_relay(RelayRole::Mobile)                               │
│        → PC: CloudBridge 收到 connect_relay → connect_via_relay(RelayRole::Pc)     │
│        → novaic-quic-service Relay 配对 PC 与手机                                 │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 五、连接路径总览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 场景矩阵                                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  桌面端 + 本机 VM                                                                 │
│  local_vmcontrol 有值, device_id == local_id                                      │
│  → ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id}                              │
│  → route_vnc → serve_local_vnc → QUIC loopback 127.0.0.1:19998                   │
│  → tunnel::open_vnc_stream → VmControl Unix socket                                │
│                                                                                   │
│  桌面端 + 远端 PC 的 VM                                                           │
│  local_vmcontrol 有值, device_id != local_id                                      │
│  → ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id}                               │
│  → route_vnc → serve_remote_vnc → relay::connect_via_relay_only                  │
│  → relay_request → Gateway 推送 connect_relay → PC 与手机经 Relay 配对            │
│  → tunnel::open_vnc_stream → 远端 VmControl                                       │
│                                                                                   │
│  移动端 + 远端 PC 的 VM                                                           │
│  local_vmcontrol = None, device_id 从 my-devices 取                               │
│  → ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id} (或 VncBridgeTransport)      │
│  → route_vnc → serve_remote_vnc → relay::connect_via_relay_only                   │
│  → 同上（Relay 路径）                                                             │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 六、关键文件索引

| 模块 | 文件 |
|------|------|
| createVncTransport | `novaic-app/src/services/vncTransport.ts` |
| VncBridge | `novaic-app/src/services/vncBridge.ts` |
| vncStream | `novaic-app/src/services/vncStream.ts` |
| vnc_proxy | `novaic-app/src-tauri/src/vnc_proxy.rs` |
| get_vnc_proxy_url | `novaic-app/src-tauri/src/commands/vnc_urls.rs` |
| vnc_bridge_connect | `novaic-app/src-tauri/src/commands/vnc_bridge.rs` |
| P2pClient | `novaic-app/src-tauri/p2p/src/client.rs` |
| relay | `novaic-app/src-tauri/p2p/src/relay.rs` |
| CloudBridge | `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` |
| my-devices | `novaic-gateway/gateway/api/p2p.py` |
