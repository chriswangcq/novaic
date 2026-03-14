# NovAIC 现状梳理 — 供专家方案设计

> 目标：将 Device 管理、AppInstance、VNC（maindesk/subuser）一并优化，需专家给出统一方案。

---

## 一、系统架构概览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  前端 (React + Tauri)                                                             │
│  - Agent / Device / VNC / Scrcpy 等 UI                                            │
│  - api.ts → invoke('gateway_get/post') → Gateway                                  │
│  - vmService.getVncTransport() → vnc_proxy / vnc_bridge                          │
└─────────────────────────────────────────────────────────────────────────────────┘
           │
           │ Gateway API (HTTP/WS)
           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Gateway (Python)                                                                 │
│  - 鉴权、设备/Agent 管理、P2P my-devices                                          │
│  - 代理到 VmControl (PC Client WebSocket)                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
           │
           │ PC Client WebSocket / HTTP Proxy
           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  VmControl (Rust, 内嵌于 Tauri 或独立进程)                                         │
│  - VM/Android 生命周期、VNC/Scrcpy 代理                                            │
│  - P2P QUIC 服务端、Cloud Bridge (Relay 连接)                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
           │
           │ QUIC / P2P
           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  vnc_proxy (Tauri App 内)                                                         │
│  - ws://127.0.0.1:{port}/vnc/{device_id}/{agent_id}                              │
│  - 本地 → QUIC loopback；远端 → P2P                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
           │
           │ QUIC stream
           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  p2p/tunnel (Rust)                                                                │
│  - find_vnc_target(resource_id) → Unix socket 或 TCP port                         │
│  - maindesk: vm_id → novaic-vnc-{vm_id}.sock                                      │
│  - subuser: vm_id:username → /tmp/novaic/share-{vm_id}/vnc-{username}.port        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、Device 管理现状

### 2.1 数据模型

- **Device**：Linux VM 或 Android 设备，有 `id`、`type`、`status`、`device_serial` 等
- **AgentDeviceBinding**：Agent 与 Device 的绑定，含 `subject_type`（main / vm_user / default）、`subject_id`（main→"main"，vm_user→username）
- **数据源**：`api.devices.listForUser()`、`api.devices.list(agentId)`、`api.getAgentBinding(agentId)`

### 2.2 前端入口

| 场景 | 组件 | 数据来源 |
|------|------|----------|
| 设备管理页 | DeviceManagerPage | `api.devices.listForUser()` |
| 设备侧边栏 | DeviceSidebar | Agent 的 devices / getAgentBinding |
| 浮窗 | DeviceFloatingPanel | getAgentBinding + api.devices.get |
| 添加设备 | AddLinuxModal, AddAndroidModal | `api.devices.createLinuxForUser` 等 |

### 2.3 后端

- **Gateway**：`/api/devices`、`/api/devices/{id}`、`/api/agents/{id}/devices`、`/api/agents/{id}/binding`
- **DeviceRepository**：DB 存储
- **PC Client**：VmControl 通过 WebSocket 连接 Gateway，上报 device_id、app_instance_id

### 2.4 已知问题（DEVICE_SUBJECT_DESIGN.md）

- `agent.devices` 常为空，正确流应为 `getAgentBinding` → `api.devices.get(binding.device_id)`
- 需按 `subject_type` 选择渲染组件（main / vm_user / default）

---

## 三、AppInstance 现状

### 3.1 定义

- **app_instance_id**：本实例唯一 ID（UUID），上报 device_id 时与 Gateway 关联
- **app_type**：Desktop / Mobile
- **machine_label**：机器型号/主机名
- **is_ready**：登录后为 true

### 3.2 使用位置

- **Tauri**：`get_app_instance`、`get_local_device_id` 命令
- **Cloud Bridge**：连接 Relay 时携带 `app_instance_id`、`machine_label`
- **Gateway my-devices**：`by_app_instance` 分组、`current_device_id` 标注本机、`is_local`

### 3.3 数据流

```
登录 → update_cloud_token → app_instance.set_ready()
     → Cloud Bridge 连接 Relay
     → my-devices 返回 devices + by_app_instance（按 app_instance 分组）
```

---

## 四、VNC 现状（maindesk vs subuser）

### 4.1 调用链差异

| 维度 | Maindesk | Subuser |
|------|----------|---------|
| 组件 | VNCViewShared, DeviceVNCView, VNCView | VmUserVNCView |
| getVncTransport 参数 | `device.id` | `${deviceId}:${username}` |
| 后端 resource_id | vm_id | vm_id:username |
| 目标 | Unix socket | TCP port 文件 |

### 4.2 后端路由（p2p/tunnel.rs find_vnc_target）

- **Maindesk**：`/tmp/novaic/novaic-vnc-{vm_id}.sock`
- **Subuser**：`/tmp/novaic/share-{vm_id}/vnc-{username}.port` → 读端口 → `127.0.0.1:{port}`

### 4.3 前端差异

- Maindesk：useVNCConnection / useDeviceVNCConnection / vncStream，有 WebSocket 探测、轮询重试、自动重连
- Subuser：VmUserVNCView 内直接 connect，无重试，需手动 Retry
- RFB 参数：maindesk 有 `shared`、`credentials`；subuser 有 `wsProtocols: ['binary']`

### 4.4 痛点

- 主桌面与子用户表现不一致（连接成功率、重试策略）
- 差异分散在前端（多套组件/hook）和后端（tunnel 内 find_vnc_target）
- 期望：差异屏蔽在 vmcontrol 端，之后走通用 VNC 连接

---

## 五、相关文件索引

### 5.1 前端

| 文件 | 职责 |
|------|------|
| `novaic-app/src/services/api.ts` | Gateway API 封装、devices、getAgentBinding |
| `novaic-app/src/services/vm.ts` | getVncTransport、getVncUrl |
| `novaic-app/src/services/vncBridge.ts` | VncBridgeTransport、shouldUseVncBridge |
| `novaic-app/src/services/vncStream.ts` | 共享 VNC 流 |
| `novaic-app/src/components/VM/DeviceManagerPage.tsx` | 设备管理页 |
| `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` | 浮窗、main/vm_user 渲染 |
| `novaic-app/src/components/Layout/DeviceSidebar.tsx` | 设备侧边栏 |
| `novaic-app/src/components/VM/VmUserVNCView.tsx` | 子用户 VNC |
| `novaic-app/src/components/Visual/VNCViewShared.tsx` | 主桌面共享流 |
| `novaic-app/src/components/Visual/DeviceVNCView.tsx` | Device 主桌面 |
| `novaic-app/src/components/Visual/useVNCConnection.ts` | 主桌面连接 hook |
| `novaic-app/src/components/Visual/useDeviceVNCConnection.ts` | Device 连接 hook |

### 5.2 后端

| 文件 | 职责 |
|------|------|
| `novaic-app/src-tauri/src/commands/app_instance.rs` | get_app_instance、get_local_device_id |
| `novaic-app/src-tauri/src/state/mod.rs` | AppInstance 定义 |
| `novaic-app/src-tauri/src/vnc_proxy.rs` | VNC WebSocket 代理、route_vnc |
| `novaic-app/src-tauri/src/commands/vnc_urls.rs` | get_vnc_proxy_url |
| `novaic-app/src-tauri/src/commands/vnc_bridge.rs` | OTA 下 VNC Bridge |
| `novaic-app/src-tauri/p2p/src/tunnel.rs` | find_vnc_target、QUIC 流路由 |
| `novaic-app/src-tauri/vmcontrol/src/cloud_bridge.rs` | Relay 连接、run_tunnel_server |
| `novaic-app/src-tauri/vmcontrol/src/api/routes/vnc.rs` | VmControl VNC WebSocket（仅 maindesk） |
| `novaic-gateway/gateway/api/devices.py` | Device API |
| `novaic-gateway/gateway/api/p2p.py` | my-devices、by_app_instance |
| `novaic-gateway/gateway/api/internal/pc_client.py` | PC Client、app_instance_id |

### 5.3 设计文档

| 文件 | 内容 |
|------|------|
| `docs/MAINDESK_VS_SUBUSER_VNC_ANALYSIS.md` | VNC 主桌面 vs 子用户差异分析 |
| `DEVICE_SUBJECT_DESIGN.md` | Device 按 Subject 渲染方案 |
| `novaic-app/VNC_SCRCPY_WS_CONNECTIONS.md` | VNC/Scrcpy 连接梳理 |

---

## 六、待专家回答的问题

1. **Device 与 Binding 的统一模型**：如何简化 agent.devices、getAgentBinding、subject_type 的协作，减少前端分支？
2. **AppInstance 与 Device 的关系**：app_instance 层级、my-devices 分组、本机标注，是否可进一步简化？
3. **VNC 统一入口**：如何将 maindesk/subuser 差异收口到 vmcontrol，使 tunnel 及之后走通用 VNC 连接？
4. **前端组件收敛**：VNCViewShared、DeviceVNCView、VmUserVNCView、useVNCConnection、useDeviceVNCConnection、vncStream 能否收敛为更少的抽象？
5. **整体优化顺序**：Device → AppInstance → VNC，或反之，建议的改造顺序与依赖关系？
