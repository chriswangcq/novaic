# 前端 VNC 到后端 VmControl 完整链路

> 从浏览器 noVNC 到 QEMU VNC socket 的端到端数据流

---

## 一、整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              前端 (novaic-app)                                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  AgentDesktopView / DeviceDesktopView / VNCViewShared / vncStream                        │
│       │                                                                                  │
│       ├─ createVncTransport(target) 或 vmService.getVncTransport(streamKey, pcClientId)  │
│       │       │                                                                          │
│       │       └─ invoke('get_vnc_proxy_url', { resourceId, pcClientId })                 │
│       │                                                                                  │
│       └─ RFB(container, transportOrUrl)  ← transportOrUrl = ws://127.0.0.1:{port}/vnc/...│
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ WebSocket
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          Tauri VncProxy (novaic-app/src-tauri)                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  vnc_proxy.rs                                                                             │
│  • 监听 127.0.0.1:0 (动态端口)                                                            │
│  • 路由: GET /vnc/{device_id}/{agent_id}  → route_vnc  → serve_local_vnc │ serve_remote_vnc│
│  • device_id = pc_client_id (物理 PC 标识)                                                │
│  • agent_id  = resource_id (maindesk: device_id, subuser: device_id:username)            │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                    │                                    │
                    │ 本机                              │ 远端
                    │ local_vmcontrol.device_id == device_id
                    │                                    │
                    ▼                                    ▼
┌──────────────────────────────┐    ┌──────────────────────────────────────────────────────┐
│  serve_local_vnc              │    │  serve_remote_vnc                                     │
│  • 127.0.0.1:{} QUIC loopback │    │  • p2p_client.connect(gateway, token, device_id)     │
│  • 复用 local_conn 缓存        │    │  • Gateway → Relay → PC 远端 QUIC tunnel             │
└──────────────────────────────┘    └──────────────────────────────────────────────────────┘
                    │                                    │
                    │ 共用 QUIC 连接                      │
                    ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  p2p::tunnel::open_vnc_stream(conn, agent_id)                                            │
│  • 开 QUIC stream，写入头部 [0x01][len][resource_id]                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ QUIC stream
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  PC 侧 tunnel server (p2p/tunnel.rs)                                                      │
│  • 监听 QUIC incoming streams                                                             │
│  • handle_incoming_stream: 解析 [stream_type:0x01][id_len][resource_id]                   │
│  • 调用 ensure_vnc_endpoint(resource_id) → Unix socket 路径                              │
│  • proxy_quic_to_unix: QUIC stream ↔ Unix socket 双向代理                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ Unix socket
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  p2p::vnc_endpoint::ensure_vnc_endpoint(resource_id)                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  maindesk (resource_id 不含 ':')                                                          │
│    → /tmp/novaic/novaic-vnc-{vm_id}.sock  (QEMU 内置 VNC socket)                          │
│                                                                                          │
│  subuser (resource_id = vm_id:username)                                                   │
│    → 轮询 port 文件 /tmp/novaic/share-{vm_id}/vnc-{username}.port (最多 30s)             │
│    → 建立 Unix 代理 /tmp/novaic/vnc-{vm_id}-{username}.sock → 127.0.0.1:{port}           │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ Unix socket (RFB 协议)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  QEMU / Xvnc                                                                              │
│  • maindesk: QEMU -vnc unix:/tmp/novaic/novaic-vnc-{vm_id}.sock                           │
│  • subuser: Xvnc 监听 TCP port，port 文件写入 share 目录                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、关键路径说明

### 2.1 前端入口

| 组件 | 入口 | resourceId 来源 |
|------|------|-----------------|
| 桌面直连 | AgentDesktopView | useAgentDevice → bindingToVncTarget → device_id 或 device_id:username |
| 桌面直连 | DeviceDesktopView | buildVncTarget → device.id 或 device.id:username |
| 浮层 | DeviceFloatingPanel | useAgentBinding / useDeviceVncTarget |
| 共享流 | vncStream | subscribeToVNCStream(streamKey, pcClientId) → streamKey = deviceId |

### 2.2 get_vnc_proxy_url (Tauri 命令)

```text
输入: resourceId, pcClientId?
输出: ws://127.0.0.1:{vnc_proxy_port}/vnc/{device_id}/{resource_id}
```

- **device_id** 解析：
  - 桌面：local_vmcontrol.device_id 或 pcClientId
  - 手机：Gateway GET /api/p2p/my-devices → 取第一个 online 的 pc_client_id

### 2.3 VncProxy 路由决策

```text
route_vnc(ws, device_id, agent_id):
  if local_vmcontrol.device_id == device_id:
    → serve_local_vnc   (QUIC loopback 127.0.0.1:{p2p_port})
  else:
    → serve_remote_vnc  (Gateway locate + relay + QUIC)
```

### 2.4 本地 vs 远端路径

| 场景 | 连接方式 | QUIC 目标 |
|------|----------|-----------|
| 桌面本机 | 127.0.0.1:{p2p_port} 直连 | VmControl 本机 P2P server |
| 手机远端 | Gateway relay_request → PC 推送 → relay | relay 服务器中转 |

### 2.5 VmControl 侧 Tunnel Server

- 监听 QUIC 连接上的 incoming streams
- 每个 stream 头部：`[0x01 VNC][id_len][resource_id]`
- 调用 `ensure_vnc_endpoint(resource_id)` 得到 Unix socket path
- `proxy_quic_to_unix` 双向转发

---

## 三、数据流概览（方案 B：2026-03 起）

```text
浏览器 noVNC  ←IPC→  vnc_stream_connect  →  route_vnc_to_channel  ←QUIC stream→  Tunnel Server  ←Unix socket→  QEMU/Xvnc
     RFB 协议              VncBridgeTransport              bridge_channel_quic
```

---

## 四、相关文件索引

| 层级 | 文件 | 职责 |
|------|------|------|
| 前端 | vncTransport.ts | createVncTransport，一律 VncStreamTransport |
| 前端 | vncBridge.ts | VncBridgeTransport，invoke vnc_stream_connect |
| 前端 | vncStream.ts | 共享流订阅，getVncTransport |
| 前端 | useVnc.ts | RFB 会话、重连、状态 |
| Tauri | vnc_stream.rs | vnc_stream_connect/send/close 命令 |
| Tauri | vnc_proxy.rs | route_vnc_to_channel、bridge_channel_quic；Scrcpy 仍用 WS |
| Tauri | p2p/client.rs | connect / connect_direct |
| Tauri | p2p/tunnel.rs | open_vnc_stream、run_tunnel_server、proxy_quic_to_unix |
| Tauri | p2p/vnc_endpoint.rs | ensure_vnc_endpoint |
| VmControl | vnc.rs | HTTP WebSocket 端点（直连 VmControl 时用） |
| VmControl | vm.rs | QEMU 启动时 -vnc unix:... |

---

## 五、方案 B：统一 IPC 模式（2026-03）

无论 OTA 与否，一律使用 `vnc_stream_connect`，无 WebSocket：

```text
noVNC  ←IPC→  vnc_stream_connect  →  route_vnc_to_channel  →  QUIC  ←后续同上→
```

- VncProxy 的 `/vnc` WebSocket 路由已移除，仅保留 `/scrcpy` 供 Scrcpy 使用

---

---

## 六、调试日志（VNC-FLOW）

各环节均打 `[VNC-FLOW]` 前缀日志，便于排查连接问题。控制台过滤：`VNC-FLOW`。

| 环节 | 前缀 | 文件 |
|------|------|------|
| 1-前端 | createVncTransport | vncTransport.ts |
| 2-vncStream | connectStream, getVncTransport, RFB | vncStream.ts |
| 3-useVnc | doConnect, RFB connect/disconnect | useVnc.ts |
| 4-Tauri | get_vnc_proxy_url（Scrcpy 用）, device_id 解析 | vnc_urls.rs |
| 5-VncStream | route_vnc_to_channel, bridge_channel_quic | vnc_stream.rs, vnc_proxy.rs |
| 6-Tunnel | handle_incoming_stream, ensure_vnc_endpoint | p2p/tunnel.rs |
| 7-vnc_endpoint | maindesk/subuser socket 查找 | p2p/vnc_endpoint.rs |

---

*文档基于 2026-03 代码库整理*
