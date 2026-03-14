# noVNC → VmControl 链路分析：Maindesk vs Subuser 差异

> 从浏览器 noVNC 到 QEMU/Xvnc 的端到端数据流，以及 maindesk 与 subuser 在各环节的差异。

---

## 一、整体架构（方案 B，2026-03）

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              前端 (novaic-app)                                               │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  DeviceDesktopView / VncCanvas                                                               │
│       │                                                                                      │
│       ├─ vncTarget.resourceId: maindesk = deviceId；subuser = deviceId:username               │
│       │                                                                                      │
│       └─ createVncTransport(vncTarget) → VncBridgeTransport → invoke('vnc_stream_connect')     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                        │ IPC (无 WebSocket)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  Tauri vnc_stream.rs                                                                         │
│  vnc_stream_connect(resourceId, pcClientId) → route_vnc_to_channel → bridge_channel_quic    │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                        │ QUIC stream
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  p2p::tunnel (PC 侧)                                                                         │
│  handle_incoming_stream → ensure_vnc_endpoint(resource_id) → proxy_quic_to_unix              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                        │ Unix socket
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  p2p::vnc_endpoint::ensure_vnc_endpoint                                                      │
│  maindesk: 直接返回 QEMU socket 路径                                                         │
│  subuser:  轮询 port 文件 → 建立 Unix 代理 → 返回代理 socket 路径                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │ maindesk                              │ subuser
                    ▼                                       ▼
┌──────────────────────────────────┐    ┌────────────────────────────────────────────────────┐
│  QEMU -vnc unix:/tmp/novaic/      │    │  Xvnc (VM 内) 监听 TCP 5900+N                         │
│  vnc-{vm_id}.sock                 │    │  port 文件: /tmp/novaic/share-{vm_id}/vnc-{user}.port│
│  (VM 启动时即创建)                 │    │  Unix 代理: vnc-{vm_id}-{user}.sock → 127.0.0.1:port │
└──────────────────────────────────┘    └────────────────────────────────────────────────────┘
```

---

## 二、各环节 Maindesk vs Subuser 差异表

| 环节 | 维度 | Maindesk | Subuser |
|------|------|----------|---------|
| **1. 前端 resourceId** | 格式 | `deviceId`（单段） | `deviceId:username`（两段） |
| | 来源 | DeviceDesktopView `subjectType='main'` | DeviceDesktopView `subjectType='vm_user'` |
| | 示例 | `666e2498-ef9a-4daa-85d7-ae45ef881aa5` | `666e2498-ef9a-4daa-85d7-ae45ef881aa5:test` |
| **2. 前置条件** | deviceStatus | 必须 `running` 才建连 | 无前置检查，mount 即建连 |
| | 启动控制 | 有 Start/Stop 按钮 | 无（Xvnc 由 VM 内 systemd 管理） |
| **3. vnc_stream_connect** | 输入 | `resourceId=vm_id` | `resourceId=vm_id:username` |
| | 后续路径 | 相同：route_vnc_to_channel → QUIC | 相同 |
| **4. ensure_vnc_endpoint** | 判断 | `!resource_id.contains(':')` | `resource_id.contains(':')` |
| | 发现方式 | 短轮询 3×200ms 查 socket 文件 | 轮询 port 文件 30s，间隔 500ms |
| | 目标路径 | `vnc-{vm_id}.sock` 或 `novaic-vnc-{vm_id}.sock` | `vnc-{vm_id}-{username}.sock`（代理） |
| | 超时 | 3×200ms 未找到即失败 | 30s 未找到 port 文件即失败 |
| **5. 后端 VNC 源** | 类型 | QEMU 内置 VNC（Unix socket） | Xvnc/TigerVNC（TCP 5900+N） |
| | 创建时机 | VM 启动时 QEMU 创建 | 用户登录后 Xvnc 启动，写入 port 文件 |
| | 路径/端口 | `/tmp/novaic/vnc-{vm_id}.sock` | `127.0.0.1:{port}`，port 从 port 文件读取 |
| **6. 9p 共享** | 用途 | 无 | share 目录映射到 VM `/mnt/novaic-share`，port 文件由 VM 内写入 |

---

## 三、详细链路分叉点

### 3.1 前端分叉（DeviceDesktopView）

```tsx
// maindesk
resourceId: device.id                    // 单段
subjectType: 'main' | 'default'
deviceStatus 必须 === 'running' 才 createVncTransport

// subuser
resourceId: `${deviceId}:${username}`   // 两段
subjectType: 'vm_user'
无 deviceStatus 检查，有 vncTarget 即 createVncTransport
```

**文件**：`novaic-app/src/components/Visual/DeviceDesktopView.tsx`

### 3.2 传输层（统一）

- 两者均走 `VncBridgeTransport` → `vnc_stream_connect` → `route_vnc_to_channel`
- 连接池、QUIC、tunnel 逻辑完全一致

**文件**：`vncBridge.ts`、`vnc_stream.rs`、`vnc_proxy.rs`

### 3.3 后端分叉（vnc_endpoint.rs）

| 步骤 | Maindesk | Subuser |
|------|----------|---------|
| 解析 | `resource_id` 不含 `:` | `resource_id` 含 `:`，拆为 `vm_id`、`username` |
| 发现 | 轮询 `/tmp/novaic/vnc-{id}.sock` 或 `novaic-vnc-{id}.sock` | 轮询 `/tmp/novaic/share-{vm_id}/vnc-{username}.port` |
| 返回 | 直接返回 socket 路径 | 创建 Unix 代理 `vnc-{vm_id}-{username}.sock` → `127.0.0.1:{port}` |
| 代理 | 无 | 有：`run_subuser_proxy` 监听 Unix，转发到 TCP |

**文件**：`novaic-app/src-tauri/p2p/src/vnc_endpoint.rs`

### 3.4 VM 侧 VNC 源

| 类型 | 创建者 | 路径/端口 | 创建时机 |
|------|--------|-----------|----------|
| Maindesk | QEMU `-vnc unix:...` | `/tmp/novaic/vnc-{agent_id}.sock` | VM 启动时 |
| Subuser | Xvnc（VM 内） | TCP `5900+display_num` | 用户登录后，systemd 启动 Xvnc |

**Maindesk 创建**：`vmcontrol/src/api/routes/vm.rs` 中 `start_vm`：

```rust
let vnc_socket = format!("/tmp/novaic/vnc-{}.sock", agent_id);
// QEMU args: "-vnc", format!("unix:{}", vnc_socket)
```

**Subuser 端口**：VM 内 Xvnc 启动后，将端口写入 `/mnt/novaic-share/vnc-{username}.port`，经 9p 映射到 host `/tmp/novaic/share-{vm_id}/vnc-{username}.port`。

**Subuser hostfwd**：`vm.rs` 中 `req.vm_user_display_nums` 决定 QEMU 的 `hostfwd=tcp:{5900+N}-:5900+N`，使 host 的 `127.0.0.1:5900+N` 可访问 VM 内 Xvnc。

---

## 四、时序差异（易出问题点）

| 场景 | Maindesk | Subuser |
|------|----------|---------|
| **就绪时机** | VM 启动后，QEMU 即创建 socket，通常 <1s | 用户登录 → Xvnc 启动 → port 文件写入，可能数秒 |
| **轮询超时** | 3×200ms 未找到即失败 | 30s 未找到 port 文件即失败 |
| **前端重试** | `deviceStatus=running` 后才建连，有 Start 按钮 | 无 deviceStatus，mount 即建连，失败需用户 Retry |

**Subuser 典型失败**：用户刚登录，Xvnc 尚未启动或 port 文件未写入，前端已发起连接 → `ensure_vnc_endpoint` 轮询 30s 超时。

---

## 五、文件索引

| 层级 | 文件 | 职责 |
|------|------|------|
| 前端 | `DeviceDesktopView.tsx` | vncTarget 构造、maindesk/subuser 分支、deviceStatus |
| 前端 | `vncTransport.ts` | createVncTransport、缓存、pendingByKey 去重 |
| 前端 | `vncBridge.ts` | VncBridgeTransport、vnc_stream_connect、onopen 延后 |
| Tauri | `vnc_stream.rs` | vnc_stream_connect/send、连接池、空闲驱逐 |
| Tauri | `vnc_proxy.rs` | route_vnc_to_channel、bridge_channel_quic、QUIC 连接 |
| Tauri | `p2p/tunnel.rs` | handle_incoming_stream、open_vnc_stream、proxy_quic_to_unix |
| Tauri | `p2p/vnc_endpoint.rs` | ensure_vnc_endpoint、maindesk/subuser 分支、subuser 代理 |
| VmControl | `vm.rs` | start_vm、QEMU -vnc、9p share、hostfwd |

---

## 六、数据流简图（Maindesk）

```
noVNC RFB
    │
    ▼
VncBridgeTransport.connect() → invoke('vnc_stream_connect', { resourceId: vm_id })
    │
    ▼
vnc_stream_connect → route_vnc_to_channel → get_or_create_local_conn (QUIC 127.0.0.1:19998)
    │
    ▼
p2p::tunnel::open_vnc_stream(conn, vm_id)
    │
    ▼
ensure_vnc_endpoint(vm_id) → 轮询 vnc-{vm_id}.sock → 找到
    │
    ▼
proxy_quic_to_unix(QUIC stream, /tmp/novaic/vnc-{vm_id}.sock)
    │
    ▼
QEMU VNC (RFB over Unix)
```

---

## 七、数据流简图（Subuser）

```
noVNC RFB
    │
    ▼
VncBridgeTransport.connect() → invoke('vnc_stream_connect', { resourceId: vm_id:username })
    │
    ▼
vnc_stream_connect → route_vnc_to_channel → get_or_create_local_conn (QUIC 127.0.0.1:19998)
    │
    ▼
p2p::tunnel::open_vnc_stream(conn, vm_id:username)
    │
    ▼
ensure_vnc_endpoint(vm_id:username)
    │  轮询 /tmp/novaic/share-{vm_id}/vnc-{username}.port
    │  读 port → 5901
    │  创建 Unix 代理 vnc-{vm_id}-{username}.sock
    │  代理: Unix ↔ 127.0.0.1:5901 (Xvnc)
    ▼
proxy_quic_to_unix(QUIC stream, /tmp/novaic/vnc-{vm_id}-{username}.sock)
    │
    ▼
Unix 代理 → TCP 127.0.0.1:5901 → Xvnc (RFB over TCP)
```

---

*文档基于 2026-03 代码库整理*
