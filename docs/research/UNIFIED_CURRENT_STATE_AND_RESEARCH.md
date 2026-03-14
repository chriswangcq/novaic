# NovAIC 现状与调研 — 统一文档（供专家方案设计）

> **协作文档已迁移至** [`docs/unify-vnc/`](./unify-vnc/README.md)，含现状、专家方案、任务清单。  
> 目标：将 Device 管理、AppInstance、VNC（maindesk/subuser）一并优化，需专家给出统一方案。  
> 本文档合并了现状梳理与 5 个 subagent 的调研结果。

---

## 一、系统架构概览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  前端 (React + Tauri)                                                             │
│  - Agent / Device / VNC / Scrcpy 等 UI                                            │
│  - api.ts → invoke('gateway_get/post') → Gateway                                  │
│  - vmService.getVncTransport() → vnc_proxy / vnc_bridge                          │
└─────────────────────────────────────────────────────────────────────────────────┘
           │ Gateway API (HTTP/WS)
           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Gateway (Python) — 鉴权、设备/Agent 管理、P2P my-devices、PC Client WebSocket   │
└─────────────────────────────────────────────────────────────────────────────────┘
           │ PC Client WebSocket / HTTP Proxy
           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  VmControl (Rust) — VM/Android 生命周期、VNC/Scrcpy、P2P QUIC、Cloud Bridge      │
└─────────────────────────────────────────────────────────────────────────────────┘
           │ QUIC / P2P
           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  vnc_proxy (Tauri) — ws://.../vnc/{device_id}/{agent_id}                         │
│  p2p/tunnel — find_vnc_target(resource_id) → Unix socket 或 TCP port             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、Device 管理

### 2.1 数据模型（重要）

**Device 按 User 组织，Agent 只引用**：

- **Device**：用户级资源，`listForUser()` 获取用户所有设备
- **Agent**：通过 **Binding** 引用一个 Device，不「拥有」设备列表
- **AgentDeviceBinding**：agent_id → device_id + subject_type + subject_id（引用关系）

```
User  →  has many Devices (listForUser)
Agent →  has one Binding  →  references one Device (getAgentBinding)
```

| 概念 | 表/存储 | 说明 |
|------|---------|------|
| **Logical devices** | `devices` | 用户级，Linux VM / Android 配置与生命周期 |
| **Physical PC clients** | `pc_clients` | 运行 VmControl 的物理机 |
| **AgentDeviceBinding** | `agent_device_bindings` | Agent 引用：agent_id → device_id, subject_type, subject_id |
| **subject_type** | — | main（主桌面）/ vm_user（子用户）/ default（Android） |

### 2.2 前端数据流

| 组件 | 数据来源 | 用途 |
|------|----------|------|
| AgentDrawer (Devices tab) | `api.devices.listForUser()` | 设备列表、selectedDeviceId、写入 deviceManagerDevices |
| DeviceFloatingPanel | 设计为 `getAgentBinding` + `api.devices.get` | **尚未实现**（仅 VmUserVNCView 注释提及） |
| DeviceSidebar | 设计为设备侧边栏 | **尚未实现**（App.tsx 注释提及） |
| useDeviceVNCConnection | `api.devices.start/stop/status` | VNC 生命周期 |

**正确数据流**：`getAgentBinding(agentId)` → binding → `api.devices.get(binding.device_id)` → device。  
**错误模型**：`agent.devices` 表示 Agent 拥有设备列表—实际设计是 Agent 只引用一个 Device。

**问题**：
- DeviceSidebar、DeviceFloatingPanel 尚未实现
- 仅 AgentDrawer 调用 `listForUser` 并写入 `deviceManagerDevices`
- 多处独立轮询 status（5s / 5s / 3s）
- 部分代码仍用 `agent.devices`（错误），应改为 `getAgentBinding` → `devices.get`

### 2.3 后端 API

| 端点 | 说明 |
|------|------|
| `GET /api/devices` | 用户设备列表（按 User 组织） |
| `GET /api/devices/{id}` | 设备详情 |
| `GET /api/agents/{id}/binding` | Agent 绑定（引用哪个 device + subject） |

**说明**：`GET /api/agents/{id}/devices`、`list_by_agent` 等「按 Agent 组织设备」的 API 与当前设计不符（Device 按 User 组织，Agent 只引用），无需实现。前端 `api.devices.list(agentId)` 仍存在并会请求该路径，会 404，应废弃并改用 `listForUser` + `getAgentBinding`。

**device_id 语义混淆**：
- `devices` 表：逻辑设备，主键 `id`（VM/AVD 配置）
- `pc_clients`：物理 PC，主键 `device_id`（VmControl Ed25519）
- VNC proxy 路径中的 device_id 为物理 device_id（vmcontrol_device_id）

**多 PC**：`get_pc_client_manager` 始终用第一个连接的设备，无法指定目标 PC。

---

## 三、AppInstance 与 my-devices

### 3.1 AppInstance

| 字段 | 说明 |
|------|------|
| app_instance_id | 本实例唯一 UUID，每次启动新建 |
| app_type | Desktop / Mobile |
| machine_label | 机器型号/主机名 |
| is_ready | 登录后为 true |

**数据流**：Tauri 主进程 setup → VmControl Cloud Bridge WS（x-app-instance-id, x-machine-label）→ Gateway DeviceRegistry

### 3.2 my-devices

- **来源**：`_p2p_registry`（P2P 心跳）+ `DeviceRegistry`（Cloud Bridge）
- **返回**：`{ devices: [...], by_app_instance: [...] }`，按 app_instance_id 分组
- **is_local**：需传入 `current_device_id` 查询参数，匹配时标记

**Gap**：`get_vnc_proxy_url`、`vnc_bridge_connect` 调用 my-devices 时**未传 current_device_id**，is_local 实际未生效。

---

## 四、VNC（maindesk vs subuser）

### 4.1 调用链对比

| 维度 | Maindesk | Subuser |
|------|----------|---------|
| 组件 | VNCView（agent 场景）、DeviceVNCView（device 场景） | VmUserVNCView |
| resource_id | VNCView 用 `currentAgentId`；DeviceVNCView 用 `device.id` | `${deviceId}:${username}` |
| 后端目标 | Unix socket | TCP port 文件 |
| 路径 | `/tmp/novaic/novaic-vnc-{vm_id}.sock` | `/tmp/novaic/share-{vm_id}/vnc-{username}.port` |

### 4.2 前端差异

| 项目 | Maindesk | Subuser |
|------|----------|---------|
| WebSocket 探测 | 有 | 无 |
| 轮询重试 | 有（3s） | 无 |
| 自动重连 | vncStream 有（2s，最多 3 次） | 无，仅手动 Retry |
| RFB 参数 | shared, credentials, clipViewport | wsProtocols: ['binary']，无 shared |
| 前置条件 | status === 'running' && wsReady | mount 即 connect |

### 4.3 后端路由（p2p/tunnel.rs find_vnc_target）

```rust
// resource_id 含 ':' → subuser → TCP port 文件
// 否则 → maindesk → Unix socket
```

- **Maindesk**：QEMU VNC socket，VM 启动后即存在
- **Subuser**：依赖 Xvnc 启动、port 文件写入，时序敏感

### 4.4 痛点

- 主桌面与子用户连接成功率、重试策略不一致
- 差异分散在前端（多套组件/hook）和后端（tunnel 内 find_vnc_target）
- 期望：差异收口到 vmcontrol，之后走通用 VNC 连接

---

## 五、Gaps 与建议

### 5.1 Device

1. 前端统一使用「User 设备列表 + Agent Binding 引用」模型，移除对 `agent.devices` 的依赖
2. 明确区分逻辑 device_id 与物理 device_id
3. 多 PC 场景下支持指定目标设备

### 5.2 AppInstance

1. my-devices 调用时传入 `current_device_id`，使 is_local 生效
2. 明确 app_instance_id 与 device_id 的职责边界

### 5.3 VNC

1. Subuser 增加轮询/自动重连
2. 统一 RFB 参数（shared、credentials、wsProtocols）
3. 将 find_vnc_target 逻辑移入 vmcontrol，tunnel 只做通用转发

### 5.4 前端收敛

- DeviceSidebar、DeviceFloatingPanel 是否实现及如何接入
- VNCView、DeviceVNCView、VmUserVNCView、useVNCConnection、useDeviceVNCConnection、vncStream 能否收敛为更少抽象

---

## 六、文件索引

### 6.1 前端

| 文件 | 职责 |
|------|------|
| `src/services/api.ts` | devices.*, agents.getAgentBinding |
| `src/services/vm.ts` | getVncTransport, getVncUrl |
| `src/services/vncBridge.ts` | VncBridgeTransport, shouldUseVncBridge |
| `src/services/vncStream.ts` | 共享 VNC 流（含自动重连） |
| `components/Layout/AgentDrawer.tsx` | Agents + Devices tab，设备列表（listForUser） |
| `components/Visual/VNCView.tsx` | Agent 主桌面 VNC |
| `components/Visual/DeviceVNCView.tsx` | Device 主桌面 VNC |
| `components/VM/VmUserVNCView.tsx` | 子用户 VNC |
| `components/Visual/useVNCConnection.ts` | 主桌面连接 hook |
| `components/Visual/useDeviceVNCConnection.ts` | Device 连接 hook |

### 6.2 后端

| 文件 | 职责 |
|------|------|
| `src-tauri/src/commands/app_instance.rs` | get_app_instance, get_local_device_id |
| `src-tauri/src/state/mod.rs` | AppInstance 定义 |
| `src-tauri/src/vnc_proxy.rs` | VNC WS 代理、route_vnc |
| `src-tauri/src/commands/vnc_urls.rs` | get_vnc_proxy_url |
| `src-tauri/src/commands/vnc_bridge.rs` | OTA VNC Bridge |
| `src-tauri/p2p/src/tunnel.rs` | find_vnc_target、QUIC 流路由 |
| `src-tauri/vmcontrol/src/cloud_bridge.rs` | Relay 连接、run_tunnel_server |
| `gateway/api/devices.py` | Device API |
| `gateway/api/p2p.py` | my-devices、by_app_instance |
| `gateway/api/internal/pc_client.py` | PC Client、app_instance_id |
| `gateway/db/repositories/device.py` | DeviceRepository |

---

## 七、待专家回答的问题

1. **Device 与 Binding 的统一模型**：Device 按 User 组织、Agent 通过 Binding 引用—如何简化 getAgentBinding + subject_type 在前端的协作？
2. **AppInstance 与 Device 的关系**：app_instance 层级、my-devices 分组、本机标注，是否可进一步简化？
3. **VNC 统一入口**：如何将 maindesk/subuser 差异收口到 vmcontrol？
4. **前端组件收敛**：VNC 与 Device 相关组件能否收敛为更少的抽象？
5. **整体优化顺序**：Device → AppInstance → VNC，建议的改造顺序与依赖关系？
